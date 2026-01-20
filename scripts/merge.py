#!/usr/bin/env python3
"""
Merge LoRA adapter with base model.
Usage: python merge.py --config config/avorion.yaml --output ./avorion-merged
"""

import argparse
import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def load_config(config_path: str, base_path: str = "config/base.yaml") -> dict:
    with open(base_path) as f:
        config = yaml.safe_load(f)
    with open(config_path) as f:
        domain_config = yaml.safe_load(f)
    for key, value in domain_config.items():
        if isinstance(value, dict) and key in config:
            config[key].update(value)
        else:
            config[key] = value
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    config = load_config(args.config)

    print(f"Loading base model: {config['model']['name']}")
    base_model = AutoModelForCausalLM.from_pretrained(
        config["model"]["name"],
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    print(f"Loading adapter: {config['output']['adapter_dir']}")
    model = PeftModel.from_pretrained(base_model, config["output"]["adapter_dir"])

    print("Merging weights...")
    merged = model.merge_and_unload()

    print(f"Saving to {args.output}")
    merged.save_pretrained(args.output)

    tokenizer = AutoTokenizer.from_pretrained(config["model"]["name"])
    tokenizer.save_pretrained(args.output)
    print("Done!")


if __name__ == "__main__":
    main()
