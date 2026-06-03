# Example Scripts & Training Runs

verl provides working example scripts for every supported algorithm and hardware configuration. These scripts are the best starting point for any training task.

## Example Directory Structure

```
examples/
├── grpo_trainer/          # GRPO examples
│   ├── run_qwen3_8b_fsdp.sh
│   ├── run_qwen3_8b_fsdp2.sh
│   ├── run_deepseek_v3_671b_megatron.sh
│   ├── run_deepseek_v3_671b_fsdp.sh
│   ├── run_qwen2.5_vl_7b_fsdp.sh       # Vision-language
│   ├── run_kimi_vl_7b_fsdp.sh
│   ├── run_qwen3_moe_30b_megatron.sh   # MoE
│   └── config/                          # Custom configs
├── ppo_trainer/           # PPO examples
│   ├── run_qwen3_8b_fsdp.sh
│   ├── run_deepseek_v3_671b_megatron.sh
│   └── config/
├── remax_trainer/         # ReMax examples
├── rloo_trainer/          # RLOO examples
├── sft/                   # Supervised Fine-Tuning
├── distillation/          # Knowledge distillation
├── tuning/
│   └── lora/              # LoRA fine-tuning examples
└── tutorial/
    └── agent_loop_get_started/  # Agent loop tutorial
```

## Common Training Templates

### Template 1: Basic GRPO (FSDP, 1 node, 8 GPUs)

```bash
python -m verl.trainer.main_ppo_sync \
    algorithm.adv_estimator=grpo \
    data.train_files=$HOME/data/train.parquet \
    data.val_files=$HOME/data/test.parquet \
    data.train_batch_size=256 \
    data.max_prompt_length=512 \
    data.max_response_length=1024 \
    actor_rollout_ref.model.path=Qwen/Qwen3-8B \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.actor.ppo_mini_batch_size=128 \
    actor_rollout_ref.actor.ppo_epochs=1 \
    actor_rollout_ref.actor.use_dynamic_bsz=True \
    actor_rollout_ref.actor.ppo_max_token_len_per_gpu=24000 \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef=0.001 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.actor.fsdp_config.param_offload=False \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=False \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
    actor_rollout_ref.rollout.n=8 \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    algorithm.use_kl_in_reward=False \
    trainer.critic_warmup=0 \
    trainer.logger='["console","wandb"]' \
    trainer.project_name=verl_grpo_example \
    trainer.experiment_name=qwen3_8b_function_rm \
    trainer.n_gpus_per_node=8 \
    trainer.nnodes=1 \
    trainer.save_freq=-1 \
    trainer.test_freq=5 \
    trainer.total_epochs=15 \
    "$@"
```

### Template 2: PPO (FSDP, 1 node, 8 GPUs)

```bash
python -m verl.trainer.main_ppo_sync \
    data.train_files=$HOME/data/train.parquet \
    data.val_files=$HOME/data/test.parquet \
    data.train_batch_size=256 \
    data.max_prompt_length=512 \
    data.max_response_length=1024 \
    actor_rollout_ref.model.path=Qwen/Qwen3-8B \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.actor.ppo_mini_batch_size=128 \
    actor_rollout_ref.actor.ppo_epochs=1 \
    actor_rollout_ref.actor.use_dynamic_bsz=True \
    actor_rollout_ref.actor.ppo_max_token_len_per_gpu=24000 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
    actor_rollout_ref.rollout.n=1 \
    critic.optim.lr=1e-5 \
    critic.model.use_remove_padding=True \
    critic.model.path=Qwen/Qwen3-8B \
    critic.ppo_max_token_len_per_gpu=98304 \
    algorithm.adv_estimator=gae \
    algorithm.kl_ctrl.kl_coef=0.001 \
    trainer.critic_warmup=0 \
    trainer.logger='["console","wandb"]' \
    trainer.project_name=verl_ppo_example \
    trainer.experiment_name=qwen3_8b_ppo \
    trainer.n_gpus_per_node=8 \
    trainer.nnodes=1 \
    trainer.save_freq=-1 \
    trainer.test_freq=5 \
    trainer.total_epochs=15 \
    "$@"
```

### Template 3: Large Model (DeepSeek-V3 671B, Megatron-LM)

```bash
python -m verl.trainer.main_ppo_sync \
    algorithm.adv_estimator=grpo \
    data.train_files=$HOME/data/train.parquet \
    data.val_files=$HOME/data/test.parquet \
    data.train_batch_size=1024 \
    data.max_prompt_length=512 \
    data.max_response_length=4096 \
    actor_rollout_ref.model.path=deepseek-ai/DeepSeek-V3 \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.strategy=megatron \
    actor_rollout_ref.actor.megatron.tensor_model_parallel_size=8 \
    actor_rollout_ref.actor.megatron.pipeline_model_parallel_size=4 \
    actor_rollout_ref.actor.megatron.expert_model_parallel_size=8 \
    actor_rollout_ref.actor.megatron.sequence_parallel=true \
    actor_rollout_ref.rollout.name=vllm \
    actor_rollout_ref.rollout.tensor_model_parallel_size=8 \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.6 \
    actor_rollout_ref.rollout.n=8 \
    actor_rollout_ref.ref.strategy=megatron \
    trainer.logger='["console","wandb"]' \
    trainer.project_name=verl_grpo_deepseek \
    trainer.experiment_name=deepseek_v3_671b_megatron \
    trainer.n_gpus_per_node=8 \
    trainer.nnodes=32 \
    trainer.total_training_steps=1000 \
    "$@"
```

### Template 4: LoRA Fine-Tuning

```bash
python -m verl.trainer.main_ppo_sync \
    algorithm.adv_estimator=grpo \
    data.train_files=$HOME/data/train.parquet \
    data.val_files=$HOME/data/test.parquet \
    actor_rollout_ref.model.path=Qwen/Qwen3-8B \
    actor_rollout_ref.actor.optim.lr=1e-6 \
    actor_rollout_ref.actor.peft_config=lora \
    actor_rollout_ref.actor.peft.lora.r=8 \
    actor_rollout_ref.actor.peft.lora.alpha=16 \
    # ... (other parameters same as Template 1)
```

### Template 5: Vision-Language Model Training

```bash
python -m verl.trainer.main_ppo_sync \
    algorithm.adv_estimator=grpo \
    data.train_files=$HOME/data/multimodal_train.parquet \
    data.val_files=$HOME/data/multimodal_test.parquet \
    data.image_key=images \
    data.max_prompt_length=2048 \
    data.max_response_length=1024 \
    actor_rollout_ref.model.path=Qwen/Qwen2.5-VL-7B-Instruct \
    actor_rollout_ref.model.trust_remote_code=True \
    # ... (other parameters same as Template 1)
```

## Data Format

verl expects data in **Parquet** format with specific columns:

### RLHF/RM Data Format

| Column | Type | Description |
|--------|------|-------------|
| `prompt` | list[dict] | Chat template messages (conversation format) |
| `data_source` | str | Source identifier (e.g., "gsm8k", "math") |
| `ability` | str (optional) | Task category (e.g., "math", "code") |
| `reward_model` | dict (optional) | Ground truth for reward computation |
| `extra_info` | dict (optional) | Additional metadata |

### SFT Data Format

| Column | Type | Description |
|--------|------|-------------|
| `messages` | list[dict] | Full conversation messages |
| `images` | bytes (optional) | Image data for VLMs |
| `videos` | bytes (optional) | Video data for VLMs |

## Reward Functions

verl provides built-in reward functions in `verl/utils/reward_score/`:

| Function | Task | File |
|----------|------|------|
| GSM8K | Math word problems | `gsm8k.py` |
| MATH | Competition math | `math.py` |
| HumanEval | Code generation | `humaneval.py` |
| MBPP | Code generation | `mbpp.py` |
| Custom | Generic regex-based | Various |

### Using a Custom Reward Function

```python
# my_reward.py
def compute_reward(prompt: str, response: str, ground_truth=None, **kwargs):
    # Your reward logic here
    return score

# Register in config:
# reward.reward_fn = custom
# reward.reward_fn_config.custom_file = /path/to/my_reward.py
```

## Example Script Patterns

### Multi-Node Training

```bash
# On each node, run the same command
# Ray handles the cluster setup
export RAY_ADDRESS="auto"  # Connect to existing Ray cluster
bash examples/grpo_trainer/run_qwen3_8b_fsdp.sh
```

### Hot-Swapping Rollout Backend

```bash
# Use SGLang instead of vLLM
python -m verl.trainer.main_ppo_sync \
    ... \
    actor_rollout_ref.rollout.name=sglang \
    "$@"
```

### Debug Mode (Single GPU, HuggingFace Only)

```bash
python -m verl.trainer.main_ppo_sync \
    data.train_batch_size=4 \
    data.max_prompt_length=256 \
    data.max_response_length=256 \
    actor_rollout_ref.actor.ppo_mini_batch_size=2 \
    actor_rollout_ref.actor.ppo_epochs=1 \
    actor_rollout_ref.rollout.name=hf \
    actor_rollout_ref.rollout.n=1 \
    trainer.n_gpus_per_node=1 \
    trainer.nnodes=1 \
    trainer.total_epochs=1 \
    "$@"
```
