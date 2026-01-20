#!/usr/bin/env python3
"""
Train a LoRA adapter for a specific domain.
Usage: python train.py --config config/avorion.yaml
       python train.py --config config/gdscript.yaml
"""

import argparse
import torch
import yaml
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer


def load_config(config_path: str, base_path: str = "config/base.yaml") -> dict:
    """Load and merge base + domain configs."""
    with open(base_path) as f:
        config = yaml.safe_load(f)
    with open(config_path) as f:
        domain_config = yaml.safe_load(f)

    # Deep merge
    for key, value in domain_config.items():
        if isinstance(value, dict) and key in config:
            config[key].update(value)
        else:
            config[key] = value
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to domain config")
    parser.add_argument("--resume", type=str, help="Resume from checkpoint")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Training LoRA for: {config['domain']}")
    print(f"Base model: {config['model']['name']}")

    # Quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config["model"]["load_in_4bit"],
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load model
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        config["model"]["name"],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    tokenizer = AutoTokenizer.from_pretrained(config["model"]["name"])
    tokenizer.pad_token = tokenizer.eos_token

    # LoRA
    lora_config = LoraConfig(
        r=config["lora"]["r"],
        lora_alpha=config["lora"]["alpha"],
        target_modules=config["lora"]["target_modules"],
        lora_dropout=config["lora"]["dropout"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Dataset
    dataset = load_dataset(
        "json", data_files=config["data"]["train_file"], split="train"
    )
    print(f"Training on {len(dataset)} examples")

    prompt_template = config["prompt_template"]

    def format_prompt(example):
        return prompt_template.format(**example)

    # Training
    training_args = TrainingArguments(
        output_dir=config["output"]["adapter_dir"],
        num_train_epochs=config["training"]["num_epochs"],
        per_device_train_batch_size=config["training"]["batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation"],
        learning_rate=config["training"]["learning_rate"],
        warmup_ratio=config["training"]["warmup_ratio"],
        logging_steps=config["output"]["logging_steps"],
        save_steps=config["output"]["save_steps"],
        save_total_limit=3,
        bf16=config["training"]["bf16"],
        optim="paged_adamw_8bit",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        formatting_func=format_prompt,
        max_seq_length=config["training"]["max_seq_length"],
        tokenizer=tokenizer,
    )

    print("Starting training...")
    trainer.train(resume_from_checkpoint=args.resume)

    model.save_pretrained(config["output"]["adapter_dir"])
    tokenizer.save_pretrained(config["output"]["adapter_dir"])
    print(f"Saved adapter to {config['output']['adapter_dir']}")


if __name__ == "__main__":
    main()
