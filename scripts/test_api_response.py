#!/usr/bin/env python3
"""
Debug script to test API response format for avorion domain
"""

import anthropic
import json
from pathlib import Path

# Import the JSON parsing utility
from json_parser_fix import safe_json_parse

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

    print("\n=== PROMPT SENT TO API ===")
    print(prompt[:500])
    print("...")

    # Call Claude API directly
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        print("\n=== RAW RESPONSE FROM API ===")
        print(response_text[:1000])
        print("...")

        print("\n=== TRYING TO PARSE ===")
        parsed = safe_json_parse(response_text)
        print("Parsed result:", parsed)

        if parsed is None:
            print("JSON parsing failed!")

    except Exception as e:
        print(f"Error calling API: {e}")


if __name__ == "__main__":
    test_api_call()
