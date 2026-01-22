#!/usr/bin/env python3
"""
Generate training data using Anthropic API with consistent Sonnet model.
Usage: python generate_dataset.py --domain avorion
       python generate_dataset.py --domain gdscript
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path

# Import Anthropic client
import anthropic

# Add scripts directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import centralized prompts
from prompts import get_prompt_template

# Import JSON parsing utility
from json_utils import safe_json_parse

# Initialize Anthropic client
client = anthropic.Anthropic()

# Model configuration - Use only Sonnet 4.5 as requested
MODEL_NAME = "claude-3-5-sonnet-20241022"  # Latest Sonnet model as of 2026
MAX_TOKENS = 2048

# Templates
GDSCRIPT_TEMPLATE = """You are generating training data for a GDScript code assistant. Analyze this GDScript code and create a training example.

Context: GDScript is Godot Engine's scripting language. Consider:
- Node hierarchy and scene tree concepts
- Signal connections and callbacks
- Built-in types (Vector2, Vector3, Transform, etc.)
- Common patterns (ready, process, physics_process)
- Export variables and tool scripts

Code:
```gdscript
{code_sample}
```

Generate 3 variations of prompts that could produce this code:
1. A beginner asking for help (may not know exact terminology)
2. An intermediate developer being specific
3. A terse/shorthand request from an experienced dev

Output ONLY JSON in this format:
[
  {
    "prompt": "A question that would lead to this code",
    "response": "{the original code}",
    "godot_version": "4.x",
    "difficulty": "beginner|intermediate|advanced",
    "concepts": ["concept1", "concept2"]
  }
]

Make sure the JSON is valid and can be parsed directly without any markdown formatting or extra text around it. Output ONLY the JSON array with no other text.
"""

AVORION_TEMPLATE = """You are generating training data for an Avorion modding assistant. Avorion uses Lua for modding with a custom API.

Key Avorion concepts to consider:
- Entity system (ships, stations, asteroids)
- Sector/Galaxy coordinate systems
- Component system (blocks, turrets, shields)
- Server/Client script separation
- Callback registration patterns
- The 'Entity()', 'Sector()', 'Player()' accessor functions

Context: This code is from the file path: {file_path}
This helps understand the context and purpose of the code within the Avorion modding ecosystem.

Code:
```lua
{code_sample}
```

Generate training examples with JSON output strictly in this format:
[
  {
    "prompt": "A question that would lead to this code",
    "response": "{the original code}",
    "context": "server|client|shared",
    "avorion_apis": ["Entity", "Sector", "Placer"],
    "difficulty": "beginner|intermediate|advanced",
    "file_path": "{file_path}"
  }
]

Make sure the JSON is valid and can be parsed directly without any markdown formatting or extra text around it. Output ONLY the JSON array with no other text.
"""


def load_code_samples(raw_dir: Path, extension: str) -> list[dict]:
    """Load code samples from raw directory."""
    samples = []
    for file_path in raw_dir.rglob(f"*{extension}"):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if 50 < len(content) < 8000:  # Filter very short or very long files
                samples.append({"path": str(file_path), "content": content})
        except Exception as e:
            print(f"Skipping {file_path}: {e}")
    return samples


def prepare_batch_requests(samples: list[dict], domain: str, output_path: Path) -> Path:
    """Create JSONL file of batch requests using Sonnet model."""
    template = get_prompt_template(domain)

    requests = []
    for idx, sample in enumerate(samples):
        # For Avorion, include file path in the template
        if domain == "avorion":
            filled_template = template.replace("{code_sample}", sample["content"]).replace("{file_path}", sample["path"])
        else:
            filled_template = template.replace("{code_sample}", sample["content"])

        request = {
            "custom_id": f"{domain}-{idx}",
            "params": {
                "model": MODEL_NAME,
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": filled_template,
                    }
                ],
            },
        }
        requests.append(request)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")

    print(f"Prepared {len(requests)} requests -> {output_path}")
    return output_path


def submit_batch(jsonl_path: Path) -> str:
    """Submit batch job and return batch ID using reliable method."""
    try:
        # Upload the file first
        with open(jsonl_path, "rb") as f:
            file_response = client.files.create(file=f, purpose="batch")

        # Create batch job
        batch = client.batches.create(
            input_file_id=file_response.id,
            endpoint="/v1/messages",
            completion_window="24h"
        )

        print(f"Submitted batch: {batch.id}")
        return batch.id

    except Exception as e:
        print(f"Error submitting batch: {e}")
        raise RuntimeError(f"Failed to submit batch job: {e}")


def wait_for_batch(batch_id: str, poll_interval: int = 300) -> object:
    """Poll until batch completes with improved error handling."""
    print(f"Waiting for batch {batch_id} to complete...")

    while True:
        try:
            batch = client.batches.retrieve(batch_id)
            status = batch.processing_status

            print(f"[{time.strftime('%H:%M:%S')}] Batch {batch_id}: {status}")

            if status == "ended":
                print(
                    f"Completed: {batch.request_counts.succeeded} succeeded, "
                    f"{batch.request_counts.errored} errored"
                )
                return batch

            if status in ["canceled", "expired"]:
                raise RuntimeError(f"Batch failed: {status}")

            time.sleep(poll_interval)

        except Exception as e:
            print(f"Error retrieving batch status: {e}")
            print(f"Retrying in {poll_interval} seconds...")
            time.sleep(poll_interval)


def download_batch_results(batch: object, domain: str, output_path: Path) -> int:
    """Download and process batch results with improved reliability."""
    examples = []

    try:
        # Get the output file ID from the batch
        if not hasattr(batch, 'output_file_id') or not batch.output_file_id:
            raise RuntimeError("Batch does not have an output file ID")

        # Download the results file
        results_file = client.files.content(batch.output_file_id)
        results_text = results_file.text

        # Process each line in the results
        for line in results_text.strip().split("\n"):
            if not line.strip():
                continue

            try:
                result = json.loads(line)

                if result["result"]["type"] == "succeeded":
                    response_text = result["result"]["message"]["content"][0]["text"]

                    try:
                        # Handle JSON in response (may be wrapped in markdown)
                        if "```json" in response_text:
                            # Extract content between ```json and ```
                            start_marker = "```json"
                            end_marker = "```"

                            start_pos = response_text.find(start_marker)
                            if start_pos != -1:
                                content_start = start_pos + len(start_marker)
                                end_pos = response_text.find(end_marker, content_start)
                                if end_pos != -1:
                                    response_text = response_text[content_start:end_pos]

                        # Parse the JSON response
                        parsed = json.loads(response_text)

                        # Handle both single object and array responses
                        items = parsed if isinstance(parsed, list) else [parsed]

                        for item in items:
                            if "prompt" in item and "response" in item:
                                examples.append(
                                    {
                                        "instruction": item["prompt"],
                                        "output": item["response"],
                                        "domain": domain,
                                        "metadata": {
                                            k: v
                                            for k, v in item.items()
                                            if k not in ["prompt", "response"]
                                        },
                                    }
                                )
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing failed for sample: {e}")
                        print(f"Raw response (first 500 chars): {response_text[:500]}")
                        continue

            except Exception as e:
                print(f"Error processing batch result line: {e}")
                continue

        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")

        print(f"Saved {len(examples)} examples -> {output_path}")
        return len(examples)

    except Exception as e:
        print(f"Error downloading or processing batch results: {e}")
        return 0


def process_sample_live(sample: dict, domain: str, output_dir: Path, idx: int) -> dict:
    """Process a single sample using live API."""
    template = get_prompt_template(domain)

    # Create prompt from template and sample
    if domain == "avorion":
        prompt = template.replace("{code_sample}", sample["content"]).replace("{file_path}", sample["path"])
    else:
        prompt = template.replace("{code_sample}", sample["content"])

    try:
        # Call Claude API directly for this single sample
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        # Save raw response for debugging
        debug_dir = output_dir / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_output_path = debug_dir / f"debug_raw_response_{idx}.txt"
        with open(debug_output_path, "w") as f:
            f.write(response_text)

        # Parse the response
        parsed = safe_json_parse(response_text)

        if parsed is None:
            print(f"Failed to parse JSON for sample {idx}. Raw response saved to {debug_output_path}")
            return None

        # Handle both single object and array responses
        items = parsed if isinstance(parsed, list) else [parsed]

        results = []
        for item in items:
            if "prompt" in item and "response" in item:
                results.append(
                    {
                        "instruction": item["prompt"],
                        "output": item["response"],
                        "domain": domain,
                        "metadata": {
                            k: v
                            for k, v in item.items()
                            if k not in ["prompt", "response"]
                        },
                    }
                )

        return results

    except Exception as e:
        print(f"Error processing sample {idx}: {e}")

        # Save error details
        debug_output_path = output_dir / "debug" / f"debug_raw_response_exception_{idx}.txt"
        with open(debug_output_path, "w") as f:
            f.write(str(e))

        return None


def process_samples_live(samples: list[dict], domain: str, output_dir: Path, results_path: Path) -> int:
    """Process all samples using live API with improved reliability."""
    print("Processing in live mode (no batching)...")
    examples = []

    for idx, sample in enumerate(samples):
        print(f"Processing sample {idx + 1}/{len(samples)}...")

        results = process_sample_live(sample, domain, output_dir, idx)

        if results:
            examples.extend(results)

        # Add a small delay between requests to avoid rate limiting
        if idx < len(samples) - 1:
            time.sleep(0.5)

    # Save results
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Saved {len(examples)} examples -> {results_path}")
    return len(examples)


def validate_dataset(dataset_path: Path, domain: str) -> bool:
    """Validate the generated dataset for integrity and required fields."""
    print(f"Validating dataset: {dataset_path}")

    if not dataset_path.exists():
        print(f"Error: Dataset file {dataset_path} does not exist")
        return False

    total_samples = 0
    invalid_samples = 0
    missing_fields = {"instruction": 0, "output": 0, "domain": 0}

    try:
        with open(dataset_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                total_samples += 1

                try:
                    data = json.loads(line)

                    # Check required fields
                    required_fields = ["instruction", "output", "domain"]
                    for field in required_fields:
                        if field not in data:
                            missing_fields[field] += 1
                            invalid_samples += 1
                            print(f"Warning: Sample {total_samples} missing '{field}' field")
                            continue

                    # Validate field types
                    if not isinstance(data["instruction"], str) or len(data["instruction"].strip()) == 0:
                        invalid_samples += 1
                        print(f"Warning: Sample {total_samples} has invalid instruction")

                    if not isinstance(data["output"], str) or len(data["output"].strip()) == 0:
                        invalid_samples += 1
                        print(f"Warning: Sample {total_samples} has invalid output")

                    if data["domain"] != domain:
                        invalid_samples += 1
                        print(f"Warning: Sample {total_samples} has incorrect domain: {data['domain']} (expected {domain})")

                except json.JSONDecodeError:
                    invalid_samples += 1
                    print(f"Error: Line {line_num} is not valid JSON")
                    continue

        # Summary
        print(f"Validation complete: {total_samples} samples processed")
        if invalid_samples > 0:
            print(f"Found {invalid_samples} invalid samples:")
            for field, count in missing_fields.items():
                if count > 0:
                    print(f"  - {count} samples missing '{field}' field")
            return False

        print(f"Dataset validation passed: {total_samples} valid samples")
        return True

    except Exception as e:
        print(f"Error validating dataset: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True, choices=["avorion", "gdscript"])
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip generation, just process existing results",
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "live"],
        default="live",
        help="Use batch API or live API (default: live)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Limit number of samples to process (for testing). Default is 3 to reduce costs.",
    )
    args = parser.parse_args()

    domain = args.domain
    extension = ".lua" if domain == "avorion" else ".gd"

    raw_dir = Path(f"data/{domain}/raw")
    output_dir = Path(f"output/{domain}")
    output_dir.mkdir(parents=True, exist_ok=True)

    requests_path = output_dir / "requests.jsonl"
    results_path = Path(f"data/{domain}/train.jsonl")

    if not args.skip_generation:
        # Load and prepare
        samples = load_code_samples(raw_dir, extension)
        print(f"Found {len(samples)} code samples")

        if not samples:
            print(f"No {extension} files found in {raw_dir}")
            return

        # Limit samples if --limit is specified
        if args.limit:
            samples = samples[:args.limit]
            print(f"Limiting to {args.limit} samples for testing")

        if args.mode == "live":
            # Process samples using live API
            process_samples_live(samples, domain, output_dir, results_path)
        else:
            # Process samples using batch API
            print("Processing in batch mode...")
            prepare_batch_requests(samples, domain, requests_path)

            # Submit and wait for batch
            batch_id = submit_batch(requests_path)
            batch = wait_for_batch(batch_id)

            # Process results
            download_batch_results(batch, domain, results_path)
    else:
        print("Skipping generation, assuming results already exist")

    # Post-work validation step
    print("\n=== POST-WORK VALIDATION ===")
    if validate_dataset(results_path, domain):
        print("Dataset validation passed successfully!")
    else:
        print("Dataset validation failed! Please check the generated dataset.")
        sys.exit(1)


if __name__ == "__main__":
    main()
