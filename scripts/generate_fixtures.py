#!/usr/bin/env python3
"""
Generate improved test fixtures with reduced redundancy.
This script creates high-quality, non-redundant fixture files for testing.
"""

import os
import json
import random
from pathlib import Path
from prompts import get_prompt_template

def generate_avorion_fixture_samples():
    """Generate diverse Avorion Lua fixture samples by reading from raw data directory."""

    # Get all Lua files from the raw directory
    raw_dir = Path("data/avorion/raw")
    lua_files = list(raw_dir.rglob("*.lua"))

    fixture_templates = []

    # If raw directory is empty or has no files, leave a message
    if not lua_files:
        print("Warning: No raw Avorion files found in data/avorion/raw/")
        print("Please populate the raw directory with Avorion Lua files to generate fixtures.")
        return []

    # Read content from actual raw files
    for i, file_path in enumerate(lua_files[:5]):  # Limit to first 5 files for brevity
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Extract a meaningful name from the file path
            relative_path = file_path.relative_to(raw_dir)
            name_parts = [str(part) for part in relative_path.parts if part != '.']
            if name_parts:
                name = '_'.join(name_parts).replace('.lua', '')
            else:
                name = f"raw_lua_{i}"

            fixture_templates.append({
                "name": name,
                "description": f"Raw Avorion Lua code from {relative_path}",
                "content": content
            })
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            continue

    return fixture_templates

def generate_gdscript_fixture_samples():
    """Generate diverse GDScript fixture samples by reading from raw data directory."""

    # Get all GDScript files from the raw directory
    raw_dir = Path("data/gdscript/raw")
    gd_files = list(raw_dir.rglob("*.gd"))

    fixture_templates = []

    # If raw directory is empty or has no files, leave a message
    if not gd_files:
        print("Warning: No raw GDScript files found in data/gdscript/raw/")
        print("Please populate the raw directory with GDScript files to generate fixtures.")
        return []

    # Read content from actual raw files
    for i, file_path in enumerate(gd_files[:5]):  # Limit to first 5 files for brevity
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Extract a meaningful name from the file path
            relative_path = file_path.relative_to(raw_dir)
            name_parts = [str(part) for part in relative_path.parts if part != '.']
            if name_parts:
                name = '_'.join(name_parts).replace('.gd', '')
            else:
                name = f"raw_gd_{i}"

            fixture_templates.append({
                "name": name,
                "description": f"Raw GDScript code from {relative_path}",
                "content": content
            })
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            continue

    return fixture_templates

def create_fixtures(domain, target_dir):
    """Create fixture files for the specified domain."""

    if domain == "avorion":
        fixture_samples = generate_avorion_fixture_samples()
    elif domain == "gdscript":
        fixture_samples = generate_gdscript_fixture_samples()
    else:
        raise ValueError(f"Unsupported domain: {domain}")

    # Ensure target directory exists
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(fixture_samples)} fixture samples for {domain}...")

    for i, sample in enumerate(fixture_samples):
        # Create file with descriptive name
        filename = f"{sample['name']}.{'lua' if domain == 'avorion' else 'gd'}"
        filepath = target_path / filename

        # Write content
        with open(filepath, 'w') as f:
            f.write(sample['content'])

        print(f"Created: {filepath}")

    print(f"Successfully created {len(fixture_samples)} fixture files in {target_dir}")

def main():
    """Main function to generate fixtures."""
    print("Generating improved test fixtures...")

    # Create Avorion fixtures
    create_fixtures("avorion", "tests/fixtures/avorion")

    # Create GDScript fixtures
    create_fixtures("gdscript", "tests/fixtures/gdscript")

    print("Fixture generation complete!")

if __name__ == "__main__":
    main()