# Development Guide

## Prerequisites

- **Python**: >= 3.10
- **CUDA**: 12.4+ (for GPU training)
- **GPU**: NVIDIA (any), AMD (ROCm), or Ascend NPU

## Development Setup

### Install verl

```bash
# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Editable install (recommended for development)
cd /path/to/verl
pip install -e .
pip install -r requirements.txt

# Optional: NPU support
pip install -r requirements-npu.txt

# Test dependencies
pip install -r requirements-test.txt
```

### Development Tools

```bash
# Pre-commit hooks (linting, formatting, checks)
pre-commit install
pre-commit run --all-files

# Run specific linters
ruff check .
ruff format --check .
mypy .
```

## Code Quality

### Linting (Ruff)

```toml
# pyproject.toml
[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "I",    # isort
]
```

### Type Checking (Mypy)

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.10"
strict = false
```

### Pre-commit Hooks

See `.pre-commit-config.yaml` for the full list. Key hooks:

| Hook | Purpose |
|------|---------|
| `check-license-header` | Apache 2.0 header required |
| `check-docstring` | Docstring coverage check |
| `check-filename` | Naming convention enforcement |
| `check-config-generation` | Ensures generated configs are up-to-date |
| `check-structure` | Validates project structure |
| `check-test-name` | Test naming conventions |
| `ruff` | Linting and formatting |
| `mypy` | Static type checking |

### Running pre-commit selectively

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run check-license-header --all-files
```

## Testing

### Test Structure

```
tests/
├── special_e2e/          # End-to-end training tests
├── special_sanity/       # Code quality checks (license, naming)
├── special_standalone/   # Standalone isolated tests
├── trainer/              # Trainer-specific tests
├── workers/              # Worker tests
│   ├── engine/           # Engine backend tests
│   ├── rollout/          # Rollout backend tests
│   └── reward_manager/   # Reward manager tests
├── models/               # Model tests
├── tools/                # Tool framework tests
├── experimental/         # Experimental feature tests
├── utils/                # Utility tests
└── single_controller/    # Controller tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/workers/rollout/test_vllm_rollout.py

# Run with GPU filtering
pytest -m "gpu"

# Run E2E tests (requires GPU)
pytest tests/special_e2e/
```

### Test Conventions

- Test files: `test_<module>.py`
- Test functions: `test_<functionality>`
- Use `pytest.fixture` for shared setup
- Use `pytest.mark.skipif` for hardware-dependent tests
- Use Ray local mode for lightweight tests: `ray.init(local_mode=True)`

## Project Structure Conventions

### Adding New Code

Follow the existing patterns in the module you're extending:

**Adding a new training engine backend**:
```
verl/workers/engine/new_backend/
├── __init__.py
├── engine.py          # Main engine implementation (inherit from base.py)
└── config.py          # Backend-specific config
```

**Adding a new rollout backend**:
```
verl/workers/rollout/new_rollout/
├── __init__.py
├── rollout.py         # Main rollout implementation (inherit from base.py)
└── config.py          # Backend-specific config
```

**Adding a new reward manager**:
```
verl/workers/reward_manager/
├── new_manager.py     # New implementation
└── registry.py        # Register the new manager
```

**Adding a new RL algorithm**:
```
verl/trainer/ppo/
└── new_algorithm.py   # Algorithm-specific loss, advantage computation
verl/workers/reward_manager/
└── new_manager.py     # If algorithm needs special reward handling
```

### Config Convention

- Create new config files in `verl/trainer/config/` under the appropriate subdirectory
- Use structured configs (dataclasses) for type safety
- Document all parameters with comments
- Regenerate reference configs after changes:
  ```bash
  bash scripts/generate_trainer_config.sh
  ```

### Import Order

```python
# Standard library
import os
import json
from typing import Optional

# Third-party
import torch
import ray
from transformers import AutoModel

# verl internal
from verl.utils.config import validate_config
from verl.workers.engine.base import BaseEngine
```

## CI/CD

### GitHub Actions

50+ workflow files in `.github/workflows/`:

| Category | Examples |
|----------|----------|
| GPU E2E Tests | `gpu_unit_tests.yml`, `e2e_*.yml` |
| CPU Tests | `cpu_unit_tests.yml` |
| vLLM Tests | `vllm_tests.yml` |
| SGLang Tests | `sglang_tests.yml` |
| NPU Tests | `ascend_tests.yml` |
| Docker Builds | `docker_build_*.yml` |
| Pre-commit | `pre_commit.yml` |
| Nightly | `nightly_tests.yml` |

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following code conventions
4. Run pre-commit hooks
5. Add tests for new functionality
6. Run existing tests to verify no regressions
7. Submit a PR using the PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
8. Code owners are defined in `.github/CODEOWNERS`

## Key Utility Modules

### `verl/utils/config.py`
Config validation and processing utilities.

### `verl/utils/device.py`
Auto-detection of CUDA/NPU devices.

### `verl/utils/distributed.py`
Distributed training utilities (init_process_group, etc.).

### `verl/utils/tracking.py`
Experiment tracking with multiple backends: wandb, swanlab, mlflow, tensorboard.

### `verl/utils/tokenizer.py`
Tokenizer loading with fallback for various model formats.

### `verl/utils/hf_processor.py`
HuggingFace processor loading for vision-language models.

### `verl/utils/dataset/`
RL dataset classes and collate functions.

### `verl/utils/checkpoint/`
Checkpoint saving/loading/resume utilities.

### `verl/utils/reward_score/`
Reward scoring functions for math, code, and general tasks.

### `verl/utils/profiler/`
Profiling with nsys and torch profiler.

## Common Development Pitfalls

1. **Forgetting to regen configs**: After changing config dataclasses, run `scripts/generate_trainer_config.sh`
2. **Ray serialization**: Ensure all data passed between Ray actors is serializable (use `dill` if needed)
3. **GPU memory leaks**: Clean up vLLM/SGLang processes between tests
4. **NCCL timeouts**: Increase timeout for large model distributed training
5. **PyTorch version mismatch**: verl requires specific PyTorch versions matching CUDA
6. **Import order breaking pre-commit**: ruff enforces isort — run `pre-commit run ruff` before committing
