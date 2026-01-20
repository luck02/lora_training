#!/usr/bin/env python3
"""
Debug script to test API response format for avorion domain - detailed version
"""

import anthropic
import json
import re
from pathlib import Path


def debug_json_parse(response_text):
    """
    Debug version of JSON parsing to see exactly what's happening
    """
    print("=== DEBUG JSON PARSING ===")
    print(f"Full response length: {len(response_text)}")
    print(f"Contains ```json: {'```json' in response_text}")

    # Try to extract JSON from markdown code blocks
    if "```json" in response_text:
        start_marker = "```json"
        end_marker = "```"

        start_pos = response_text.find(start_marker)
        print(f"Start marker position: {start_pos}")
        if start_pos != -1:
            start_pos += len(start_marker)
            end_pos = response_text.find(end_marker, start_pos)
            print(f"End marker position: {end_pos}")
            if end_pos != -1:
                extracted = response_text[start_pos:end_pos]
                print(f"Extracted content (first 500 chars): {repr(extracted[:500])}")
                extracted = extracted.strip()
                print(f"After strip (first 500 chars): {repr(extracted[:500])}")

                try:
                    result = json.loads(extracted)
                    print(f"Successfully parsed: {type(result)}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print("Trying to find first JSON array...")
                    # Try to find JSON array
                    try:
                        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
                        if json_match:
                            array_content = json_match.group(0)
                            print(f"Found array content: {repr(array_content[:200])}")
                            return json.loads(array_content)
                    except Exception as e2:
                        print(f"Array parsing error: {e2}")

    # Try direct parsing
    try:
        result = json.loads(response_text)
        print("Direct parsing successful")
        return result
    except json.JSONDecodeError as e:
        print(f"Direct parsing failed: {e}")

    # Try to find any JSON in the text
    try:
        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if json_match:
            array_content = json_match.group(0)
            print(f"Found array via regex: {repr(array_content[:200])}")
            return json.loads(array_content)
    except Exception as e:
        print(f"Regex array parsing failed: {e}")

    return None


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

Generate training examples with JSON output:
{
  "prompt": "...",
  "response": "{the original code}",
  "context": "server|client|shared",
  "avorion_apis": ["Entity", "Sector", etc.],
  "difficulty": "beginner|intermediate|advanced"
}

Important: Avorion modders often ask about:
- How to get/modify entity properties
- Registering callbacks for game events
- Creating custom commands
- Spawning/modifying ships and stations
- Working with the block/component system
"""


def test_api_call():
    client = anthropic.Anthropic()

    # Use one of the sample files
    sample_file = Path("data/avorion/raw/ancientgates.lua")
    code_content = sample_file.read_text(encoding="utf-8", errors="ignore")

    print("=== SAMPLE CODE ===")
    print(code_content[:500])
    print("...")

    # Create prompt from template and sample
    prompt = AVORION_TEMPLATE.replace("{code_sample}", code_content)

    # Call Claude API directly
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        print("\n=== RAW RESPONSE FROM API ===")
        print(repr(response_text[:500]))
        print("...")

        parsed = debug_json_parse(response_text)
        print("\n=== FINAL RESULT ===")
        print("Parsed result:", parsed)

    except Exception as e:
        print(f"Error calling API: {e}")


if __name__ == "__main__":
    test_api_call()
