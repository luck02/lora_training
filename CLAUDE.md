# CLAUDE.md

Instructions for AI coding assistants working on this repository.

# Project Guidelines

## Critical Tool Use Rules
* **Read Before Write:** You generally lack file context. You MUST use the `View` or `Read` tool on a file BEFORE you attempt to use the `Edit` or `Write` tool on it. Never guess file content. The system will reject writes to unread files.

## Local Model Adjustments
* **Be Concise:** Avoid pleasantries. Go straight to the solution.
* **No Hallucinations:** If a file path is uncertain, list the directory first.

## Interaction Style
* **NO PRE-AMBLE:** Do not explain what you are about to do. Do not use phrases like "(now checking...)" or "(no files found...)".
* **Direct Tool Use:** Output the Tool Use block IMMEDIATELY.
* **Silence Thoughts:** If you need to reason, do it internally or inside the tool's "thought" parameter if available. Do not output raw text before a tool call.

## Project Overview

This is a **LoRA/DoRA fine-tuning pipeline** for training domain-specific coding assistants. The project is transitioning from a prototype state to a production-ready unified training system.

### Current State
- **Base Model**: Qwen3-Coder-30B-A3B-Instruct (4-bit QLoRA)
- **Domains**: Avorion (Lua), GDScript (Godot)
- **Training**: Local, separate adapters per domain
- **Status**: Working prototype

### Planned State (See `ideas/qwen3-80b-unified-adapter-plan.md`)
- **Base Model**: Qwen3-Next-80B-A3B-Instruct
- **Domains**: Avorion (Lua), Godot (GDScript + GDExtension), FLECS (ECS)
- **Training**: Cloud (8x H100), DoRA, 64k context, unified adapter
- **Deployment**: FP8 quantized on DGX Spark

## Rules

1. **Always read before writing**: Use the Read tool before editing any file.
2. **Use the virtual environment**: All Python commands must run in `.venv`.
3. **Run quality checks before committing**: `make check` or `python scripts/quality_check.py`.
4. **Reference the plan**: Major architectural decisions are in `ideas/qwen3-80b-unified-adapter-plan.md`.

## Quick Reference

### Environment Setup
```bash
cd /Users/garyclucas/dev/lora-training
source .venv/bin/activate
pip install -r requirements.txt
```

### Common Commands
```bash
# Quality checks
make check              # Run all checks
make check-fix          # Auto-fix then check
make test               # Run tests only
make lint               # Lint only

# Dataset generation (requires ANTHROPIC_API_KEY)
python scripts/generate_dataset.py --domain avorion
python scripts/generate_dataset.py --domain gdscript

# Training (local)
python scripts/train.py --config config/avorion.yaml
python scripts/train.py --config config/gdscript.yaml

# Merge adapter with base model
python scripts/merge.py --config config/avorion.yaml --output ./merged

# Run tests
python -m pytest tests/ -v
```

## Directory Structure

```
lora-training/
├── config/                 # Training configurations
│   ├── base.yaml          # Shared defaults
│   ├── avorion.yaml       # Avorion-specific config
│   └── gdscript.yaml      # GDScript-specific config
├── data/                   # Training data
│   ├── avorion/
│   │   ├── raw/           # Source Lua files
│   │   └── train.jsonl    # Generated training pairs
│   └── gdscript/
│       ├── raw/           # Source GDScript files
│       └── train.jsonl    # Generated training pairs
├── scripts/                # Core scripts (see below)
├── tests/                  # Test suite
├── adapters/               # Output: trained LoRA adapters
├── ideas/                  # Planning documents
└── docs/                   # Documentation (to be created)
```

## Core Scripts

| Script | Purpose |
|--------|---------|
| `train.py` | Main training loop (PEFT + TRL) |
| `generate_dataset.py` | Create training data via Anthropic API |
| `merge.py` | Merge LoRA adapter with base model |
| `convert_vllm.py` | Prepare model for vLLM deployment |
| `quality_check.py` | Lint, test, coverage checks |
| `prompts.py` | Domain-specific prompt templates |
| `json_utils.py` | JSON parsing utilities |
| `json_parser_fix.py` | Robust JSON extraction from API responses |
| `prepare_avorion_dataset.py` | Avorion-specific data preparation |
| `generate_fixtures.py` | Generate test fixtures |
| `capture_anthropic_responses.py` | Capture real API responses for testing |

## Configuration System

Configurations use YAML with inheritance:
- `config/base.yaml`: Shared defaults (model, LoRA params, training params)
- `config/<domain>.yaml`: Domain-specific overrides

Key parameters:
```yaml
model:
  name: "Qwen/Qwen3-Coder-30B-A3B-Instruct"
  load_in_4bit: true

training:
  max_seq_length: 2048
  num_epochs: 3
  batch_size: 2

lora:
  r: 16
  alpha: 32
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
```

## Data Pipeline

1. **Raw code** in `data/<domain>/raw/` (Lua, GDScript files)
2. **Reverse-prompting** via Anthropic API generates instruction-output pairs
3. **Quality filtering** (length, syntax, deduplication)
4. **Output** to `data/<domain>/train.jsonl`

Training data format:
```json
{"instruction": "How do I spawn a ship in Avorion?", "output": "function spawnShip()..."}
```

## External Data Sources

- **Avorion**: `/Users/garyclucas/Library/Application Support/Steam/steamapps/common/Avorion/data/`
- **FLECS** (planned): https://github.com/SanderMertens/flecs
- **godot-cpp** (planned): https://github.com/godotengine/godot-cpp

## Testing

Tests use pytest with mocked Anthropic API responses:
```bash
python -m pytest tests/ -v                    # Run all tests
python -m pytest tests/test_config.py -v      # Run specific test file
python -m pytest tests/ --cov=scripts         # With coverage
```

Test fixtures in `tests/fixtures/` contain sample code and mock API responses.

## Quality Standards

- **Linting**: Zero ruff errors
- **Coverage**: 80% minimum
- **Complexity**: McCabe <= 15 per function
- **Tests**: All must pass

## Key Files to Understand

When working on this project, start by reading:
1. `ideas/qwen3-80b-unified-adapter-plan.md` - Full architectural plan
2. `config/base.yaml` - Training defaults
3. `scripts/generate_dataset.py` - Data generation pipeline
4. `scripts/train.py` - Training loop

## Environment Variables

Required:
- `ANTHROPIC_API_KEY`: For dataset generation

Optional:
- Set via `.envrc` (direnv) or export manually

## Notes for AI Assistants

- The project is in transition. Current code works with Qwen3-30B; planned code targets Qwen3-80B.
- Don't create new config files without consulting the plan document.
- The `ideas/` directory contains planning docs, not implementation.
- When adding features, check if they align with the unified adapter plan.
- Prefer editing existing files over creating new ones.
