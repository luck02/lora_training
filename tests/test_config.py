"""
Configuration validation tests for LoRA training framework
"""

import yaml
import pytest
from pathlib import Path
from tests.conftest import base_config, avorion_config, gdscript_config


def test_base_config_loading():
    """Test that base configuration loads correctly"""
    config_path = Path("config/base.yaml")
    assert config_path.exists(), "Base config file should exist"

    with open(config_path, "r") as f:
        loaded_config = yaml.safe_load(f)

    # Basic structure validation
    assert "training" in loaded_config
    assert "lora" in loaded_config
    assert "model" in loaded_config
    assert "output" in loaded_config

    # Specific parameter validation
    assert loaded_config["model"]["name"] == "Qwen/Qwen3-Coder-30B-A3B-Instruct"
    assert loaded_config["model"]["load_in_4bit"] == True
    assert loaded_config["training"]["batch_size"] == 2


def test_avorion_config_loading():
    """Test that Avorion configuration loads correctly"""
    config_path = Path("config/avorion.yaml")
    assert config_path.exists(), "Avorion config file should exist"

    with open(config_path, "r") as f:
        loaded_config = yaml.safe_load(f)

    # Validate domain-specific settings
    assert loaded_config["domain"] == "avorion"
    assert loaded_config["description"] == "Avorion game modding with Lua"
    assert loaded_config["output"]["adapter_dir"] == "adapters/avorion-lora"
    assert "system_prompt" in loaded_config
    assert loaded_config["training"]["num_epochs"] == 5


def test_gdscript_config_loading():
    """Test that GDScript configuration loads correctly"""
    config_path = Path("config/gdscript.yaml")
    assert config_path.exists(), "GDScript config file should exist"

    with open(config_path, "r") as f:
        loaded_config = yaml.safe_load(f)

    # Validate domain-specific settings
    assert loaded_config["domain"] == "gdscript"
    assert loaded_config["description"] == "Godot 4.x game development with GDScript"
    assert loaded_config["output"]["adapter_dir"] == "adapters/gdscript-lora"
    assert "system_prompt" in loaded_config
    assert loaded_config["training"]["num_epochs"] == 3


def test_config_merging(base_config, avorion_config):
    """Test that configuration merging works correctly"""
    # Simulate merging base and domain configs
    merged_config = base_config.copy()

    # Update with domain-specific values
    for key, value in avorion_config.items():
        if isinstance(value, dict) and key in merged_config:
            merged_config[key].update(value)
        else:
            merged_config[key] = value

    # Validate merged results
    assert merged_config["model"]["name"] == "Qwen/Qwen3-Coder-30B-A3B-Instruct"
    assert merged_config["training"]["num_epochs"] == 5  # From avorion config
    assert merged_config["output"]["adapter_dir"] == "adapters/avorion-lora"


def test_all_configs_have_required_fields():
    """Test that all configs contain required fields"""
    configs = [
        ("config/base.yaml", "base"),
        ("config/avorion.yaml", "avorion"),
        ("config/gdscript.yaml", "gdscript"),
    ]

    for config_path, config_type in configs:
        path = Path(config_path)
        assert path.exists(), f"{config_type} config file should exist"

        with open(path, "r") as f:
            config = yaml.safe_load(f)

        # All configs should have basic structure
        assert "model" in config, f"{config_type} config should have model section"
        assert "output" in config, f"{config_type} config should have output section"
