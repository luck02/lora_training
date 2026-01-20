"""
Test configuration and fixtures for LoRA training framework
"""

import pytest
import json
from pathlib import Path


@pytest.fixture(scope="session")
def avorion_fixture_files():
    """Provide paths to Avorion fixture files"""
    fixture_dir = Path("tests/fixtures/avorion")
    return list(fixture_dir.glob("*.lua"))


@pytest.fixture(scope="session")
def gdscript_fixture_files():
    """Provide paths to GDScript fixture files"""
    fixture_dir = Path("tests/fixtures/gdscript")
    return list(fixture_dir.glob("*.gd"))


@pytest.fixture(scope="session")
def base_config():
    """Provide base configuration for testing"""
    return {
        "training": {
            "num_epochs": 3,
            "batch_size": 2,
            "gradient_accumulation": 4,
            "learning_rate": 2e-4,
            "warmup_ratio": 0.03,
            "max_seq_length": 2048,
            "bf16": True,
        },
        "lora": {
            "r": 16,
            "alpha": 32,
            "dropout": 0.05,
            "target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
        },
        "model": {"name": "Qwen/Qwen3-Coder-30B-A3B-Instruct", "load_in_4bit": True},
        "output": {"save_steps": 100, "logging_steps": 10},
    }


@pytest.fixture(scope="session")
def avorion_config():
    """Provide Avorion domain configuration"""
    return {
        "domain": "avorion",
        "description": "Avorion game modding with Lua",
        "data": {
            "train_file": "data/avorion/train.jsonl",
            "eval_file": "data/avorion/eval.jsonl",
        },
        "output": {"adapter_dir": "adapters/avorion-lora"},
        "prompt_template": """### Instruction:\n{instruction}\n\n### Response:\n{output}""",
        "system_prompt": "You are an expert Avorion game modder specializing in Lua scripting for ship systems, sector generation, and game mechanics.",
        "training": {"num_epochs": 5},
    }


@pytest.fixture(scope="session")
def gdscript_config():
    """Provide GDScript domain configuration"""
    return {
        "domain": "gdscript",
        "description": "Godot 4.x game development with GDScript",
        "data": {
            "train_file": "data/gdscript/train.jsonl",
            "eval_file": "data/gdscript/eval.jsonl",
        },
        "output": {"adapter_dir": "adapters/gdscript-lora"},
        "prompt_template": """### Instruction:\n{instruction}\n\n### Response:\n{output}""",
        "system_prompt": "You are an expert Godot 4 game developer specializing in GDScript, node systems, signals, and game architecture.",
        "training": {"num_epochs": 3},
    }


@pytest.fixture(scope="session")
def anthropic_responses():
    """Load real Anthropic API responses for testing"""
    responses = {}

    # Load anthropic responses if they exist
    response_dir = Path("tests/fixtures/anthropic_responses")
    if response_dir.exists():
        for response_file in response_dir.glob("*.json"):
            with open(response_file, 'r') as f:
                responses[response_file.stem] = json.load(f)

    return responses
