#!/usr/bin/env python3
"""
Test script to verify the capture script works correctly
"""

import json
import os
from pathlib import Path

def test_capture_script_structure():
    """Verify that the capture script creates the expected files"""

    # Check that the capture script exists
    capture_script = Path("scripts/capture_anthropic_responses.py")
    assert capture_script.exists(), "Capture script should exist"

    # Check that the fixtures directory exists
    fixtures_dir = Path("tests/fixtures/anthropic_responses")
    assert fixtures_dir.exists(), "Fixtures directory should exist"

    # Check that some response files were created
    response_files = list(fixtures_dir.glob("*.json"))
    assert len(response_files) > 0, "At least one response file should be created"

    # Check the content of one of the files
    for response_file in response_files:
        with open(response_file, 'r') as f:
            data = json.load(f)

        # Verify expected structure
        assert "success" in data or "error" in data, f"Response file {response_file} should have success/error field"
        assert "timestamp" in data, f"Response file {response_file} should have timestamp"

        print(f"✓ Verified {response_file.name}")

if __name__ == "__main__":
    test_capture_script_structure()
    print("All tests passed!")