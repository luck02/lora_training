# GB10 vLLM Optimization Guide

## Current Working Config (50% speedup achieved!)

```yaml
services:
  vllm-qwen3-80b-fp8:
    image: vllm-node
    container_name: qwen3-80b-fp8
    command: >
      vllm serve Qwen/Qwen3-Next-80B-A3B-Instruct-FP8
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization 0.90
      --max-model-len 131072
      --trust-remote-code
      --enable-auto-tool-choice
      --tool-call-parser hermes
      --default-chat-template-kwargs '{"enable_thinking": false}'
      --speculative-config '{"method": "qwen3_next_mtp", "num_speculative_tokens": 2}'
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - ./moe-configs:/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/fused_moe/configs/:ro
    ipc: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

**Key flags:**
- `--default-chat-template-kwargs '{"enable_thinking": false}'` - Disables Qwen3-Next thinking mode (prevents `<think>` blocks and empty content responses)
- `./moe-configs` volume mount - For self-tuned MoE kernel configs (create dir first: `mkdir -p moe-configs`)

### Performance Results

| Metric | Before | After |
|--------|--------|-------|
| Generation throughput | ~38 tok/s | **57-63 tok/s** |
| Draft acceptance rate | N/A | **95-98%** |
| Mean acceptance length | N/A | ~2.9 tokens |

---

## Next Optimization: MoE Kernel Tuning

### The Problem

You're seeing this warning:
```
WARNING: Using default MoE config. Performance might be sub-optimal!
Config file not found at: E=512,N=512,device_name=NVIDIA_GB10,dtype=fp8_w8a8,block_shape=[128,128].json
```

vLLM doesn't have pre-tuned MoE kernel configs for GB10 yet.

### Step 1: Update docker-compose for persistent configs

```yaml
services:
  vllm-qwen3-80b-fp8:
    image: vllm-node
    container_name: qwen3-80b-fp8
    command: >
      vllm serve Qwen/Qwen3-Next-80B-A3B-Instruct-FP8
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization 0.90
      --max-model-len 131072
      --trust-remote-code
      --enable-auto-tool-choice
      --tool-call-parser hermes
      --speculative-config '{"method": "qwen3_next_mtp", "num_speculative_tokens": 2}'
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
      - ./moe-configs:/moe-configs  # For tuning output
    ipc: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### Step 2: Run the MoE benchmark tuner

```bash
# Stop the server first
docker compose down

# Run tuning (this will take a while - hours for full tune)
docker run --rm --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v $(pwd)/moe-configs:/moe-configs \
  vllm-node \
  python3 -m vllm.benchmarks.kernels.benchmark_moe \
    --model Qwen/Qwen3-Next-80B-A3B-Instruct-FP8 \
    --tp-size 1 \
    --dtype auto \
    --tune \
    --batch-size 1 2 4 8 16 32 64 \
    --save-dir /moe-configs/
```

**Note:** Full tuning can take many hours. For faster results, reduce batch sizes:
```bash
--batch-size 1 4 16
```

### Step 3: Copy configs into vLLM

After tuning, you'll have JSON files like:
```
E=512,N=512,device_name=NVIDIA_GB10,dtype=fp8_w8a8,block_shape=[128,128].json
```

Option A - Mount directly (requires rebuilding image):
```yaml
volumes:
  - ./moe-configs:/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/fused_moe/configs/:ro
```

Option B - Copy into container:
```bash
docker cp ./moe-configs/*.json qwen3-80b-fp8:/usr/local/lib/python3.12/dist-packages/vllm/model_executor/layers/fused_moe/configs/
docker restart qwen3-80b-fp8
```

### Step 4: Verify configs are loaded

After restart, you should NOT see the "Using default MoE config" warning.

---

## Alternative: Check Community Configs

Before tuning from scratch, check if someone has already tuned GB10:

- https://github.com/MissionSquad/vllm-moe-configs
- Search vLLM GitHub issues for "GB10 moe config"

---

## Expected Additional Improvement

Per vLLM docs, tuned MoE configs typically give **10-30% additional throughput** on MoE models.

Combined with speculative decoding, you could potentially reach **70-80+ tok/s**.

---

## Troubleshooting

### Tuning fails or is too slow

Reduce search space:
```bash
# Minimal tune (faster, less optimal)
--batch-size 1 8 32
```

### Configs not loading

Check the filename matches exactly:
- `E=512` - number of experts
- `N=512` - expert hidden size
- `device_name=NVIDIA_GB10` - must match your GPU name exactly
- `dtype=fp8_w8a8` - must match your model dtype
- `block_shape=[128,128]` - block configuration

Run this to see your exact GPU name:
```bash
docker exec qwen3-80b-fp8 python3 -c "import torch; print(torch.cuda.get_device_name())"
```

---

## References

- [vLLM MoE Kernel Features](https://docs.vllm.ai/en/latest/design/moe_kernel_features/)
- [MissionSquad vllm-moe-configs](https://github.com/MissionSquad/vllm-moe-configs)
- [vLLM Blackwell Blog](https://blog.vllm.ai/2025/10/09/blackwell-inferencemax.html)
- [NVIDIA Forums: vLLM on GB10](https://forums.developer.nvidia.com/t/vllm-on-gb10-gpt-oss-120b-mxfp4-slower-than-sglang-llama-cpp-what-s-missing/356651)
