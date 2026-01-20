#!/usr/bin/env python3
"""
Convert merged model to vLLM format for local inference.
Usage: python convert_vllm.py --model ./avorion-merged --name avorion-coder --config config/avorion.yaml
"""

import argparse
import os
import subprocess
import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to merged model")
    parser.add_argument("--name", required=True, help="Output model name for vLLM")
    parser.add_argument("--config", required=True)
    parser.add_argument("--quantization", default="awq")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Convert to vLLM format using HF to vLLM conversion
    print(f"Converting {args.model} to vLLM format...")
    
    # Create output directory
    output_dir = f"{args.name}_vllm"
    os.makedirs(output_dir, exist_ok=True)
    
    # For vLLM, we typically just copy the model and ensure it's properly formatted
    # vLLM handles quantization differently, so we'll use the standard HuggingFace conversion
    
    # Copy the model to vLLM format directory
    try:
        subprocess.run([
            "cp", "-r", args.model, output_dir
        ], check=True)
        print(f"Copied model to {output_dir}")
    except subprocess.CalledProcessError:
        print("Failed to copy model directory")
        return

    # Generate vLLM config file
    vllm_config = {
        "model": output_dir,
        "tokenizer": args.model,  # Use same directory for tokenizer
        "quantization": args.quantization,
        "dtype": "auto",
        "max_model_len": 32768,
        "tensor_parallel_size": 1
    }
    
    # Save config for vLLM
    config_file = f"{output_dir}/vllm_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(vllm_config, f)
    
    print(f"vLLM configuration saved to {config_file}")
    print(f"Model ready for vLLM inference in {output_dir}")
    print("\nTo run with vLLM:")
    print(f"vLLM serve {output_dir} --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()