"""Gymnasium-compatible wrapper for τ²-bench dual-control environments.

This module provides Gymnasium-compatible environments for training and
evaluating agents in dual-control scenarios, implementing the interface
required by τ²-bench (ADR-020.1).

The environments support:
- Standard Gymnasium interface (reset, step, render)
- Both agent-side and user-side environments
- State verification against goal states
- Reward computation based on task completion
- Integration with RL frameworks (stable-baselines3, etc.)

Example:
    >>> from agentworld.environment import DualControlAgentEnv
    >>> from agentworld.tasks.dual_control import DualControlTaskDefinition
    >>>
    >>> task = DualControlTaskDefinition(...)
    >>> env = DualControlAgentEnv(task=task)
    >>> obs, info = env.reset()
    >>> action = "Please toggle your mobile data on"
    >>> obs, reward, done, truncated, info = env.step(action)
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

try:
    import gymnasium as gym
    from gymnasium import spaces
    HAS_GYMNASIUM = True
except ImportError:
    HAS_GYMNASIUM = False
    # Create stub classes for type checking when gymnasium not installed
    class gym:
        class Env:
            pass
    class spaces:
        @staticmethod
        def Dict(*args, **kwargs):
            return None
        @staticmethod
        def Text(*args, **kwargs):
            return None
        @staticmethod
        def Discrete(*args, **kwargs):
            return None
        @staticmethod
        def Box(*args, **kwargs):
            return None

if TYPE_CHECKING:
    from agentworld.tasks.dual_control import DualControlTaskDefinition
    from agentworld.agents.agent import Agent

logger = logging.getLogger(__name__)


@dataclass
class EnvState:
    """Internal environment state.

    Attributes:
        app_states: Current state of all apps
        conversation: List of conversation turns
        step_count: Number of steps taken
        terminated: Whether the episode is done
        truncated: Whether the episode was truncated
    """
    app_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    conversation: list[dict[str, str]] = field(default_factory=list)
    step_count: int = 0
    terminated: bool = False
    truncated: bool = False


class DualControlAgentEnv(gym.Env if HAS_GYMNASIUM else object):
    """Gymnasium environment for the service agent in dual-control scenarios.

    The agent (service_agent role) must guide the user (customer role) to
    complete tasks by providing instructions. The agent has access to backend
    apps while the user has access to device apps.

    Observation Space:
        Dict containing:
        - conversation: Text of recent conversation history
        - backend_state: Dict of backend app states visible to agent
        - step: Current step number

    Action Space:
        Text - natural language response to user

    Rewards:
        - +1.0 for achieving goal state
        - -0.01 per step (encourages efficiency)
        - +0.1 for successful coordination handoff
        - -0.1 for user confusion detected

    Example:
        >>> env = DualControlAgentEnv(task=task, user_simulator=user_agent)
        >>> obs, info = env.reset()
        >>> while True:
        ...     action = agent_model.predict(obs)
        ...     obs, reward, done, truncated, info = env.step(action)
        ...     if done or truncated:
        ...         break
    """

    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(
        self,
        task: "DualControlTaskDefinition",
        user_simulator: "Agent | None" = None,
        max_steps: int = 50,
        render_mode: str | None = None,
    ):
        """Initialize the agent environment.

        Args:
            task: Dual-control task definition with initial/goal states
            user_simulator: LLM-based user simulator agent (optional)
            max_steps: Maximum steps before truncation
            render_mode: How to render the environment ("human" or "ansi")
        """
        super().__init__()

        if not HAS_GYMNASIUM:
            raise ImportError(
                "gymnasium is required for DualControlAgentEnv. "
                "Install with: pip install gymnasium"
            )

        self.task = task
        self.user_simulator = user_simulator
        self.max_steps = max_steps
        self.render_mode = render_mode

        # Initialize spaces
        self.observation_space = spaces.Dict({
            "conversation": spaces.Text(max_length=50000),
            "backend_state": spaces.Text(max_length=10000),  # JSON string
            "step": spaces.Discrete(max_steps + 1),
        })

        self.action_space = spaces.Text(max_length=5000)

        # Internal state
        self._state: EnvState | None = None
        self._agent_apps: dict[str, Any] = {}
        self._user_apps: dict[str, Any] = {}

    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Reset the environment to initial state.

        Args:
            seed: Random seed for reproducibility
            options: Additional options (unused)

        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)

        # Initialize state from task
        self._state = EnvState(
            app_states=copy.deepcopy(self.task.initial_state),
            conversation=[],
            step_count=0,
            terminated=False,
            truncated=False,
        )

        # Initialize apps (would need actual app instances in full impl)
        self._agent_apps = {}
        self._user_apps = {}

        for app_config in self.task.agent_config.apps:
            app_id = app_config.get("id", "")
            if app_id:
                self._agent_apps[app_id] = {
                    "config": app_config,
                    "state": self._state.app_states.get(app_id, {}),
                }

        for app_config in self.task.user_config.apps:
            app_id = app_config.get("id", "")
            if app_id:
                self._user_apps[app_id] = {
                    "config": app_config,
                    "state": self._state.app_states.get(app_id, {}),
                }

        # Add initial user message if specified
        if self.task.user_config.initial_message:
            self._state.conversation.append({
                "role": "user",
                "content": self.task.user_config.initial_message,
            })

        observation = self._get_observation()
        info = {
            "task_id": self.task.task_id,
            "agent_apps": list(self._agent_apps.keys()),
            "user_apps": list(self._user_apps.keys()),
        }

        return observation, info

    def step(
        self,
        action: str,
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """Execute agent action and get user response.

        Args:
            action: Agent's natural language response/instruction

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        if self._state.terminated or self._state.truncated:
            raise RuntimeError("Episode already ended. Call reset() first.")

        self._state.step_count += 1
        reward = -0.01  # Small penalty per step to encourage efficiency

        # Record agent message
        self._state.conversation.append({
            "role": "agent",
            "content": action,
        })

        # Process any APP_ACTION directives in agent's message
        agent_results = self._process_app_actions(action, self._agent_apps)

        # Get user response (either from simulator or placeholder)
        user_response, user_results = self._get_user_response(action)
        self._state.conversation.append({
            "role": "user",
            "content": user_response,
        })

        # Process any app actions from user
        if user_results:
            reward += 0.1  # Reward for successful coordination

        # Check for user confusion
        if self._detect_user_confusion(user_response):
            reward -= 0.1

        # Check goal state
        goal_achieved = self._check_goal_state()
        if goal_achieved:
            reward += 1.0
            self._state.terminated = True

        # Check truncation
        if self._state.step_count >= self.max_steps:
            self._state.truncated = True

        observation = self._get_observation()
        info = {
            "agent_results": agent_results,
            "user_response": user_response,
            "user_results": user_results,
            "goal_achieved": goal_achieved,
        }

        return (
            observation,
            reward,
            self._state.terminated,
            self._state.truncated,
            info,
        )

    def render(self) -> str | None:
        """Render the environment.

        Returns:
            String representation if render_mode is "ansi", else None
        """
        if self._state is None:
            return None

        if self.render_mode == "ansi":
            lines = [
                f"Step: {self._state.step_count}/{self.max_steps}",
                "-" * 40,
                "Conversation:",
            ]
            for msg in self._state.conversation[-5:]:
                role = msg["role"].upper()
                content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                lines.append(f"  [{role}]: {content}")
            lines.append("-" * 40)
            return "\n".join(lines)

        elif self.render_mode == "human":
            print(self.render())

        return None

    def close(self) -> None:
        """Clean up environment resources."""
        self._state = None
        self._agent_apps = {}
        self._user_apps = {}

    def _get_observation(self) -> dict[str, Any]:
        """Build observation dict from current state."""
        if self._state is None:
            return {"conversation": "", "backend_state": "{}", "step": 0}

        # Format conversation
        conv_lines = []
        for msg in self._state.conversation[-10:]:  # Last 10 messages
            conv_lines.append(f"{msg['role']}: {msg['content']}")
        conversation_text = "\n".join(conv_lines)

        # Format backend state (only agent-visible apps)
        backend_state = {}
        for app_id, app_data in self._agent_apps.items():
            backend_state[app_id] = app_data.get("state", {})

        return {
            "conversation": conversation_text,
            "backend_state": json.dumps(backend_state),
            "step": self._state.step_count,
        }

    def _process_app_actions(
        self,
        message: str,
        apps: dict[str, Any],
    ) -> list[dict]:
        """Process APP_ACTION directives in a message.

        Args:
            message: Message potentially containing APP_ACTION directives
            apps: Dict of apps to process actions against

        Returns:
            List of action results
        """
        # Simple pattern matching for APP_ACTION directives
        import re
        results = []
        pattern = r"APP_ACTION:\s*(\w+)\.(\w+)\((.*?)\)"

        for match in re.finditer(pattern, message):
            app_id = match.group(1)
            action_name = match.group(2)
            params_str = match.group(3)

            if app_id in apps:
                # Would execute actual app action in full implementation
                results.append({
                    "app_id": app_id,
                    "action": action_name,
                    "params": params_str,
                    "success": True,  # Placeholder
                })

        return results

    def _get_user_response(self, agent_message: str) -> tuple[str, list[dict]]:
        """Get user response to agent message.

        Args:
            agent_message: Agent's instruction/message

        Returns:
            Tuple of (user_response_text, action_results)
        """
        if self.user_simulator is not None:
            # Would call user simulator in full implementation
            pass

        # Placeholder response
        return "OK, I did that.", []

    def _detect_user_confusion(self, user_message: str) -> bool:
        """Check if user message indicates confusion."""
        confusion_patterns = [
            "don't understand",
            "what do you mean",
            "confused",
            "not sure",
            "can you clarify",
        ]
        message_lower = user_message.lower()
        return any(p in message_lower for p in confusion_patterns)

    def _check_goal_state(self) -> bool:
        """Check if current state matches goal state."""
        if self._state is None:
            return False

        current_hash = self._compute_state_hash(self._state.app_states)
        goal_hash = self._compute_state_hash(self.task.goal_state)

        return current_hash == goal_hash

    def _compute_state_hash(self, state: dict) -> str:
        """Compute a hash of the state dict."""
        state_json = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()


class DualControlUserEnv(gym.Env if HAS_GYMNASIUM else object):
    """Gymnasium environment for the user in dual-control scenarios.

    The user (customer role) receives instructions from the agent and must
    execute actions on their device apps. This environment is useful for
    training user simulators or evaluating instruction clarity.

    Observation Space:
        Dict containing:
        - conversation: Text of recent conversation history
        - device_state: Dict of device app states visible to user
        - step: Current step number

    Action Space:
        Text - natural language response or APP_ACTION directive

    Rewards:
        - +1.0 for correctly following instructions
        - -0.5 for incorrect actions
        - +0.5 for asking clarifying questions (when appropriate)
    """

    metadata = {"render_modes": ["human", "ansi"]}

    def __init__(
        self,
        task: "DualControlTaskDefinition",
        agent_model: Any = None,
        max_steps: int = 50,
        render_mode: str | None = None,
        state_constrained: bool = True,
    ):
        """Initialize the user environment.

        Args:
            task: Dual-control task definition
            agent_model: Model/agent providing instructions (optional)
            max_steps: Maximum steps before truncation
            render_mode: How to render the environment
            state_constrained: If True, user can only report observable state
        """
        super().__init__()

        if not HAS_GYMNASIUM:
            raise ImportError(
                "gymnasium is required for DualControlUserEnv. "
                "Install with: pip install gymnasium"
            )

        self.task = task
        self.agent_model = agent_model
        self.max_steps = max_steps
        self.render_mode = render_mode
        self.state_constrained = state_constrained

        # Initialize spaces
        self.observation_space = spaces.Dict({
            "conversation": spaces.Text(max_length=50000),
            "device_state": spaces.Text(max_length=10000),
            "step": spaces.Discrete(max_steps + 1),
        })

        self.action_space = spaces.Text(max_length=5000)

        # Internal state
        self._state: EnvState | None = None
        self._observable_fields: set[str] = set()

    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Reset environment to initial state."""
        super().reset(seed=seed)

        self._state = EnvState(
            app_states=copy.deepcopy(self.task.initial_state),
            conversation=[],
            step_count=0,
        )

        # Get initial agent instruction
        if self.task.agent_config.initial_message:
            self._state.conversation.append({
                "role": "agent",
                "content": self.task.agent_config.initial_message,
            })

        observation = self._get_observation()
        info = {"task_id": self.task.task_id}

        return observation, info

    def step(
        self,
        action: str,
    ) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        """Execute user action.

        Args:
            action: User's response or APP_ACTION directive

        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        if self._state is None:
            raise RuntimeError("Call reset() first")

        self._state.step_count += 1
        reward = 0.0

        # Record user message
        self._state.conversation.append({
            "role": "user",
            "content": action,
        })

        # Process user actions
        action_results = self._process_user_action(action)

        # Evaluate action correctness
        if action_results:
            # Check if action matches expected from handoffs
            if self._action_matches_expected(action_results):
                reward += 1.0
            else:
                reward -= 0.5

        # Get next agent message (if agent model provided)
        agent_response = self._get_agent_response(action)
        if agent_response:
            self._state.conversation.append({
                "role": "agent",
                "content": agent_response,
            })

        # Check termination
        goal_achieved = self._check_goal_state()
        if goal_achieved:
            self._state.terminated = True

        if self._state.step_count >= self.max_steps:
            self._state.truncated = True

        observation = self._get_observation()
        info = {
            "action_results": action_results,
            "goal_achieved": goal_achieved,
        }

        return (
            observation,
            reward,
            self._state.terminated,
            self._state.truncated,
            info,
        )

    def render(self) -> str | None:
        """Render the environment."""
        if self._state is None or self.render_mode != "ansi":
            return None

        lines = [f"Step: {self._state.step_count}", "---"]
        for msg in self._state.conversation[-5:]:
            lines.append(f"[{msg['role']}]: {msg['content'][:80]}...")
        return "\n".join(lines)

    def close(self) -> None:
        """Clean up resources."""
        self._state = None

    def _get_observation(self) -> dict[str, Any]:
        """Build observation from current state."""
        if self._state is None:
            return {"conversation": "", "device_state": "{}", "step": 0}

        conv_lines = [f"{m['role']}: {m['content']}" for m in self._state.conversation[-10:]]

        # Filter to observable state if state_constrained
        device_state = self._state.app_states
        if self.state_constrained:
            device_state = self._filter_observable(device_state)

        return {
            "conversation": "\n".join(conv_lines),
            "device_state": json.dumps(device_state),
            "step": self._state.step_count,
        }

    def _filter_observable(self, state: dict) -> dict:
        """Filter state to only observable fields."""
        # Would filter based on StateFieldDef.observable in full implementation
        return state

    def _process_user_action(self, action: str) -> list[dict]:
        """Process user action/APP_ACTION."""
        import re
        results = []
        pattern = r"APP_ACTION:\s*(\w+)\.(\w+)\((.*?)\)"

        for match in re.finditer(pattern, action):
            results.append({
                "app_id": match.group(1),
                "action": match.group(2),
                "params": match.group(3),
            })

        return results

    def _action_matches_expected(self, results: list[dict]) -> bool:
        """Check if user actions match expected handoffs."""
        # Would compare against task.coordination_handoffs in full implementation
        return len(results) > 0

    def _get_agent_response(self, user_action: str) -> str | None:
        """Get agent response to user action."""
        if self.agent_model is not None:
            # Would call agent model in full implementation
            pass
        return None

    def _check_goal_state(self) -> bool:
        """Check if goal state achieved."""
        if self._state is None:
            return False

        current = json.dumps(self._state.app_states, sort_keys=True)
        goal = json.dumps(self.task.goal_state, sort_keys=True)

        return hashlib.sha256(current.encode()).hexdigest() == \
               hashlib.sha256(goal.encode()).hexdigest()


def register_environments() -> None:
    """Register AgentWorld environments with Gymnasium.

    This function registers the dual-control environments so they can be
    created using gym.make().

    Example:
        >>> from agentworld.environment import register_environments
        >>> register_environments()
        >>> env = gym.make("AgentWorld/DualControl-Agent-v0", task=task)
    """
    if not HAS_GYMNASIUM:
        logger.warning("gymnasium not installed, skipping environment registration")
        return

    try:
        gym.register(
            id="AgentWorld/DualControl-Agent-v0",
            entry_point="agentworld.environment.gym_wrapper:DualControlAgentEnv",
        )
        gym.register(
            id="AgentWorld/DualControl-User-v0",
            entry_point="agentworld.environment.gym_wrapper:DualControlUserEnv",
        )
        logger.info("Registered AgentWorld Gymnasium environments")
    except Exception as e:
        logger.warning(f"Failed to register environments: {e}")
