#!/usr/bin/env python3
"""
Extract functions from raw code files as supplementary training data.
Usage: python prepare_data.py --domain avorion
"""

import argparse
import json
import re
from pathlib import Path


def extract_lua_functions(content: str) -> list[dict]:
    """Extract Lua functions from Avorion code."""
    pairs = []
    pattern = r"function\s+(\w+(?:\.\w+)?)\s*\(([^)]*)\)(.*?)end"

    for match in re.finditer(pattern, content, re.DOTALL):
        name, params, body = match.groups()
        full_func = f"function {name}({params}){body}end"

        if len(full_func) > 50:  # Skip trivial functions
            pairs.append(
                {
                    "instruction": f"Write an Avorion Lua function called {name}",
                    "output": full_func.strip(),
                }
            )

    return pairs


def extract_gdscript_functions(content: str) -> list[dict]:
    """Extract GDScript functions."""
    pairs = []
    pattern = r"func\s+(\w+)\s*\(([^)]*)\)[^:]*:(.*?)(?=\nfunc\s|\nclass\s|\Z)"

    for match in re.finditer(pattern, content, re.DOTALL):
        name, params, body = match.groups()
        full_func = f"func {name}({params}):{body}"

        if len(full_func) > 50:
            pairs.append(
                {
                    "instruction": f"Write a GDScript function called {name}",
                    "output": full_func.strip(),
                }
            )

    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True, choices=["avorion", "gdscript"])
    args = parser.parse_args()

    domain = args.domain
    raw_dir = Path(f"data/{domain}/raw")
    output_path = Path(f"data/{domain}/extracted.jsonl")

    extension = ".lua" if domain == "avorion" else ".gd"
    extractor = (
        extract_lua_functions if domain == "avorion" else extract_gdscript_functions
    )

    all_pairs = []
    for file_path in raw_dir.rglob(f"*{extension}"):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            pairs = extractor(content)
            all_pairs.extend(pairs)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    # Save
    with open(output_path, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair) + "\n")

    print(f"Extracted {len(all_pairs)} function pairs -> {output_path}")
    print(f"Merge with: cat {output_path} >> data/{domain}/train.jsonl")


if __name__ == "__main__":
    main()
