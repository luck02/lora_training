#!/usr/bin/env python3
"""
Prepare Avorion dataset with preserved directory structure.
This script copies Avorion Lua files while maintaining their directory hierarchy
and prepares them for dataset generation.
"""

import os
import shutil
import argparse
from pathlib import Path

def prepare_avorion_dataset(source_dir, target_dir):
    """
    Copy Avorion Lua files while preserving directory structure.

    Args:
        source_dir (str): Path to Avorion data directory
        target_dir (str): Path to target raw data directory
    """
    source_path = Path(source_dir)
    target_path = Path(target_dir)

    # Ensure target directory exists
    target_path.mkdir(parents=True, exist_ok=True)

    # Find all Lua files
    lua_files = list(source_path.rglob("*.lua"))

    print(f"Found {len(lua_files)} Lua files in {source_dir}")

    copied_files = 0
    for lua_file in lua_files:
        # Calculate relative path from source directory
        rel_path = lua_file.relative_to(source_path)

        # Create target path preserving directory structure
        target_file = target_path / rel_path

        # Create subdirectories if needed
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        try:
            shutil.copy2(lua_file, target_file)
            copied_files += 1
            if copied_files % 100 == 0:
                print(f"Copied {copied_files} files...")
        except Exception as e:
            print(f"Error copying {lua_file}: {e}")

    print(f"Successfully copied {copied_files} Lua files to {target_dir}")

def main():
    parser = argparse.ArgumentParser(description='Prepare Avorion dataset with directory structure')
    parser.add_argument('--source', default='/Users/garyclucas/Library/Application Support/Steam/steamapps/common/Avorion/data',
                       help='Source Avorion data directory (default: Steam installation)')
    parser.add_argument('--target', default='/Users/garyclucas/dev/lora-training/data/avorion/raw',
                       help='Target raw data directory (default: project raw directory)')

    args = parser.parse_args()

    print(f"Preparing Avorion dataset...")
    print(f"Source: {args.source}")
    print(f"Target: {args.target}")

    if not os.path.exists(args.source):
        print(f"Error: Source directory {args.source} does not exist")
        return

    prepare_avorion_dataset(args.source, args.target)
    print("Dataset preparation complete!")

if __name__ == "__main__":
    main()