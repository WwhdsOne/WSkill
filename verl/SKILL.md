---
name: verl
description: "Use this skill whenever working with the verl (Volcano Engine Reinforcement Learning) project — an open-source RL training library for LLMs by ByteDance Seed. Triggers: verl, RLHF, LLM post-training, RL training, PPO/GRPO/RLOO for language models, HybridFlow, HybridEngine, reward modeling, LLM fine-tuning with RL, tool-calling with RL, agent training, LLM reasoning improvement with RL. Also trigger when users ask about distributed LLM training with Ray, FSDP/Megatron for RL, vLLM/SGLang for generation in training loops, or anytime they mention wanting to do post-training / alignment of large language models."
version: 1.0.0
compatibility: Requires Python >= 3.10, access to verl codebase at project root
---

# verl Skill

verl (Volcano Engine Reinforcement Learning) is ByteDance Seed's open-source RL training library for large language models. It implements the EuroSys paper "HybridFlow: A Flexible and Efficient RLHF Framework". Use this skill whenever the user asks about verl code, verl training, verl configuration, or contributing to verl.

## Overview

verl provides a complete RL post-training pipeline for LLMs:
- **Training engines**: FSDP, FSDP2, Megatron-LM, VeOmni, MindSpeed (Ascend), TorchTitan
- **Inference backends**: vLLM, SGLang, HuggingFace Transformers, TensorRT-LLM
- **RL algorithms**: PPO, GRPO, GSPO, ReMax, REINFORCE++, RLOO, PRIME, DAPO, DrGRPO, SPPO
- **Key innovation**: 3D-HybridEngine — seamless memory sharing between training and generation
- **Scale**: Up to 671B models, hundreds of GPUs, expert parallelism
- **Advanced features**: Multi-turn agent loops, tool calling, vision-language models, async training

## Core Principles

1. **Read before modifying**: Always read relevant source files before suggesting changes. The verl codebase is large and interconnected.
2. **Use config files as reference**: Hydra YAML configs at `verl/trainer/config/` document all training parameters with comments.
3. **Check examples first**: The `examples/` directory has working shell scripts for every trainer/algorithm combination — use them as templates.
4. **Follow existing patterns**: verl has well-established patterns for workers, configs, and utilities. Match them when adding new code.

## When Working with verl

### Before Writing Any Code
1. **Read the relevant yaml config** — it documents every knob
2. **Check `examples/`** for a working script matching the user's scenario
3. **Read the relevant worker module** (under `verl/workers/`) to understand the data flow
4. **Check for tests** in `tests/` that exercise the code path

### Key Source Files by Task

| Task | Key Files |
|------|-----------|
| Understanding the training loop | `verl/trainer/main_ppo_sync.py`, `verl/trainer/ppo/ray_trainer.py` |
| Configuring training | `verl/trainer/config/ppo_trainer.yaml`, config subdirs |
| Adding a new RL algorithm | `verl/trainer/ppo/`, `verl/workers/reward_manager/` |
| Adding a training backend | `verl/workers/engine/` (base.py + new engine dir) |
| Adding an inference backend | `verl/workers/rollout/` (base.py + new rollout dir) |
| Adding a reward function | `verl/utils/reward_score/` or reward_manager |
| Multi-turn / tool calling | `verl/experimental/agent_loop/`, `verl/tools/` |
| Model checkpointing | `verl/checkpoint_engine/`, `verl/utils/checkpoint/` |
| Dataset handling | `verl/utils/dataset/` |
| Running an example | `examples/<trainer>/run_*.sh` |

### Understanding the Entry Points

verl has multiple entry points, know which to use:

- **`verl.trainer.main_ppo_sync`** — The current recommended PPO/GRPO trainer (use this)
- **`verl.trainer.main_ppo`** — Legacy PPO trainer (deprecated, will be removed)
- **`verl.trainer.sft_trainer`** — Supervised fine-tuning
- **`verl.trainer.main_eval`** — Offline evaluation
- **`verl.trainer.main_generation_server`** — Standalone generation server

### Training Flow

1. Ray cluster initializes, Resource Pool Manager allocates GPUs
2. Data loader provides prompts → Rollout workers generate responses (vLLM/SGLang)
3. Reward manager scores responses → Advantages computed
4. Actor updates policy (FSDP/Megatron/VeOmni), Critic updates value function (PPO only)
5. Reference policy computes KL divergence for regularization
6. Repeat

## Reference Files

The skill includes detailed reference documentation. Read them as needed:

- **[Architecture](./references/architecture.md)** — Deep dive: 3D-HybridEngine, worker roles, Resource Pool Manager, Agent Loop, TransferQueue, data flow
- **[Configuration](./references/config.md)** — Hydra config system, ppo_trainer.yaml structure, key parameters
- **[Algorithms](./references/algorithms.md)** — All supported RL algorithms, KL penalty variants, when to use each
- **[Backends](./references/backends.md)** — Training engines (FSDP/FSDP2/Megatron/VeOmni) and inference backends (vLLM/SGLang), when to choose each
- **[Development](./references/development.md)** — Code conventions, linting, pre-commit, CI/CD, test structure, contribution guide
- **[Examples](./references/examples.md)** — All example scripts, how to adapt them, common run templates
- **[Tools & Agents](./references/tools.md)** — Tool-calling framework, Agent Loop, OpenAI-compatible schemas, reward/teacher loops

## Common Tasks

### "I want to train model X with algorithm Y"

1. Check `examples/<y>_trainer/` for a matching script
2. Read the script to see the `--config-name` and Hydra overrides
3. Read the config YAML it references
4. Help the user adjust parameters (batch size, learning rate, etc.) for their hardware

### "I want to add a new reward function"

1. Look at `verl/utils/reward_score/` for existing reward scorers
2. Read `verl/workers/reward_manager/` (naive.py, batch.py, dapo.py, prime.py) for manager patterns
3. Implement the scoring function and register it
4. Update config and example scripts

### "I want to debug a training issue"

1. Check `scripts/diagnose.py` — the built-in diagnostic tool
2. Look at the Hydra config for the problematic component
3. Check Ray logs for the specific worker group
4. Verify environment setup (CUDA version, package versions)

### "I want to contribute to verl"

1. Read `AGENTS.md` and `CLAIMED.md` for agent instructions
2. Read `CONTRIBUTING.md` for contribution guidelines
3. Check `tests/special_sanity/` for code quality requirements
4. Run pre-commit hooks: `pre-commit run --all-files`
5. Use existing patterns in the same module

## Code Conventions (Quick Reference)

- **Linter**: ruff (v0.12.2+) — pycodestyle, pyflakes, pyupgrade, flake8-bugbear, isort
- **Type checker**: mypy (v1.17.0+)
- **Testing**: pytest with Ray-based distributed tests
- **Docstrings**: Required for public functions
- **License header**: Apache 2.0 header required in all source files
- **Import order**: standard library → third-party → verl internal
- **Config**: Use Hydra/OmegaConf, keep configs in YAML in the config/ directory
- **Error handling**: Raise descriptive exceptions, log with standard logging module

## Key Directories

```
verl/
├── verl/trainer/           # Training orches…
├── verl/workers/           # Worker impl…
│   ├── engine/             # Training engines…
│   ├── rollout/            # Inference backends…
│   └── reward_manager/     # Reward scoring…
├── verl/experimental/      # Agent loop, async pol…
├── verl/tools/             # Tool-calling framew…
├── verl/models/            # Model wrappers…
├── verl/utils/             # Utilities (40+ sub-modu…
├── examples/               # Run scripts for all scenarios
├── tests/                  # Test suite
├── docs/                   # Sphinx documentation
├── docker/                 # Docker images (CUDA/ROCm/Ascend)
└── scripts/                # Utility scripts (diagnostics, conversion)
```
