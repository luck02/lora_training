# Qwen3-Next-80B Unified Adapter Training Plan

## Executive Summary

This plan outlines the architecture and procedures for training a unified LoRA/DoRA adapter on **Qwen3-Next-80B-A3B-Instruct** covering three domains:
1. **Avorion** - Lua game modding
2. **Godot** - GDScript + GDExtension C++ interop
3. **FLECS** - Entity Component System patterns

**Training**: Cloud (8x H100) | **Inference**: DGX Spark (FP8, 128GB)

---

## Phase 1: Repository Architecture Changes

### 1.1 Configuration System Overhaul

**Current**: Separate configs per domain (`avorion.yaml`, `gdscript.yaml`)
**New**: Unified config with multi-domain support

```
config/
├── base.yaml              # Shared defaults (update for 80B model)
├── unified.yaml           # NEW: Multi-domain unified training config
├── avorion.yaml           # Keep for standalone training (optional)
├── gdscript.yaml          # Keep for standalone training (optional)
└── cloud/
    ├── h100x8.yaml        # Cloud-specific training params
    └── dgx-spark.yaml     # Inference config for DGX Spark
```

**Key config changes for `base.yaml`:**
```yaml
model:
  name: "Qwen/Qwen3-Next-80B-A3B-Instruct"  # Updated model
  load_in_4bit: true  # For cloud QLoRA (or false for DoRA)

training:
  max_seq_length: 65536  # CONFIRMED: 64k context (increased from 2048)
  gradient_checkpointing: true  # Required for 64k context

lora:
  r: 64  # Increased rank for larger model
  alpha: 128
  target_modules:  # MoE-aware targeting
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
    # Note: Do NOT target router/gate modules in MoE
```

### 1.2 Data Directory Restructure

```
data/
├── unified/
│   ├── train.jsonl        # Combined training data
│   ├── eval.jsonl         # Combined eval data
│   └── raw/
│       ├── avorion/       # Symlink to existing
│       ├── godot/         # Expanded GDScript + GDExtension
│       └── flecs/         # NEW: FLECS source code
├── avorion/               # Keep existing
├── gdscript/              # Keep existing (expand with GDExtension)
└── flecs/                 # NEW domain
    ├── train.jsonl
    └── raw/
        ├── flecs_core.h
        ├── flecs_systems.c
        └── ... (cloned from FLECS repo)
```

### 1.3 New Scripts Required

```
scripts/
├── train.py               # Update for DoRA support + long context
├── train_cloud.py         # NEW: Cloud-optimized training script
├── merge_offload.py       # NEW: Disk-offloaded merge for 80B model
├── quantize_fp8.py        # NEW: FP8 quantization script
├── generate_dataset.py    # Update for unified multi-domain generation
├── fetch_flecs.py         # NEW: Clone and prepare FLECS training data
├── fetch_gdextension.py   # NEW: Fetch godot-cpp examples
└── validate_unified.py    # NEW: Validate domain balance in dataset
```

---

## Phase 2: Data Collection Strategy

### 2.1 Domain: Avorion (Existing)

**Source**: `/Users/garyclucas/Library/Application Support/Steam/steamapps/common/Avorion/data/`

**Status**: Partially collected (10+ Lua files in `data/avorion/raw/`)

**Action**:
- Expand collection to include more sector scripts, entity systems
- Target: ~300-400 Lua files for comprehensive API coverage
- Generate **~2000 instruction-output pairs** (CONFIRMED: 6000 total dataset)

**System Prompt**:
```
You are an expert Avorion game modder specializing in Lua scripting
for ship systems, sector generation, faction mechanics, and game events.
```

### 2.2 Domain: Godot (Expand)

**Sources**:
1. Existing GDScript samples
2. **NEW**: `godot-cpp` repository (GDExtension bindings)
3. **NEW**: Official GDExtension examples
4. **NEW**: Godot documentation code samples

**Data to collect**:
- GDScript patterns (existing)
- GDExtension C++ bindings examples
- Node registration, signal handling in C++
- Custom resource types

**System Prompt**:
```
You are an expert Godot 4 developer specializing in GDScript,
GDExtension C++ bindings, node systems, signals, and game architecture.
```

### 2.3 Domain: FLECS (New)

**Source**: https://github.com/SanderMertens/flecs

**Data to collect**:
- Core headers (`flecs.h`, `flecs.hpp`)
- Example code from `examples/` directory
- Documentation code snippets
- Query patterns, system definitions, component relationships

**Key FLECS patterns to emphasize**:
```c
// Component definition
ECS_COMPONENT(world, Position);
ECS_COMPONENT(world, Velocity);

// System definition
ECS_SYSTEM(world, Move, EcsOnUpdate, Position, Velocity);

// Query patterns
ecs_query_t *q = ecs_query(world, {
    .filter.terms = {{ ecs_id(Position) }, { ecs_id(Velocity) }}
});
```

**System Prompt**:
```
You are an expert in FLECS Entity Component System, data-oriented design,
and integrating ECS architectures with game engines like Godot via GDExtension.
```

### 2.4 Cross-Domain Examples (Critical)

Train on examples that **bridge domains**:

```jsonl
{"instruction": "Create a FLECS system that syncs entity positions with Godot Node3D transforms via GDExtension", "output": "..."}
{"instruction": "Design an Avorion-style sector generation system using FLECS archetypes", "output": "..."}
```

This teaches the model to combine knowledge across domains.

---

## Phase 3: Training Pipeline

### 3.1 Dataset Generation Updates

Update `scripts/generate_dataset.py`:

```python
DOMAINS = {
    "avorion": {
        "system_prompt": "You are an expert Avorion...",
        "raw_path": "data/avorion/raw",
        "file_patterns": ["*.lua"],
        "weight": 1.0,  # Relative sampling weight
    },
    "godot": {
        "system_prompt": "You are an expert Godot 4...",
        "raw_path": "data/gdscript/raw",
        "file_patterns": ["*.gd", "*.cpp", "*.hpp"],
        "weight": 1.2,  # Slightly oversample
    },
    "flecs": {
        "system_prompt": "You are an expert in FLECS...",
        "raw_path": "data/flecs/raw",
        "file_patterns": ["*.c", "*.h", "*.cpp", "*.hpp"],
        "weight": 1.5,  # Oversample newer domain
    },
}
```

**Unified dataset format** (`data/unified/train.jsonl`):
```jsonl
{"domain": "avorion", "system": "You are an expert...", "instruction": "...", "output": "..."}
{"domain": "flecs", "system": "You are an expert...", "instruction": "...", "output": "..."}
{"domain": "godot", "system": "You are an expert...", "instruction": "...", "output": "..."}
```

### 3.2 Training Script Updates

**For cloud training** (`scripts/train_cloud.py`):

```python
# Key differences from local train.py:

# 1. DoRA support (optional, for maximum quality)
from peft import LoraConfig
lora_config = LoraConfig(
    r=64,
    lora_alpha=128,
    use_dora=True,  # Weight-Decomposed LoRA
    target_modules=[...],
)

# 2. Gradient checkpointing for long context
model.gradient_checkpointing_enable()

# 3. DeepSpeed ZeRO-3 for multi-GPU
training_args = TrainingArguments(
    deepspeed="config/deepspeed_zero3.json",
    ...
)

# 4. Longer context handling
max_seq_length=32768,  # or 65536

# 5. Domain-aware formatting
def format_prompt(example):
    return f"""<|im_start|>system
{example['system']}<|im_end|>
<|im_start|>user
{example['instruction']}<|im_end|>
<|im_start|>assistant
{example['output']}<|im_end|>"""
```

### 3.3 Cloud Training Configuration

**Recommended: RunPod or Lambda Labs (8x H100 80GB)**

Cost estimate: ~$25-30/hour × 4-8 hours = **$100-240**

```yaml
# config/cloud/h100x8.yaml
training:
  batch_size: 2          # Reduced for 64k context
  gradient_accumulation: 16  # Compensate for smaller batch
  num_epochs: 3
  learning_rate: 1e-4    # Lower for larger model
  warmup_ratio: 0.05
  max_seq_length: 65536  # CONFIRMED: 64k context
  bf16: true
  gradient_checkpointing: true  # Required for 64k

deepspeed:
  zero_stage: 3
  offload_optimizer: true  # Enable for 64k context headroom

lora:
  r: 64
  alpha: 128
  use_dora: true  # CONFIRMED: DoRA for maximum quality
```

---

## Phase 4: Merge and Deployment (All on Cloud)

**Key Insight**: Merge and quantize on the cloud instance, then download only the final FP8 model.

```
Training (BF16)  →  Merge (FP16)  →  Quantize (FP8)  →  Download
   Cloud              Cloud            Cloud           to DGX Spark
   ~640GB VRAM       ~200GB RAM       ~200GB RAM       ~45GB transfer
```

### 4.1 Cloud-Native Merge

Run on the same cloud instance after training completes:

```python
# scripts/merge_cloud.py
from transformers import AutoModelForCausalLM
from peft import PeftModel
import torch

# Cloud H100s have plenty of memory - no offloading needed
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
    device_map="auto",  # Distributes across H100s
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)

# Load and merge DoRA adapter
print("Loading DoRA adapter...")
model = PeftModel.from_pretrained(model, "adapters/unified-dora")
print("Merging weights...")
merged = model.merge_and_unload()

# Save with sharding for easier transfer
merged.save_pretrained(
    "./merged-80b",
    max_shard_size="5GB",
)
print("Merge complete: ./merged-80b")
```

### 4.2 FP8 Quantization (On Cloud)

Quantize before downloading to minimize transfer size:

**Option A: llm-compressor (Recommended)**
```python
# scripts/quantize_fp8.py
from llmcompressor.transformers import oneshot
from llmcompressor.modifiers.quantization import QuantizationModifier

# FP8 quantization with calibration
recipe = QuantizationModifier(
    targets="Linear",
    scheme="FP8",
    ignore=["lm_head"],  # Keep output layer in higher precision
)

oneshot(
    model="./merged-80b",
    dataset="data/unified/train.jsonl",
    recipe=recipe,
    output_dir="./merged-80b-fp8",
    num_calibration_samples=512,
    max_seq_length=4096,  # Calibration doesn't need full 64k
)
```

**Option B: AutoFP8 (Simpler)**
```bash
pip install auto-fp8
auto-fp8 ./merged-80b --output ./merged-80b-fp8 --calibration-samples 512
```

### 4.3 Download to DGX Spark

```bash
# From cloud instance - transfer only the FP8 model (~45GB)
rsync -avP --progress ./merged-80b-fp8/ user@dgx-spark:/models/qwen3-unified-fp8/

# Or use rclone for cloud storage intermediary
rclone sync ./merged-80b-fp8 s3:my-bucket/models/qwen3-unified-fp8/
```

**Fallback: Disk-Offloaded Local Merge**

If you need to merge locally (e.g., cloud instance terminated), use disk offloading:

```python
# scripts/merge_offload.py (for local use only)
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
    device_map="auto",
    offload_folder="./offload_cache",  # Spill to SSD
    offload_state_dict=True,
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
)
```

### 4.3 DGX Spark Deployment

```yaml
# config/cloud/dgx-spark.yaml
inference:
  model_path: "./merged-80b-fp8"
  dtype: "fp8"
  max_model_len: 65536
  tensor_parallel_size: 1

  # Memory estimation:
  # - FP8 model: ~40-45GB
  # - KV cache (65k ctx): ~50-60GB
  # - Total: ~100GB (fits in 128GB)
```

**vLLM launch command**:
```bash
vllm serve ./merged-80b-fp8 \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype fp8 \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.90
```

---

## Phase 5: Implementation Roadmap

### Stage 1: Data Preparation (Week 1)

- [ ] Clone FLECS repository, extract training-relevant code (~500 files)
- [ ] Clone godot-cpp, extract GDExtension examples (~200 files)
- [ ] Expand Avorion raw data collection (~400 Lua files)
- [ ] Create unified dataset generation pipeline
- [ ] Generate full dataset (~6000 examples: 2000/domain + cross-domain)
- [ ] Validate dataset quality and domain balance

### Stage 2: Local Testing (Week 1-2)

- [ ] Test training pipeline with Qwen3-30B-A3B (current model) locally
- [ ] Validate unified dataset formatting
- [ ] Test long-context (8k-16k) on local hardware
- [ ] Verify domain switching via system prompts

### Stage 3: Cloud Training (Week 2)

- [ ] Provision cloud instance (8x H100)
- [ ] Upload dataset and configs
- [ ] Run training (estimate: 4-8 hours)
- [ ] Download trained adapter

### Stage 4: Merge and Quantize (Week 2-3)

- [ ] Merge DoRA adapter on cloud instance (same session as training)
- [ ] Quantize merged model to FP8 on cloud
- [ ] Download FP8 model (~45GB) to DGX Spark

### Stage 5: Deployment and Validation (Week 3)

- [ ] Deploy on DGX Spark via vLLM
- [ ] Test all three domains
- [ ] Benchmark context length and throughput
- [ ] Iterate on system prompts if needed

### Stage 6: HuggingFace Publication (Week 3-4)

- [ ] Obtain Boxelware permission for Avorion data (see Phase 6)
- [ ] Create HuggingFace repositories
- [ ] Write model cards and dataset cards
- [ ] Upload artifacts
- [ ] Announce to community

---

## Phase 6: Community Contribution (HuggingFace Publication)

### 6.1 Licensing Requirements

**Before publishing, obtain permission for proprietary content:**

| Domain | License | Status | Action Required |
|--------|---------|--------|-----------------|
| FLECS | MIT | Clear | None - attribute in model card |
| Godot/godot-cpp | MIT | Clear | None - attribute in model card |
| Avorion | Proprietary | **Blocked** | Contact Boxelware for permission |

### 6.2 Boxelware Outreach Process

**Contact Methods** (in order of preference):
1. **Discord**: [Avorion Official Discord](https://discord.gg/avorion) - #modding or #general
2. **Email**: info@boxelware.de
3. **Steam Forums**: Avorion > Discussions > Modding

**Draft Permission Request**:

```
Subject: Permission Request - AI Training Dataset from Avorion Lua Scripts

Hi Boxelware Team,

I'm developing an open-source AI coding assistant specialized in game development,
with a focus on helping modders write Lua scripts for games like Avorion.

I would like to request permission to include instruction-response pairs derived
from Avorion's Lua scripts in a publicly available training dataset on HuggingFace.

The project would:
- Help new modders learn Avorion's Lua API through AI assistance
- Credit Avorion/Boxelware prominently in all documentation
- Potentially grow the modding community by lowering the barrier to entry
- NOT redistribute raw game files (only AI-generated instruction/response pairs)

The dataset and trained model would be freely available to the community under
a permissive license (Apache 2.0 or similar).

Would you be open to this? I'm happy to:
- Add specific attribution requirements you prefer
- Limit the scope of included content
- Provide you a copy before publication for review
- Discuss any other requirements

Thank you for creating such a moddable game!

Best regards,
[Your Name]
[GitHub/HuggingFace profile link]
```

**Follow-up Timeline**:
- Week 1: Send initial request
- Week 2: Follow up if no response
- Week 3: Try alternative contact method
- If no response after 3 weeks: Publish FLECS+Godot only adapter (no Avorion)

### 6.3 HuggingFace Repository Structure

```
huggingface.co/[your-username]/
│
├── qwen3-80b-gamedev-dora/              # DoRA Adapter (~500MB)
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   ├── tokenizer_config.json
│   ├── special_tokens_map.json
│   └── README.md                         # Model Card
│
├── gamedev-instruct-6k/                  # Dataset (~100MB)
│   ├── train.jsonl
│   ├── eval.jsonl
│   ├── metadata.json
│   └── README.md                         # Dataset Card
│
└── qwen3-80b-gamedev-fp8/               # Optional: Full Model (~45GB)
    ├── config.json
    ├── model-00001-of-00010.safetensors
    ├── model-00002-of-00010.safetensors
    │   ... (sharded weights)
    ├── tokenizer.json
    └── README.md                         # Model Card
```

### 6.4 Model Card Template

Create `README.md` for the adapter repository:

```markdown
---
license: apache-2.0
language:
- en
library_name: peft
base_model: Qwen/Qwen3-Next-80B-A3B-Instruct
tags:
- game-development
- lua
- gdscript
- ecs
- flecs
- godot
- avorion
- code-generation
- dora
datasets:
- [your-username]/gamedev-instruct-6k
---

# Qwen3-80B GameDev DoRA Adapter

A DoRA (Weight-Decomposed Low-Rank Adaptation) adapter for game development tasks,
trained on Qwen3-Next-80B-A3B-Instruct.

## Supported Domains

| Domain | Description | System Prompt Trigger |
|--------|-------------|----------------------|
| **Avorion** | Lua scripting for ship systems, sectors, factions | "You are an expert Avorion game modder..." |
| **Godot** | GDScript + GDExtension C++ bindings | "You are an expert Godot 4 developer..." |
| **FLECS** | Entity Component System patterns | "You are an expert in FLECS ECS..." |

## Usage

### With PEFT

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen3-Next-80B-A3B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# Load adapter
model = PeftModel.from_pretrained(base_model, "[your-username]/qwen3-80b-gamedev-dora")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-Next-80B-A3B-Instruct")

# Generate
messages = [
    {"role": "system", "content": "You are an expert in FLECS ECS..."},
    {"role": "user", "content": "Create a movement system with Position and Velocity components"}
]
# ... standard generation code
```

### With vLLM (Merged FP8)

```bash
vllm serve [your-username]/qwen3-80b-gamedev-fp8 \
    --dtype fp8 \
    --max-model-len 65536
```

## Training Details

| Parameter | Value |
|-----------|-------|
| Base Model | Qwen3-Next-80B-A3B-Instruct |
| Method | DoRA (Weight-Decomposed LoRA) |
| Rank | 64 |
| Alpha | 128 |
| Context Length | 65,536 tokens |
| Training Examples | ~6,000 |
| Epochs | 3 |
| Hardware | 8x NVIDIA H100 80GB |

## Limitations

- Specialized for game development; general capabilities may be slightly reduced
- Avorion domain reflects game version at training time (may not include latest API changes)
- FLECS examples based on v3.x API

## Attribution

This adapter was trained on data from:
- **FLECS** by Sander Mertens (MIT License)
- **Godot Engine** and **godot-cpp** (MIT License)
- **Avorion** by Boxelware (used with permission)

## Citation

```bibtex
@misc{qwen3-gamedev-dora-2025,
  author = {[Your Name]},
  title = {Qwen3-80B GameDev DoRA Adapter},
  year = {2025},
  publisher = {HuggingFace},
  url = {https://huggingface.co/[your-username]/qwen3-80b-gamedev-dora}
}
```
```

### 6.5 Dataset Card Template

Create `README.md` for the dataset repository:

```markdown
---
license: apache-2.0
task_categories:
- text-generation
language:
- en
tags:
- code
- game-development
- lua
- gdscript
- cpp
- ecs
size_categories:
- 1K<n<10K
---

# GameDev Instruct Dataset (6K)

An instruction-tuning dataset for game development AI assistants, covering:
- Avorion Lua modding
- Godot GDScript & GDExtension
- FLECS Entity Component System

## Dataset Structure

```json
{
  "domain": "flecs",
  "system": "You are an expert in FLECS Entity Component System...",
  "instruction": "Create a system that applies gravity to all entities with Position and Velocity components",
  "output": "// FLECS gravity system\nvoid GravitySystem(ecs_iter_t *it) {\n    Position *p = ecs_field(it, Position, 1);\n    Velocity *v = ecs_field(it, Velocity, 2);\n    \n    for (int i = 0; i < it->count; i++) {\n        v[i].y -= 9.81f * it->delta_time;\n        p[i].x += v[i].x * it->delta_time;\n        p[i].y += v[i].y * it->delta_time;\n    }\n}\n\n// Register system\nECS_SYSTEM(world, GravitySystem, EcsOnUpdate, Position, Velocity);"
}
```

## Domain Distribution

| Domain | Examples | Percentage |
|--------|----------|------------|
| Avorion | ~2,000 | 33% |
| Godot | ~2,000 | 33% |
| FLECS | ~2,000 | 33% |
| Cross-domain | ~200 | 3% |

## Data Sources

| Domain | Source | License |
|--------|--------|---------|
| FLECS | [github.com/SanderMertens/flecs](https://github.com/SanderMertens/flecs) | MIT |
| Godot | [github.com/godotengine/godot-cpp](https://github.com/godotengine/godot-cpp) | MIT |
| Avorion | Boxelware game scripts | Used with permission |

## Generation Method

Examples were generated using reverse-prompting with Claude 3.5 Sonnet:
1. Source code files were provided as context
2. Claude generated natural language instructions that would produce the code
3. Pairs were filtered for quality (syntax validity, length, deduplication)

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("[your-username]/gamedev-instruct-6k")

# Filter by domain
avorion_data = dataset.filter(lambda x: x["domain"] == "avorion")
flecs_data = dataset.filter(lambda x: x["domain"] == "flecs")
```

## Intended Use

- Fine-tuning code generation models for game development
- Training domain-specific coding assistants
- Research on multi-domain instruction tuning

## Limitations

- Avorion examples reflect a specific game version
- Code examples may require adaptation for newer API versions
- Not suitable for learning game design theory (code-focused only)
```

### 6.6 Publication Checklist

```markdown
## Pre-Publication Checklist

### Licensing
- [ ] Boxelware permission obtained (email/Discord confirmation saved)
- [ ] MIT attribution for FLECS included
- [ ] MIT attribution for Godot included
- [ ] License file (Apache 2.0) added to all repos

### Quality
- [ ] Model tested on all three domains
- [ ] Dataset validated (no PII, no secrets, syntax valid)
- [ ] Example outputs reviewed for quality
- [ ] README examples actually work

### Metadata
- [ ] Model card complete with all sections
- [ ] Dataset card complete with all sections
- [ ] Tags appropriate for discoverability
- [ ] Base model correctly linked

### Technical
- [ ] Adapter loads correctly with PEFT
- [ ] FP8 model loads correctly with vLLM
- [ ] Dataset loads correctly with `datasets` library
- [ ] File checksums/hashes documented

### Community
- [ ] Announcement post drafted for:
  - [ ] HuggingFace discussions
  - [ ] r/LocalLLaMA
  - [ ] Godot Discord/Forums
  - [ ] Avorion Discord/Forums
  - [ ] FLECS Discord
```

### 6.7 Upload Commands

```bash
# Install HuggingFace CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Upload adapter
huggingface-cli upload [your-username]/qwen3-80b-gamedev-dora ./adapters/unified-dora/

# Upload dataset
huggingface-cli upload [your-username]/gamedev-instruct-6k ./data/unified/ --repo-type dataset

# Upload full model (optional, large)
huggingface-cli upload [your-username]/qwen3-80b-gamedev-fp8 ./merged-80b-fp8/
```

---

## Confirmed Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Training Method** | DoRA | Maximum quality for reasoning/code tasks |
| **Dataset Size** | ~6000 examples | 2000/domain + cross-domain bridging examples |
| **Context Length** | 64k tokens | Full file context for complex codebases |

### Remaining Decision

**Versioning Strategy**: How to version adapters? Git LFS, HuggingFace Hub, or local storage?

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Model name incorrect | Verify HuggingFace model ID before training |
| Domain imbalance | Use weighted sampling, validate with `validate_unified.py` |
| Merge OOM | Use disk offloading, run on cloud instance with more RAM |
| FP8 quality loss | Calibrate with domain-specific data, test before deployment |
| Cloud cost overrun | Set budget alerts, use spot instances where possible |

---

## Files to Create/Modify

### New Files
- `config/unified.yaml`
- `config/cloud/h100x8.yaml`
- `config/cloud/dgx-spark.yaml`
- `config/deepspeed_zero3.json`
- `scripts/train_cloud.py`
- `scripts/merge_cloud.py` (primary - for cloud use)
- `scripts/merge_offload.py` (fallback - for local use with disk offloading)
- `scripts/quantize_fp8.py`
- `scripts/fetch_flecs.py`
- `scripts/fetch_gdextension.py`
- `scripts/validate_unified.py`
- `scripts/upload_huggingface.py` (automated HF upload with validation)
- `data/flecs/` directory structure
- `docs/MODEL_CARD.md` (template for HuggingFace)
- `docs/DATASET_CARD.md` (template for HuggingFace)
- `docs/boxelware_permission.md` (track permission request status)

### Modified Files
- `config/base.yaml` (model name, context length)
- `scripts/generate_dataset.py` (multi-domain support)
- `requirements.txt` (add deepspeed, llm-compressor, huggingface_hub)
- `CLAUDE.md` (update instructions)

---

## Next Steps

### Immediate (This Week)
1. **Review and approve this plan**
2. **Send Boxelware permission request** (don't wait - start early)
3. Begin Phase 1: Data Preparation
   - Clone FLECS repository
   - Clone godot-cpp repository
   - Expand Avorion raw data collection

### Short-term (Weeks 1-2)
4. Create unified dataset generation pipeline
5. Generate and validate ~6000 examples
6. Test locally with current 30B model

### Medium-term (Weeks 2-3)
7. Provision cloud training (8x H100)
8. Run DoRA training
9. Merge and quantize on cloud
10. Deploy to DGX Spark

### Publication (Week 3-4)
11. Finalize HuggingFace model/dataset cards
12. Upload artifacts (pending Boxelware permission)
13. Announce to community

## Decisions Confirmed

| Decision | Choice |
|----------|--------|
| ECS Library | FLECS |
| Godot Interop | GDExtension |
| Training Method | DoRA |
| Dataset Size | ~6000 examples |
| Context Length | 64k tokens |
| Domain Switching | System prompts |
| Publication | HuggingFace (pending Boxelware permission)
