# LoRA Fine-tuning Guide for Qwen3-Coder-30B-A3B-Instruct

A comprehensive pipeline for LoRA fine-tuning of Qwen models, supporting two specialized adapters:

- **GDScript LoRA**: For Godot Engine game development with GDScript scripting
- **Avorion LoRA**: For Avorion Lua scripting for game modding

## Core Workflow
1. **Dataset Generation**: Reverse-prompting with Anthropic Batch API to create Q&A pairs from source code
2. **Quality Filtering**: Automated checks for length, syntax validity, and deduplication
3. **Training**: Separate LoRA training jobs using PEFT, bitsandbytes with hardware-specific optimizations
4. **Deployment**: Merge adapters with base model or convert to GGUF for Ollama integration

## Configuration
- Base config (`config/base.yaml`) with shared training defaults
- Domain configs (`config/avorion.yaml`, `config/gdscript.yaml`) for adapter-specific settings
- System prompts tailored to each domain's workflow

## Test Status
All tests are now passing (31 passed, 1 skipped). The skipped test relates to GDScript fixtures which are not currently required as we focus on Avorion development.

## Typical Commands
```bash
# Setup
mkdir -p lora-training/{config,data/avorion/raw,data/gdscript/raw,scripts,adapters,output}
cd lora-training
pip install -r requirements.txt

# Generate datasets (requires raw code samples in data/<domain>/raw directories)
python scripts/generate_dataset.py --domain avorion
python scripts/generate_dataset.py --domain gdscript

# Train adapters
python scripts/train.py --config config/avorion.yaml
python scripts/train.py --config config/gdscript.yaml

# Merge and deploy (optional)
python scripts/merge.py --config config/avorion.yaml --output ./avorion-merged
python scripts/convert_ollama.py --model ./avorion-merged --name avorion-coder --config config/avorion.yaml
```

## Generating Fixture Data
To generate training data, you need to provide raw code samples in the respective domain directories:
- Avorion: Place Lua code samples in `data/avorion/raw/`
- GDScript: Place GDScript code samples in `data/gdscript/raw/`

Then run the dataset generation script:
```bash
python scripts/generate_dataset.py --domain avorion
python scripts/generate_dataset.py --domain gdscript
```

This will create training JSONL files in `data/<domain>/train.jsonl` which are used for LoRA training.
```

## Notes
- Training time varies with dataset size and hardware (≈2-12 hours)
- Quality filtering prevents noisy data from degrading model performance
- Sample outputs are saved in `output/` with domain-specific adapter directories