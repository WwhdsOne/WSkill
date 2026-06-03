# verl Architecture

## High-Level Architecture

verl implements the HybridFlow programming model from the EuroSys paper. The key insight is **separation of control flow from computation**, enabling flexible composition of distributed RL components.

### Training Pipeline Flow

```
                    ┌────────────────────────┐
                    │   Ray Cluster           │
                    │  (distributed runtime)  │
                    └────────┬───────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ DataLoader │  │ Resource   │  │ Trainer    │
     │ (prompts)  │  │ Pool Mgr   │  │ (orchestr) │
     └─────┬──────┘  │ (GPU alloc)│  └─────┬──────┘
           │         └────────────┘        │
           ▼                               ▼
  ┌────────────────────┐          ┌──────────────────┐
  │ Rollout Workers    │          │ Actor Workers     │
  │ (vLLM/SGLang/HF)   │◄────────►│ (FSDP/Mega/V OmnI)│
  │ Generate responses  │  shares  │ Update policy      │
  └────────┬───────────┘  model   └────────┬───────────┘
           │                               │
           ▼                               ▼
  ┌────────────────────┐          ┌──────────────────┐
  │ Reward Manager     │          │ Critic Workers    │
  │ Score responses    │──────────►│ (PPO only)        │
  └────────────────────┘          └──────────────────┘
           │
           ▼
  ┌────────────────────┐
  │ Reference Policy   │
  │ KL divergence      │
  └────────────────────┘
```

### Data Flow per Step

1. **Prompt ingestion**: Dataset → DataLoader → prompt tokens
2. **Generation (Rollout)**: Prompt → Rollout Worker (vLLM/SGLang) → response tokens + log probs
3. **Reward computation**: (prompt, response) → Reward Manager → scalar reward
4. **Advantage computation**: rewards → GAE (Generalized Advantage Estimation) → advantages
5. **Policy update**: (prompts, responses, advantages) → Actor Worker → updated policy weights
6. **Value update** (PPO only): (prompts, responses, returns) → Critic Worker → updated value function
7. **KL penalty** (optional): response log probs → Reference Policy → KL divergence

## 3D-HybridEngine

The key innovation that enables efficient RL training at scale. In standard implementations, training and generation have separate model copies in GPU memory, wasting resources. The 3D-HybridEngine solves this by:

### 3 Dimensions of Hybrid
1. **Model weight sharing**: Actor (training) and Rollout (generation) share the same model weights
2. **Memory optimization**: Weights reside in one location, eliminating redundant copies
3. **Communication reduction**: No need to transfer weights between training and generation phases

### How it works
- During rollouts, the model is configured for inference (no gradients, KV cache optimization)
- During training, the model switches to training mode (gradients enabled, optimizer state)
- The transition is fast because weights stay in place
- Supported by both FSDP and Megatron-LM backends

## Worker Architecture

### Actor Worker (`verl/workers/engine/`)
- **Role**: Runs the policy model, computes PPO loss, updates weights
- **Backends**: FSDP (base.py + fsdp/), FSDP2, Megatron-LM (megatron/), VeOmni (veomni/), MindSpeed (mindspeed/), TorchTitan (torchtitan/)
- **Key methods**: `update_policy()`, `compute_log_prob()`

### Rollout Worker (`verl/workers/rollout/`)
- **Role**: Generates responses from prompts during rollout phase
- **Backends**: vLLM (vllm_rollout/), SGLang (sglang_rollout/), HuggingFace (hf_rollout.py), TensorRT-LLM (trtllm_rollout/)
- **Key methods**: `generate_sequences()`, gets prompts, returns token sequences + log probs

### Reward Manager (`verl/workers/reward_manager/`)
- **Role**: Computes reward signals for generated responses
- **Types**:
  - `NaiveRewardManager`: Simple pass-through to reward functions
  - `BatchRewardManager`: Batched reward computation
  - `DAPORewardManager`: For DAPO algorithm
  - `PRIMERewardManager`: For PRIME algorithm
- **Registry**: `verl/workers/reward_manager/registry.py` manages registration

### Critic Worker (PPO only)
- **Role**: Estimates value functions for advantage computation
- Uses the same engine backends as Actor
- Optional — not needed for GRPO, RLOO, etc.

### Reference Policy Worker
- **Role**: Computes KL divergence for regularization
- Typically uses HuggingFace inference
- Can also use vLLM/SGLang for efficiency

## Resource Pool Manager (`verl/single_controller/ray/`)

The RPC-based distributed controller that maps logical worker groups to physical GPU resources:

- **RayWorkerGroup**: A group of Ray actors forming a worker group
- **ResourcePoolManager**: Allocates GPUs across nodes to worker groups
- **Deployment modes**: Colocate (actor+rollout same GPUs) or separate (different GPUs)
- **Scaling**: Supports data parallelism, tensor parallelism, pipeline parallelism, expert parallelism

## Agent Loop (`verl/experimental/agent_loop/`)

Manages multi-turn interactions between the model and tools/environment:

- **AgentLoopManager**: Orchestrates agent loops in parallel
- **SingleTurnAgentLoop**: Standard single-turn rollout
- **ToolAgentLoop**: Multi-turn with tool calling (function calls, code execution, web search)
- **ToolParser**: Parses tool call syntax from model outputs (OpenAI-compatible schemas)

## TransferQueue (`verl/experimental/transfer_queue/`)

Asynchronous streaming data management between rollout and training:
- **ZMQ-based**: ZeroMQ for reliable message passing
- **Mooncake RDMA**: RDMA-based for ultra-low latency (ByteDance internal)
- **Benefits**: Decouples rollout generation from training, enables continuous data streaming

## Experimental Features

| Feature | Location | Status |
|---------|----------|--------|
| Agent Loop (multi-turn) | `verl/experimental/agent_loop/` | Active development |
| Reward Loop (async) | `verl/experimental/reward_loop/` | Experimental |
| Teacher Loop | `verl/experimental/teacher_loop/` | Experimental |
| Fully Async Policy | `verl/experimental/fully_async_policy/` | Experimental |
| One-Step Off-Policy | `verl/experimental/one_step_off_policy/` | Experimental |
| Separation (compute/control) | `verl/experimental/separation/` | Experimental |
| Knowledge Distillation | `verl/trainer/distillation/` | Integrated |
| Vision-Language (VLM) | `verl/models/` | Integrated (Qwen2.5-VL, Kimi-VL, GLM-4V) |

## Model Checkpointing

- **Engine**: `verl/checkpoint_engine/` supports local filesystem and HDFS
- **Utilities**: `verl/utils/checkpoint/` for save/load/resume
- **Model merging**: `scripts/legacy_model_merger.py` and `scripts/megatron_merge_lora.py`
- **Format conversion**: `scripts/converter_hf_to_mcore.py` (HF to Megatron-Core)
- **LoRA**: `verl/model_merger/` supports LoRA weight merging

## Scaling Dimensions

verl supports multiple parallelism strategies simultaneously:

1. **Data Parallelism**: Split batch across GPUs
2. **Tensor Parallelism**: Split model layers across GPUs (Megatron-style)
3. **Pipeline Parallelism**: Split model stages across GPUs
4. **Sequence Parallelism**: DeepSpeed Ulysses for long sequences
5. **Expert Parallelism**: For Mixture-of-Experts models (DeepSeek-V3 671B)
6. **FSDP**: Shard parameters, gradients, optimizer states across GPUs

These can be combined — e.g., FSDP + Tensor Parallelism + Expert Parallelism for extremely large models.
