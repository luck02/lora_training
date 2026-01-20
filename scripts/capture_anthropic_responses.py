#!/usr/bin/env python3
"""
Script to capture real Anthropic API responses for testing purposes.
This script makes actual API calls with the EXACT same prompts used in the real pipeline
so that we get responses that match what will be used in production.
"""

import os
import json
import anthropic
from pathlib import Path
from typing import Dict, Any, List
import time
import random
import subprocess

# Load environment variables from .envrc if it exists
def load_env_vars():
    """Load environment variables from .envrc file"""
    try:
        # Source the .envrc file and get the environment
        result = subprocess.run(['bash', '-c', 'source .envrc && env'],
                               capture_output=True, text=True, check=True)

        # Parse the environment variables
        for line in result.stdout.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    except Exception as e:
        print(f"Warning: Could not load .envrc: {e}")
        # Fall back to loading .env file if it exists
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

load_env_vars()

# Exact templates from generate_dataset.py - these are the prompts that will be used in the real pipeline
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

ERROR_PROMPT = """You are simulating an error response from the Claude API.

Generate a JSON response that represents an error scenario:
{
  "error": "API_ERROR",
  "message": "An error occurred while processing your request",
  "retry_after": 30
}
"""

def create_anthropic_client():
    """Create and return an Anthropic client instance"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    return anthropic.Anthropic(api_key=api_key)

def make_api_call(client, prompt: str, model: str = "claude-sonnet-4-5-20250929") -> Dict[str, Any]:
    """Make a single API call and return the response"""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text content
        response_text = response.content[0].text

        # Add delay to respect rate limits
        time.sleep(random.uniform(0.5, 1.5))

        return {
            "success": True,
            "response_text": response_text,
            "model": model,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"API call failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "model": model,
            "timestamp": time.time()
        }

def get_sample_code_from_fixtures(domain: str) -> str:
    """Get sample code from existing fixture files to use in prompts"""
    fixture_dir = Path(f"tests/fixtures/{domain}")

    if not fixture_dir.exists():
        # Return placeholder if no fixtures exist
        if domain == "avorion":
            return """function spawnShip(entityId)
    local entity = Entity(entityId)
    if entity then
        entity:setProperty("health", 100)
        return entity
    end
    return nil
end"""
        else:  # gdscript
            return """extends Node

func _ready() -> void:
    var timer = Timer.new()
    timer.wait_time = 1.0
    timer.connect("timeout", self, "_on_timeout")
    add_child(timer)
    timer.start()

func _on_timeout() -> void:
    print("Timer timed out!")"""

    # Find a sample file
    sample_files = list(fixture_dir.glob("*"))
    if sample_files:
        sample_file = sample_files[0]
        try:
            return sample_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    # Return placeholder if we can't read any files
    if domain == "avorion":
        return """function spawnShip(entityId)
    local entity = Entity(entityId)
    if entity then
        entity:setProperty("health", 100)
        return entity
    end
    return nil
end"""
    else:  # gdscript
        return """extends Node

func _ready() -> void:
    var timer = Timer.new()
    timer.wait_time = 1.0
    timer.connect("timeout", self, "_on_timeout")
    add_child(timer)
    timer.start()

func _on_timeout() -> void:
    print("Timer timed out!")"""


def capture_responses():
    """Capture responses for different scenarios using the exact same prompts as the real pipeline"""
    client = create_anthropic_client()

    # Create output directory
    output_dir = Path("tests/fixtures/anthropic_responses")
    output_dir.mkdir(exist_ok=True)

    # Capture different response types
    responses = {}

    # Get sample code from fixtures
    avorion_sample = get_sample_code_from_fixtures("avorion")
    gdscript_sample = get_sample_code_from_fixtures("gdscript")

    # Create prompts with exact same format as used in real pipeline
    avorion_prompt = AVORION_TEMPLATE.replace("{code_sample}", avorion_sample)
    gdscript_prompt = GDSCRIPT_TEMPLATE.replace("{code_sample}", gdscript_sample)

    print("Capturing Avorion response...")
    avorion_result = make_api_call(client, avorion_prompt)
    responses["avorion_batch_responses"] = avorion_result

    print("Capturing GDScript response...")
    gdscript_result = make_api_call(client, gdscript_prompt)
    responses["gdscript_batch_responses"] = gdscript_result

    print("Capturing error response...")
    error_result = make_api_call(client, ERROR_PROMPT)
    responses["error_responses"] = error_result

    # Save responses to JSON files
    for filename, response_data in responses.items():
        output_file = output_dir / f"{filename}.json"
        with open(output_file, 'w') as f:
            json.dump(response_data, f, indent=2)

        print(f"Saved {filename}.json")

    print("All responses captured!")

if __name__ == "__main__":
    capture_responses()