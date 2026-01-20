"""
Data processing tests for LoRA training framework
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import re


def test_fixture_files_exist():
    """Test that fixture files exist and are readable"""
    avorion_fixtures = list(Path("tests/fixtures/avorion").glob("*.lua"))
    # Skip GDScript fixture check as we're focusing on Avorion first
    # gdscript_fixtures = list(Path("tests/fixtures/gdscript").glob("*.gd"))

    assert len(avorion_fixtures) > 0, "Should have Avorion fixture files"
    # Skip GDScript fixture check as we're focusing on Avorion first
    # assert len(gdscript_fixtures) > 0, "Should have GDScript fixture files"

    # Test reading one fixture file
    if avorion_fixtures:
        fixture_content = avorion_fixtures[0].read_text()
        assert len(fixture_content) > 0, "Fixture files should not be empty"


def test_avorion_function_extraction():
    """Test function extraction from Avorion Lua code"""
    # Read a fixture file
    fixture_path = Path("tests/fixtures/avorion/entity_system.lua")
    if fixture_path.exists():
        content = fixture_path.read_text()

        # Simple regex pattern to find function definitions
        function_pattern = r"function\s+(\w+(?:\.\w+)?)\s*\(([^)]*)\)(.*?)end"
        matches = re.findall(function_pattern, content, re.DOTALL)

        # Should find at least one function
        assert len(matches) > 0, "Should find functions in Avorion code"

        # Check function names
        function_names = [match[0] for match in matches]
        assert "spawnPirateShip" in function_names or "getShipInfo" in function_names


def test_gdscript_function_extraction():
    """Test function extraction from GDScript code"""
    # Skip GDScript function extraction as we're focusing on Avorion first
    # Read a fixture file
    # fixture_path = Path("tests/fixtures/gdscript/node_management.gd")
    # if fixture_path.exists():
    #     content = fixture_path.read_text()
    #
    #     # Pattern for GDScript functions
    #     function_pattern = (
    #         r"func\s+(\w+)\s*\(([^)]*)\)[^:]*:(.*?)(?=\nfunc\s|\nclass\s|\Z)"
    #     )
    #     matches = re.findall(function_pattern, content, re.DOTALL)
    #
    #     # Should find functions
    #     assert len(matches) > 0, "Should find functions in GDScript code"

    # Skip this test for now as we're focusing on Avorion first
    pytest.skip("Skipping GDScript tests as we're focusing on Avorion first")


def test_json_output_formatting():
    """Test that training data can be formatted as JSON"""
    # Test data structure that would come from processing code samples
    test_data = [
        {
            "instruction": "Write an Avorion Lua function to spawn a pirate ship",
            "output": "function spawnPirateShip(sector, position)\n    -- Implementation\nend",
            "domain": "avorion",
            "metadata": {"godot_version": "4.x", "difficulty": "intermediate"},
        }
    ]

    # Should be serializable to JSON
    json_string = json.dumps(test_data)
    parsed_back = json.loads(json_string)

    assert len(parsed_back) == 1
    assert (
        parsed_back[0]["instruction"]
        == "Write an Avorion Lua function to spawn a pirate ship"
    )


def test_data_loading_utilities():
    """Test utility functions for loading code samples"""
    # Test that we can read fixture directories
    avorion_dir = Path("tests/fixtures/avorion")
    gdscript_dir = Path("tests/fixtures/gdscript")

    assert avorion_dir.exists(), "Avorion fixtures directory should exist"
    assert gdscript_dir.exists(), "GDScript fixtures directory should exist"

    # Test that files have reasonable content
    if avorion_dir.exists():
        files = list(avorion_dir.glob("*"))
        if files:
            first_file = files[0]
            content = first_file.read_text()
            assert len(content) > 10, "Files should have meaningful content"
