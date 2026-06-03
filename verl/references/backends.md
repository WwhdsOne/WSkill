# Training & Inference Backends

verl supports multiple backends for both training and inference. The choice of backend affects throughput, memory usage, and compatibility with different model architectures.

## Training Engines

### FSDP (Fully Sharded Data Parallel)

**Location**: `verl/workers/engine/fsdp/`
**Config**: `actor_rollout_ref.actor.strategy=fsdp`

PyTorch-native distributed training. Shards model parameters, gradients, and optimizer states across GPUs.

**When to use**:
- Default choice for most use cases
- Good for models up to ~70B parameters
- Best for single-node or small multi-node setups
- Well-tested and stable

**Key options**:
```yaml
actor_rollout_ref.actor.strategy: fsdp
actor_rollout_ref.actor.fsdp_config:
  param_offload: False       # Offload params to CPU
  optimizer_offload: False   # Offload optimizer state to CPU
  wrap_policy:
    min_num_params: 0        # FSDP unit size
  fsdp_size: -1             # -1 = auto
```

### FSDP2

**Location**: `verl/workers/engine/fsdp/` (FSDP2 codepath)
**Config**: `actor_rollout_ref.actor.strategy=fsdp2`

Recommended by PyTorch distributed team. Better throughput and memory efficiency than FSDP.

**Key advantages over FSDP**:
- Better memory management
- Higher throughput for large models
- CPU offloading integrated
- Recommended for new setups

**Key options**:
```yaml
actor_rollout_ref.actor.strategy: fsdp2
actor_rollout_ref.actor.fsdp_config:
  param_offload: True        # Commonly enabled for memory
  optimizer_offload: True
```

### Megatron-LM

**Location**: `verl/workers/engine/megatron/`
**Config**: `actor_rollout_ref.actor.strategy=megatron`

NVIDIA's distributed training framework. Uses tensor parallelism, pipeline parallelism, and expert parallelism.

**When to use**:
- Models > 70B parameters (e.g., DeepSeek 671B)
- Need tensor parallelism and pipeline parallelism
- Mixture-of-Experts (MoE) architectures
- Multi-node training at scale

**Key options**:
```yaml
actor_rollout_ref.actor.strategy: megatron
actor_rollout_ref.actor.megatron:
  tensor_model_parallel_size: 2
  pipeline_model_parallel_size: 1
  expert_model_parallel_size: 1
  virtual_pipeline_model_parallel_size: null
  context_parallel_size: 1
  sequence_parallel: true
  use_distributed_optimizer: true
```

**Checkpoint conversion**: Need `scripts/converter_hf_to_mcore.py` for HF ↔ Megatron checkpoints.

### VeOmni

**Location**: `verl/workers/engine/veomni/`
**Config**: `actor_rollout_ref.actor.strategy=veomni`

ByteDance's internal training engine. Provides additional optimizations for certain model architectures.

### MindSpeed (Ascend NPU)

**Location**: `verl/workers/engine/mindspeed/`
**Config**: `actor_rollout_ref.actor.strategy=mindspeed`

For Huawei Ascend NPU hardware. Requires `torch-npu` and Ascend drivers.

### TorchTitan

**Location**: `verl/workers/engine/torchtitan/`
**Config**: `actor_rollout_ref.actor.strategy=torchtitan`

Meta's TorchTitan training framework. Alternative for advanced distributed training scenarios.

### AutoModel

**Location**: `verl/workers/engine/automodel/`
Automatic engine selection based on model and hardware.

## Inference (Rollout) Backends

The rollout phase uses a separate inference backend to generate responses. The 3D-HybridEngine shares weights between the training engine and inference backend.

### vLLM

**Location**: `verl/workers/rollout/vllm_rollout/`
**Config**: `actor_rollout_ref.rollout.name=vllm`

High-throughput LLM serving engine.

**When to use**: Default choice for most setups. Best throughput.
**Version**: >= 0.8.2 (bundled in verl)
**Install**: `bash scripts/install_vllm.sh`

**Key options**:
```yaml
actor_rollout_ref.rollout:
  name: vllm
  tensor_model_parallel_size: 1
  gpu_memory_utilization: 0.5
  enforce_eager: false        # Use CUDA graph if false
  max_num_batched_tokens: 8192
  enable_chunked_prefill: false
```

### SGLang

**Location**: `verl/workers/rollout/sglang_rollout/`
**Config**: `actor_rollout_ref.rollout.name=sglang`

Efficient structured generation engine. Good for tool calling and constrained decoding.

**When to use**:
- Structured/constrained generation
- Tool-calling workloads
- When vLLM has compatibility issues

**Install**: `bash scripts/install_sglang.sh`

### HuggingFace Transformers

**Location**: `verl/workers/rollout/hf_rollout.py`
**Config**: `actor_rollout_ref.rollout.name=hf`

Native HuggingFace inference using `model.generate()`.

**When to use**:
- Debugging (most transparent, no optimization magic)
- Small-scale testing
- When other backends have compatibility issues

### TensorRT-LLM

**Location**: `verl/workers/rollout/trtllm_rollout/`
**Config**: `actor_rollout_ref.rollout.name=trtllm`

NVIDIA's optimized inference engine with TensorRT compilation.

**When to use**: NVIDIA GPUs with specific model support, maximum throughput.

## Backend Selection Guide

### For Training Engine

| Scenario | Recommended Engine |
|----------|-------------------|
| New project, < 70B model | **FSDP2** |
| Existing setup, stability | **FSDP** |
| > 70B model, multi-node | **Megatron-LM** |
| ByteDance internal | VeOmni |
| Ascend NPU | MindSpeed |

### For Inference Backend

| Scenario | Recommended Backend |
|----------|-------------------|
| General use, best throughput | **vLLM** |
| Structured generation, tool calling | **SGLang** |
| Debugging, testing | HuggingFace |
| NVIDIA optimized, specific models | TensorRT-LLM |

## Hardware Support Matrix

| Backend | CUDA (NVIDIA) | ROCm (AMD) | Ascend NPU |
|---------|--------------|------------|------------|
| FSDP | Yes | Yes | Yes |
| FSDP2 | Yes | Yes | - |
| Megatron-LM | Yes | - | - |
| VeOmni | Yes | - | - |
| MindSpeed | - | - | Yes |
| vLLM | Yes | Yes (limited) | - |
| SGLang | Yes | - | - |
| HF Transformers | Yes | Yes | Yes |
| TensorRT-LLM | Yes | - | - |
