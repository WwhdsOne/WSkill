# verl Configuration System

verl uses **Hydra** (with OmegaConf) for hierarchical, composable configuration. Understanding the config system is essential for both using and developing verl.

## Configuration System Overview

### Entry Point

The main PPO trainer uses:
```bash
python -m verl.trainer.main_ppo_sync --config-path=config --config-name=ppo_trainer
```

This loads `verl/trainer/config/ppo_trainer.yaml` as the root config.

### Config Hierarchy

Configs are organized by component in `verl/trainer/config/`:

```
verl/trainer/config/
├── ppo_trainer.yaml           # Root config (primary)
├── ppo_megatron_trainer.yaml  # Megatron-LM variant
├── sft_trainer_engine.yaml    # SFT engine config
├── evaluation.yaml            # Evaluation config
├── actor/                     # Actor model configs
├── critic/                    # Critic model configs
├── data/                      # Dataset configs
├── model/                     # Model architecture configs
├── rollout/                   # Rollout/generation configs
├── reward/                    # Reward function configs
├── algorithm/                 # Algorithm configs (PPO, GRPO, etc.)
├── engine/                    # Engine backend configs
├── optim/                     # Optimizer configs
└── profiler/                  # Profiling configs
```

### ppo_trainer.yaml Structure

The root config groups all component configs together:

```yaml
# Top-level config groups
actor_rollout_ref:   # Actor, Rollout, and Reference policy (3D-HybridEngine)
  actor:
    # Model config, optimizer, FSDP/Megatron settings
  rollout:
    # Generation parameters (temperature, top_p, max_tokens)
    # Inference backend (vLLM/SGLang/HF)
  ref:
    # Reference policy config (KL penalty)

critic:              # Value function model (PPO only)
  # Model config, optimizer, engine settings

algorithm:           # RL algorithm parameters
  # PPO clip range, KL penalty type, gamma, lambda (GAE)

trainer:             # Trainer orchestration
  # Total steps, save/checkpoint frequency, logging

data:                # Dataset config
  # Training files, validation files, batch sizes

reward:              # Reward model config
  # Reward function type, reward model path

distillation:        # Knowledge distillation (optional)
  # Teacher model, distillation configs

global_profiler:     # Profiling options
  # nsys, torch profiler settings

transfer_queue:      # Async data streaming (optional)
  # ZMQ, Mooncake settings
```

### Override Syntax

Hydra supports command-line overrides of any config value:

```bash
python -m verl.trainer.main_ppo_sync \
    --config-path=config --config-name=ppo_trainer \
    data.train_files=/path/to/data.parquet \
    data.max_prompt_length=512 \
    data.max_response_length=2048 \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    trainer.total_epochs=10 \
    trainer.project_name=my-experiment \
    trainer.experiment_name=run-1
```

## Key Configuration Parameters

### Actor (`actor_rollout_ref.actor`)

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| `model.path` | HF model path or name | `Qwen/Qwen3-8B` |
| `model.use_fused_kernels` | Enable Liger kernels | `true` |
| `optim.lr` | Learning rate | `1e-6` |
| `optim.lr_warmup_steps` | LR warmup steps | `10` |
| `ppo_mini_batch_size` | PPO minibatch size | `256` |
| `ppo_epochs` | PPO epochs per rollout | `1` |
| `use_dynamic_bsz` | Dynamic batch sizing | `true` |
| `strategy` | Training backend | `fsdp`, `fsdp2`, `megatron` |
| `grad_clip` | Gradient clipping | `1.0` |
| `clip_ratio` | PPO clip ratio | `0.2` |
| `kl_loss_coef` | KL penalty coefficient | `0.001` |
| `entropy_coeff` | Entropy bonus coefficient | `0.0` |

### Rollout (`actor_rollout_ref.rollout`)

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| `name` | Inference backend | `vllm`, `sglang`, `hf` |
| `temperature` | Sampling temperature | `1.0` |
| `top_p` | Nucleus sampling | `1.0` |
| `top_k` | Top-k sampling | `-1` (disabled) |
| `n` | Responses per prompt | `4` (GRPO), `1` (PPO) |
| `max_model_len` | Max context length | model max |
| `gpu_memory_utilization` | GPU memory fraction | `0.5` |
| `tensor_model_parallel_size` | TP for inference | `1` |
| `enforce_eager` | Disable CUDA graph | `false` |

### Algorithm (`algorithm`)

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| `gamma` | Discount factor | `1.0` |
| `lam` | GAE lambda | `0.95` |
| `adv_estimator` | Advantage estimator | `gae`, `grpo`, `reinforce_plus_plus` |
| `kl_ctrl.kl_coef` | KL coefficient | `0.001` |
| `kl_ctrl.type` | KL control type | `fixed`, `adaptive` |
| `clip_ratio` | PPO clipping range | `0.2` |

### Trainer (`trainer`)

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| `total_epochs` | Total training epochs | depends on dataset size |
| `total_training_steps` | Total training steps | `null` (auto) |
| `save_freq` | Checkpoint save frequency (steps) | `-1` |
| `test_freq` | Validation frequency (steps) | `-1` |
| `logger` | Logging backend | `['console', 'wandb']` |
| `project_name` | wandb/SwanLab project name | `verl_examples` |
| `experiment_name` | Experiment run name | `qwen3_8b_grpo` |
| `nnodes` | Number of nodes | `1` |
| `n_gpus_per_node` | GPUs per node | `8` |

### Data (`data`)

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| `train_files` | Training data path | `/path/to/train.parquet` |
| `val_files` | Validation data path | `/path/to/test.parquet` |
| `train_batch_size` | Global batch size | `1024` |
| `max_prompt_length` | Max prompt tokens | `1024` |
| `max_response_length` | Max response tokens | `1024` |
| `filter_overlong_prompts` | Skip too-long prompts | `true` |
| `truncation` | Truncation side | `error`, `left`, `right` |

## Config Auto-Generation

verl can auto-generate comprehensive reference configs with all defaults:

```bash
# Generate full reference config for the FSDP-based trainer
bash scripts/generate_trainer_config.sh

# Output goes to:
# verl/trainer/config/_generated_ppo_trainer.yaml
# verl/trainer/config/_generated_ppo_megatron_trainer.yaml
```

These generated files show every single config option with default values — use them as reference when unsure about a parameter.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CUDA_VISIBLE_DEVICES` | GPU device selection |
| `NCCL_DEBUG` | NCCL debug level |
| `NCCL_SOCKET_IFNAME` | NCCL network interface |
| `RAY_DEDUP_LOGS` | Ray log deduplication (`0` to disable) |
| `VLLM_ATTENTION_BACKEND` | vLLM attention backend (`FLASH_ATTN`) |
| `VLLM_USE_V1` | Enable vLLM V1 engine (`1`) |

## Common Config Patterns

### Pattern 1: GRPO on 8 GPUs, 1 Node
```bash
python -m verl.trainer.main_ppo_sync \
    --config-path=examples/grpo_trainer/config \
    --config-name=ppo_trainer \
    data.train_files=$HOME/data/gsm8k/train.parquet \
    data.val_files=$HOME/data/gsm8k/test.parquet \
    data.train_batch_size=256 \
    data.max_prompt_length=512 \
    data.max_response_length=1024 \
    actor_rollout_ref.model.path=Qwen/Qwen3-8B \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.ppo_mini_batch_size=128 \
    actor_rollout_ref.actor.ppo_epochs=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.temperature=1.0 \
    actor_rollout_ref.rollout.n=8 \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.5 \
    trainer.total_epochs=5 \
    trainer.project_name=verl_grpo_examples \
    trainer.experiment_name=qwen3_8b_grpo \
    trainer.nnodes=1 \
    trainer.n_gpus_per_node=8
```

### Pattern 2: FSDP2 (recommended for new setups)
```bash
actor_rollout_ref.actor.strategy=fsdp2 \
actor_rollout_ref.ref.strategy=fsdp2 \
actor_rollout_ref.actor.fsdp_config.param_offload=True \
actor_rollout_ref.actor.fsdp_config.optimizer_offload=True
```

### Pattern 3: LoRA fine-tuning
```bash
actor_rollout_ref.actor.peft_config=lora \
actor_rollout_ref.actor.peft.lora.r=8 \
actor_rollout_ref.actor.peft.lora.alpha=16 \
actor_rollout_ref.actor.peft.lora.target_modules='["q_proj","v_proj"]'
```
