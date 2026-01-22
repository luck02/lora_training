# LoRA Training Pipeline

A production-ready pipeline for training domain-specific LoRA/DoRA adapters on large language models. Currently supports **Qwen3** models with plans for unified multi-domain training.

## Features

- **Reverse-prompting dataset generation** using Anthropic's Claude API
- **QLoRA/DoRA training** with PEFT, bitsandbytes, and TRL
- **Multi-domain support** for game development scripting languages
- **Quality filtering** (syntax validation, length checks, deduplication)
- **Configurable training** via YAML inheritance system
- **vLLM deployment** support with FP8 quantization (planned)

## Supported Domains

| Domain | Language | Description |
|--------|----------|-------------|
| **Avorion** | Lua | Game modding for ship systems, sectors, factions |
| **Godot** | GDScript | Game development with Godot Engine |
| **FLECS** | C/C++ | Entity Component System patterns (planned) |

## Quick Start

### Prerequisites

- Python 3.11+
- CUDA-capable GPU (for training)
- Anthropic API key (for dataset generation)

### Installation

```bash
git clone https://github.com/yourusername/lora-training.git
cd lora-training
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Generate Training Data

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"

# Place raw code samples in data/<domain>/raw/
# Then generate training pairs:
python scripts/generate_dataset.py --domain avorion
```

### Train an Adapter

```bash
python scripts/train.py --config config/avorion.yaml
```

### Merge and Deploy

```bash
# Merge adapter with base model
python scripts/merge.py --config config/avorion.yaml --output ./merged-model

# Convert for vLLM (optional)
python scripts/convert_vllm.py --model ./merged-model --name my-model --config config/avorion.yaml
```

## Project Structure

```
lora-training/
├── config/                 # Training configurations
│   ├── base.yaml          # Shared defaults
│   ├── avorion.yaml       # Avorion-specific config
│   └── gdscript.yaml      # GDScript-specific config
├── data/                   # Training data
│   └── <domain>/
│       ├── raw/           # Source code files
│       └── train.jsonl    # Generated training pairs
├── scripts/                # Core pipeline scripts
├── tests/                  # Test suite
├── adapters/               # Output: trained adapters
└── ideas/                  # Planning documents
```

## Configuration

Training uses a YAML inheritance system:

```yaml
# config/base.yaml - shared defaults
model:
  name: "Qwen/Qwen3-Coder-30B-A3B-Instruct"
  load_in_4bit: true

training:
  max_seq_length: 2048
  num_epochs: 3
  batch_size: 2
  learning_rate: 2e-4

lora:
  r: 16
  alpha: 32
  target_modules:
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
```

Domain configs override base settings:

```yaml
# config/avorion.yaml
domain: avorion
training:
  num_epochs: 5  # More epochs for smaller dataset
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
make test

# Run quality checks (lint + tests + coverage)
make check
```

## Quality Standards

- **Linting**: Zero ruff errors
- **Coverage**: 80% minimum
- **Complexity**: McCabe <= 15 per function

Run `make check` before committing.

## Roadmap

See `ideas/qwen3-80b-unified-adapter-plan.md` for the full architectural plan.

### Current (v0.1)
- [x] Separate adapters per domain
- [x] Local QLoRA training on Qwen3-30B
- [x] Anthropic API dataset generation
- [x] Basic quality filtering

### Planned (v0.2)
- [ ] Unified multi-domain adapter
- [ ] Cloud training support (8x H100)
- [ ] DoRA (Weight-Decomposed LoRA)
- [ ] 64k context length
- [ ] FLECS ECS domain
- [ ] GDExtension C++ support
- [ ] FP8 quantization
- [ ] HuggingFace publication

## Contributing

See `CONTRIBUTING.md` for development guidelines.

1. Fork the repository
2. Create a feature branch
3. Run `make check` before committing
4. Submit a pull request

## License

[MIT License](LICENSE) (to be added)

## Acknowledgments

- [Qwen](https://github.com/QwenLM/Qwen) for the base models
- [PEFT](https://github.com/huggingface/peft) for parameter-efficient fine-tuning
- [TRL](https://github.com/huggingface/trl) for training utilities
- [Anthropic](https://anthropic.com) for Claude API (dataset generation)
