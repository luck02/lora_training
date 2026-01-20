#!/usr/bin/env python3
"""
Debug script to examine the exact response from API
"""

import anthropic
import json
import re
from pathlib import Path

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
        print("=== RAW RESPONSE ANALYSIS ===")
        print(f"Length: {len(response_text)}")
        print(f"First 200 chars: {repr(response_text[:200])}")
        print(f"Last 200 chars: {repr(response_text[-200:])}")

        # Check the structure manually
        print("\n=== CHECKING STRUCTURE ===")
        print(f"Has ```json: {'```json' in response_text}")
        start_pos = response_text.find("```json")
        end_pos = response_text.find("```", start_pos + 1)
        print(f"Start pos of ```json: {start_pos}")
        print(f"End pos of ```json: {end_pos}")

        if start_pos != -1 and end_pos != -1:
            print(
                f"Content between markers: {repr(response_text[start_pos + 6 : end_pos][:200])}"
            )

        # Test manual parsing of a segment
        if start_pos != -1 and end_pos != -1:
            json_segment = response_text[start_pos + 6 : end_pos].strip()
            print(f"\nManual segment extraction: {repr(json_segment[:200])}")
            try:
                parsed = json.loads(json_segment)
                print(f"Manual parsing successful: {type(parsed)}")
                print(
                    f"First item: {parsed[0] if isinstance(parsed, list) and len(parsed) > 0 else 'No items'}"
                )
            except Exception as e:
                print(f"Manual parsing failed: {e}")
                # Try to see what's causing issues
                print("Looking for problematic characters...")
                for i, char in enumerate(json_segment[:500]):
                    if ord(char) > 127:
                        print(f"Non-ASCII char at pos {i}: {repr(char)}")

    except Exception as e:
        print(f"Error calling API: {e}")


if __name__ == "__main__":
    test_api_call()
