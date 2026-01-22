#!/usr/bin/env python3
"""
Centralized prompt definitions for dataset generation.
This module eliminates redundancy and provides shared prompt templates
for both fixture generation and actual dataset creation.
"""

# GDScript Prompt Templates
GDSCRIPT_PROMPT_TEMPLATE = """You are generating training data for a GDScript code assistant. Analyze this GDScript code and create a training example.

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

# Avorion Prompt Templates
AVORION_PROMPT_TEMPLATE = """You are generating training data for an Avorion modding assistant. Avorion uses Lua for modding with a custom API.

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

# Base prompt template for consistency
BASE_PROMPT_TEMPLATE = """You are generating training data for a {domain} code assistant.

Context: {context_description}

Code:
```{language}
{code_sample}
```

Generate training examples with JSON output strictly in this format:
{output_format}

Make sure the JSON is valid and can be parsed directly without any markdown formatting or extra text around it. Output ONLY the JSON array with no other text.
"""

# Utility function to get appropriate prompt template
def get_prompt_template(domain: str, file_path: str = None) -> str:
    """
    Get the appropriate prompt template for the given domain.

    Args:
        domain (str): The programming domain ('avorion' or 'gdscript')
        file_path (str, optional): File path for Avorion domain

    Returns:
        str: The appropriate prompt template
    """
    if domain == "avorion":
        return AVORION_PROMPT_TEMPLATE
    elif domain == "gdscript":
        return GDSCRIPT_PROMPT_TEMPLATE
    else:
        raise ValueError(f"Unsupported domain: {domain}")