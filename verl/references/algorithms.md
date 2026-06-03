# Supported RL Algorithms

verl implements a comprehensive suite of RL algorithms for LLM post-training. All algorithms use the same infrastructure (HybridEngine, rollout backends, reward managers) — they differ in how advantages are computed and how the policy is updated.

## Algorithm Comparison

| Algorithm | Needs Critic | Needs Reference | Uses GAE | Best For |
|-----------|-------------|-----------------|----------|----------|
| PPO | Yes | Yes | Yes | General RLHF, strong baselines |
| GRPO | No | Yes | No | Math/reasoning tasks, simpler setup |
| GSPO | No | Yes | No | Sequence-level optimization |
| ReMax | No | Yes | No | Variance reduction |
| REINFORCE++ | No | No | No | Simplest possible RL (no KL) |
| RLOO | No | No | No | Low-variance simple RL |
| PRIME | No | No | No | Process reward with implicit process |
| DAPO | No | Yes | No | Decoupled clip & dynamic sampling |
| DrGRPO | No | Yes | No | GRPO with kl divergence control |
| SPPO | No | Yes | No | Self-play preference optimization |

## PPO (Proximal Policy Optimization)

The original algorithm from Schulman et al. Most general and well-tested.

**Components**: Actor + Critic + Reference Policy
**Training loop**:
1. Rollout: Generate responses from current policy
2. Compute rewards from reward model
3. Compute advantages using GAE (requires critic's value estimates)
4. PPO clipped objective: L = min(ratio * A, clip(ratio, 1-ε, 1+ε) * A)
5. KL penalty to prevent policy drift: L_total = L_ppo - β * KL(π_new || π_ref)
6. Update actor and critic

**Config**: `--config-name=ppo_trainer`
**Example**: `examples/ppo_trainer/`

## GRPO (Group Relative Policy Optimization)

Used by DeepSeek-R1. No critic needed — uses group-based relative scoring.

**Components**: Actor + Reference Policy (no Critic)
**Training loop**:
1. Rollout: Generate N responses per prompt (N=4-16)
2. Compute raw rewards for each response
3. Standardize rewards within each group: z = (r - mean) / std
4. Use standardized rewards as advantages directly (no GAE)
5. PPO clipped objective with group-relative advantages
6. KL penalty from reference policy

**Why GRPO over PPO**: Simpler (no critic), often better for reasoning/math tasks where reward signals are clear.

**Config**: `--config-name=ppo_trainer` with `algorithm.adv_estimator=grpo`
**Example**: `examples/grpo_trainer/`

## GSPO (Group-level Sequence Policy Optimization)

Sequence-level variant of GRPO. Optimizes at the sequence level rather than token level.

## ReMax (Reverse Maximum)

Variance reduction technique. Uses the best reward in a batch as baseline to reduce variance in REINFORCE gradient estimates.

## REINFORCE++

Improved REINFORCE with several modern techniques (value clipping, loss clipping). Simplest algorithm — no critic, no reference, just policy gradient on rewards.

## RLOO (REINFORCE Leave-One-Out)

**Components**: Actor only
**Training loop**:
- Generate K responses per prompt
- Advantage = reward_i - mean(rewards of other K-1 responses)
- This is a leave-one-out baseline for variance reduction

**When to use**: Simpler than PPO, doesn't need value function. Good for scenarios where reward signals are clean.

## PRIME (Process Reinforcement with Implicit Process)

Uses process-level rewards derived from model's own generation process. Special reward manager (`PRIMERewardManager`) extracts implicit signals.

## DAPO (Decoupled Clip and Dynamic Sampling Policy Optimization)

Key innovations:
- **Decoupled clip**: Separate clipping for upper and lower bounds
- **Dynamic sampling**: Adjusts number of samples based on reward variance
- Uses `DAPORewardManager`

## DrGRPO

GRPO variant that uses learned KL-divergence control. Similar to GRPO but with adaptive KL coefficient based on KL-divergence between training and reference distributions.

## SPPO (Self-Play Preference Optimization)

Self-play approach where the model generates its own preference data:
1. Generate multiple responses per prompt
2. Rank responses by reward
3. Use winning/losing pairs for preference optimization
4. Iterate — model improves by playing against itself

## KL Penalty Variants

All algorithms that use a reference policy support multiple KL penalty types:

### Fixed KL (`kl_ctrl.type=fixed`)
- Constant KL coefficient throughout training
- Simple and predictable

### Adaptive KL (`kl_ctrl.type=adaptive`)
- KL coefficient adjusts based on target divergence
- Prevents too much policy drift
- Parameters: `kl_ctrl.kl_coef` (initial), `kl_ctrl.target_kl`, `kl_ctrl.horizon`

### KL Penalty Methods

| Method | Description | Config |
|--------|-------------|--------|
| KL Cov | Covariance-based KL | `kl_loss_type=KL_Cov` |
| Clip Cov | Clipped covariance | `kl_loss_type=Clip_Cov` |
| Entropy | Entropy regularization | `entropy_coeff` |

## Advantage Estimators

| Estimator | Description | Config |
|-----------|-------------|--------|
| GAE | Generalized Advantage Estimation (needs Critic) | `adv_estimator=gae` |
| GRPO | Group-relative (standardized rewards) | `adv_estimator=grpo` |
| REINFORCE++ | Improved REINFORCE style | `adv_estimator=reinforce_plus_plus` |

## Choosing an Algorithm

Start simple, add complexity only if needed:

1. **Start with GRPO** for math/coding/reasoning tasks with objective reward functions
   - Simple, no critic needed, well-tested for DeepSeek-style training
2. **Use PPO** for general RLHF where you need a value function for credit assignment
   - More stable on long trajectories, better for subjective rewards
3. **Try RLOO/REINFORCE++** for minimal setup
   - Good for quick experiments, fewer moving parts
4. **Consider PRIME/DAPO** for specialized reward scenarios
   - PRIME for implicit process rewards, DAPO for dynamic batch sizing
