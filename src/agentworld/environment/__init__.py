"""Gymnasium-compatible environments for τ²-bench evaluation.

This module provides Gymnasium-compatible environments for training and
evaluating agents in dual-control scenarios, per τ²-bench requirements
(ADR-020.1).

The environments support:
- Standard Gymnasium interface (reset, step, render)
- Integration with stable-baselines3 for RL training
- HuggingFace ecosystem compatibility
- Dual-control scenarios with agent and user environments

Example:
    >>> import gymnasium as gym
    >>> env = gym.make("AgentWorld/DualControl-Agent-v0", task=task_def)
    >>> obs, info = env.reset()
    >>> for _ in range(100):
    ...     action = agent.predict(obs)
    ...     obs, reward, done, truncated, info = env.step(action)
    ...     if done:
    ...         break
"""

from agentworld.environment.gym_wrapper import (
    DualControlAgentEnv,
    DualControlUserEnv,
    register_environments,
)

__all__ = [
    "DualControlAgentEnv",
    "DualControlUserEnv",
    "register_environments",
]
