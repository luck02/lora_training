#!/usr/bin/env python3
"""
Generate training data using Anthropic Batch API.
Usage: python generate_dataset.py --domain avorion
       python generate_dataset.py --domain gdscript
"""

import anthropic
import json
import time
import argparse
from pathlib import Path

# Import the JSON parsing utility
from json_parser_fix import safe_json_parse

client = anthropic.Anthropic()

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
    "difficulty": "beginner|intermediate|advanced"
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


def prepare_batch_requests(samples: list[dict], domain: str, output_path: Path):
    """Create JSONL file of batch requests."""
    template = GDSCRIPT_TEMPLATE if domain == "gdscript" else AVORION_TEMPLATE

    requests = []
    for idx, sample in enumerate(samples):
        request = {
            "custom_id": f"{domain}-{idx}",
            "params": {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 2048,
                "messages": [
                    {
                        "role": "user",
                        "content": template.replace("{code_sample}", sample["content"]),
                    }
                ],
            },
        }
        requests.append(request)

    with open(output_path, "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")

    print(f"Prepared {len(requests)} requests -> {output_path}")
    return output_path


def submit_batch(jsonl_path: Path) -> str:
    """Submit batch job and return batch ID."""
    with open(jsonl_path, "rb") as f:
        uploaded_file = client.files.create(file=f, purpose="batch")

    batch = client.batches.create(
        input_file_id=uploaded_file.id, endpoint="/v1/messages", completion_window="24h"
    )

    print(f"Submitted batch: {batch.id}")
    return batch.id


def wait_for_batch(batch_id: str, poll_interval: int = 300):
    """Poll until batch completes."""
    while True:
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


def process_results(batch, domain: str, output_path: Path) -> int:
    """Download results and save as training JSONL."""
    results_content = client.files.content(batch.output_file_id)

    examples = []
    for line in results_content.text.strip().split("\n"):
        result = json.loads(line)

        if result["result"]["type"] == "succeeded":
            response_text = result["result"]["message"]["content"][0]["text"]
            try:
                # Handle JSON in response (may be wrapped in markdown)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                parsed = json.loads(response_text)

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
            except json.JSONDecodeError:
                # Better error handling - try a more robust parsing approach
                print("JSON parsing failed for sample")
                print("Raw response (first 500 chars): {}".format(response_text[:500]))
                continue

    # Save
    with open(output_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Saved {len(examples)} examples -> {output_path}")
    return len(examples)


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
        default="batch",
        help="Use batch API or live API (default: batch)",
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

        if args.mode == "live":
            # For live mode, process each sample individually
            print("Processing in live mode (no batching)...")
            examples = []
            for idx, sample in enumerate(samples):
                # Create a single request for this sample
                template = (
                    GDSCRIPT_TEMPLATE if domain == "gdscript" else AVORION_TEMPLATE
                )
                # Create prompt from template and sample
                prompt = template.replace("{code_sample}", sample["content"])
                # Call Claude API directly for this single sample
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-5-20250929",
                        max_tokens=2048,
                        messages=[{"role": "user", "content": prompt}],
                    )

                    response_text = response.content[0].text

                    # Parse the response with better error handling
                    try:
                        # Save raw response for debugging
                        debug_output_path = Path(f"debug_raw_response_{idx}.txt")
                        with open(debug_output_path, "w") as f:
                            f.write(response_text)
                        
                        parsed = safe_json_parse(response_text)

                        if parsed is None:
                            print(
                                "Failed to parse JSON for sample {}. Raw response saved to debug_raw_response_{}.txt".format(
                                    idx, idx
                                )
                            )
                            continue

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
                    except Exception as e:
                        print("JSON parsing failed for sample {} with exception: {}".format(idx, e))
                        print(
                            "Raw response (first 500 chars): {}".format(
                                response_text[:500]
                            )
                        )
                        # Also save the raw response for debugging
                        debug_output_path = Path(f"debug_raw_response_exception_{idx}.txt")
                        with open(debug_output_path, "w") as f:
                            f.write(response_text)
                        continue
                except Exception as e:
                    print(f"Error processing sample {idx}: {e}")
                    continue

            # Save results
            with open(results_path, "w") as f:
                for ex in examples:
                    f.write(json.dumps(ex) + "\n")

            print(f"Saved {len(examples)} examples -> {results_path}")
        else:
            # Batch mode - original implementation
            prepare_batch_requests(samples, domain, requests_path)

            # Submit and wait
            batch_id = submit_batch(requests_path)
            batch = wait_for_batch(batch_id)

            # Process results
            process_results(batch, domain, results_path)
    else:
        print("Skipping generation, assuming results already exist")


if __name__ == "__main__":
    main()
