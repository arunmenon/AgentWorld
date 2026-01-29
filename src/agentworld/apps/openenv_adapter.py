"""OpenEnv Adapter - Import OpenEnv environments as AgentWorld apps.

This module provides an adapter that wraps OpenEnv environments
(from Meta/Hugging Face) as AgentWorld SimulatedApp plugins,
enabling agents to use OpenEnv tools alongside native apps.

Example:
    >>> from agentworld.apps.openenv_adapter import OpenEnvApp
    >>>
    >>> # Create adapter for CodingEnv
    >>> coding_app = OpenEnvApp.from_hub("openenv/coding-env")
    >>>
    >>> # Use like any other AgentWorld app
    >>> result = await coding_app.execute(
    ...     agent_id="agent_1",
    ...     action="run_code",
    ...     params={"code": "print('Hello!')"}
    ... )
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from agentworld.apps.base import (
    AppAction,
    AppResult,
    BaseSimulatedApp,
    ParamSpec,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# OpenEnv Types (minimal definitions to avoid hard dependency)
# ==============================================================================


@dataclass
class OpenEnvTool:
    """Representation of an OpenEnv/MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class OpenEnvStepResult:
    """Result from OpenEnv step() call."""

    observation: dict[str, Any]
    reward: float | None = None
    done: bool = False


# ==============================================================================
# OpenEnv Client Protocol
# ==============================================================================


class OpenEnvClientProtocol:
    """Protocol for OpenEnv environment clients.

    This defines the interface that OpenEnv clients must implement.
    Allows us to work with any OpenEnv environment without importing
    the actual openenv package at module level.
    """

    def reset(self, **kwargs: Any) -> Any:
        """Reset the environment."""
        raise NotImplementedError

    def step(self, action: Any) -> Any:
        """Execute an action in the environment."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the environment connection."""
        raise NotImplementedError

    def list_tools(self) -> list[Any]:
        """List available MCP tools (for MCP-based envs)."""
        raise NotImplementedError

    def call_tool(self, name: str, **kwargs: Any) -> Any:
        """Call an MCP tool by name (for MCP-based envs)."""
        raise NotImplementedError

    @property
    def state(self) -> Any:
        """Get current environment state."""
        raise NotImplementedError


# ==============================================================================
# OpenEnv App Adapter
# ==============================================================================


class OpenEnvApp(BaseSimulatedApp):
    """Adapter that wraps an OpenEnv environment as an AgentWorld app.

    This allows OpenEnv environments to be used alongside native AgentWorld
    apps, with the same interface for agents.

    Supports two OpenEnv patterns:
    1. MCP Tool-based (EchoEnv, etc.): Uses list_tools() and call_tool()
    2. Action-based (CodingEnv, Tbench2Env): Uses step() with typed actions

    Example:
        >>> # From Hugging Face Hub
        >>> app = OpenEnvApp.from_hub("openenv/coding-env")
        >>>
        >>> # From local Docker
        >>> app = OpenEnvApp.from_url("http://localhost:8001", env_type="coding")
        >>>
        >>> # Initialize for simulation
        >>> await app.initialize(sim_id="sim_1", agents=["agent_1"], config={})
        >>>
        >>> # Execute action
        >>> result = await app.execute("agent_1", "run_code", {"code": "print(42)"})
    """

    def __init__(
        self,
        env_client: Any,
        app_id: str,
        name: str,
        description: str,
        env_type: str = "mcp",  # "mcp" or "action"
        action_mapping: dict[str, str] | None = None,
    ):
        """Initialize the OpenEnv adapter.

        Args:
            env_client: OpenEnv environment client instance
            app_id: Unique app ID (e.g., "openenv:coding")
            name: Display name (e.g., "OpenEnv Coding")
            description: Description for agents
            env_type: Type of OpenEnv interface ("mcp" or "action")
            action_mapping: Optional mapping of AgentWorld action names to OpenEnv
        """
        super().__init__()
        self._env_client = env_client
        self._app_id = app_id
        self._name = name
        self._description = description
        self._env_type = env_type
        self._action_mapping = action_mapping or {}
        self._tools_cache: list[OpenEnvTool] | None = None
        self._episode_active = False
        self._last_observation: dict[str, Any] = {}
        self._last_reward: float | None = None
        self._episode_done = False

    @classmethod
    def from_hub(
        cls,
        repo_id: str,
        app_id: str | None = None,
        env_type: str = "auto",
    ) -> "OpenEnvApp":
        """Create adapter from Hugging Face Hub.

        Args:
            repo_id: Hub repository ID (e.g., "openenv/coding-env")
            app_id: Optional custom app ID (defaults to repo_id)
            env_type: Environment type ("mcp", "action", or "auto" to detect)

        Returns:
            OpenEnvApp instance

        Example:
            >>> app = OpenEnvApp.from_hub("openenv/coding-env")
        """
        # Import OpenEnv dynamically
        try:
            from openenv.core.env_client import EnvClient
        except ImportError:
            raise ImportError(
                "OpenEnv is not installed. Install with: pip install openenv-core"
            )

        # Determine environment class based on repo_id
        env_name = repo_id.split("/")[-1].replace("-", "_")
        detected_type = env_type

        # Try to import the specific environment
        env_client = None
        try:
            if "coding" in env_name:
                from coding_env import CodingEnv
                env_client = CodingEnv.from_hub(repo_id)
                detected_type = "action" if env_type == "auto" else env_type
            elif "echo" in env_name:
                from echo_env import EchoEnv
                env_client = EchoEnv.from_hub(repo_id)
                detected_type = "mcp" if env_type == "auto" else env_type
            elif "tbench" in env_name or "tb2" in env_name:
                from tbench2_env import Tbench2Env
                env_client = Tbench2Env.from_hub(repo_id)
                detected_type = "action" if env_type == "auto" else env_type
            elif "browser" in env_name:
                from browsergym_env import BrowserGymEnv
                env_client = BrowserGymEnv.from_hub(repo_id)
                detected_type = "action" if env_type == "auto" else env_type
            else:
                # Generic MCP client
                from openenv.core.mcp_client import MCPToolClient
                env_client = MCPToolClient.from_hub(repo_id)
                detected_type = "mcp" if env_type == "auto" else env_type
        except ImportError as e:
            logger.warning(f"Could not import specific env for {repo_id}: {e}")
            # Fall back to generic client
            from openenv.core.mcp_client import MCPToolClient
            env_client = MCPToolClient.from_hub(repo_id)
            detected_type = "mcp"

        return cls(
            env_client=env_client,
            app_id=app_id or f"openenv:{env_name}",
            name=f"OpenEnv {env_name.replace('_', ' ').title()}",
            description=f"OpenEnv environment: {repo_id}",
            env_type=detected_type,
        )

    @classmethod
    def from_url(
        cls,
        base_url: str,
        env_type: str = "mcp",
        app_id: str | None = None,
        name: str | None = None,
    ) -> "OpenEnvApp":
        """Create adapter from a running OpenEnv server URL.

        Args:
            base_url: URL of the OpenEnv server (e.g., "http://localhost:8001")
            env_type: Environment type ("mcp" or "action")
            app_id: Optional custom app ID
            name: Optional custom name

        Returns:
            OpenEnvApp instance

        Example:
            >>> app = OpenEnvApp.from_url("http://localhost:8001", env_type="coding")
        """
        try:
            from openenv.core.mcp_client import MCPToolClient
            from openenv.core.env_client import EnvClient
        except ImportError:
            raise ImportError(
                "OpenEnv is not installed. Install with: pip install openenv-core"
            )

        # Use MCP client for tool-based, generic for action-based
        if env_type == "mcp":
            env_client = MCPToolClient(base_url=base_url)
        else:
            # For action-based, we need to know the specific type
            # Default to generic client that sends raw actions
            env_client = MCPToolClient(base_url=base_url)

        # Derive app_id from URL if not provided
        derived_id = app_id or f"openenv:{base_url.split(':')[-1]}"

        return cls(
            env_client=env_client,
            app_id=derived_id,
            name=name or f"OpenEnv ({base_url})",
            description=f"OpenEnv environment at {base_url}",
            env_type=env_type,
        )

    # ==========================================================================
    # BaseSimulatedApp Implementation
    # ==========================================================================

    @property
    def app_id(self) -> str:
        return self._app_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def get_actions(self) -> list[AppAction]:
        """Get available actions from OpenEnv environment.

        For MCP-based envs, converts tools to actions.
        For action-based envs, returns predefined action schema.
        """
        if self._env_type == "mcp":
            return self._get_mcp_actions()
        else:
            return self._get_typed_actions()

    def _get_mcp_actions(self) -> list[AppAction]:
        """Convert MCP tools to AppAction definitions."""
        actions = []

        # Try to get tools from the environment
        try:
            if self._tools_cache is None:
                raw_tools = self._env_client.list_tools()
                self._tools_cache = [
                    OpenEnvTool(
                        name=t.name if hasattr(t, 'name') else t.get('name', ''),
                        description=t.description if hasattr(t, 'description') else t.get('description', ''),
                        input_schema=t.input_schema if hasattr(t, 'input_schema') else t.get('input_schema', {}),
                    )
                    for t in raw_tools
                ]

            for tool in self._tools_cache:
                params = self._schema_to_params(tool.input_schema)
                actions.append(AppAction(
                    name=tool.name,
                    description=tool.description,
                    parameters=params,
                    returns={"type": "object", "description": "Tool result"},
                ))

        except Exception as e:
            logger.warning(f"Failed to get MCP tools: {e}")
            # Return a generic action
            actions.append(AppAction(
                name="call_tool",
                description="Call an OpenEnv tool",
                parameters={
                    "tool_name": ParamSpec(
                        name="tool_name",
                        type="string",
                        description="Name of the tool to call",
                        required=True,
                    ),
                    "arguments": ParamSpec(
                        name="arguments",
                        type="object",
                        description="Arguments for the tool",
                        required=False,
                        default={},
                    ),
                },
            ))

        return actions

    def _get_typed_actions(self) -> list[AppAction]:
        """Get actions for action-based OpenEnv environments."""
        # Define common actions based on env type
        if "coding" in self._app_id.lower():
            return [
                AppAction(
                    name="run_code",
                    description="Execute code in the environment",
                    parameters={
                        "code": ParamSpec(
                            name="code",
                            type="string",
                            description="Code to execute",
                            required=True,
                        ),
                    },
                    returns={
                        "stdout": "string",
                        "stderr": "string",
                        "exit_code": "number",
                    },
                ),
            ]
        elif "tbench" in self._app_id.lower() or "tb2" in self._app_id.lower():
            return [
                AppAction(
                    name="execute",
                    description="Execute a command in the task environment",
                    parameters={
                        "command": ParamSpec(
                            name="command",
                            type="string",
                            description="Command to execute",
                            required=True,
                        ),
                        "action_type": ParamSpec(
                            name="action_type",
                            type="string",
                            description="Type of action (exec, read, write)",
                            required=False,
                            default="exec",
                        ),
                    },
                    returns={
                        "output": "string",
                        "success": "boolean",
                    },
                ),
                AppAction(
                    name="read_file",
                    description="Read a file in the environment",
                    parameters={
                        "file_path": ParamSpec(
                            name="file_path",
                            type="string",
                            description="Path to the file",
                            required=True,
                        ),
                    },
                ),
                AppAction(
                    name="write_file",
                    description="Write content to a file",
                    parameters={
                        "file_path": ParamSpec(
                            name="file_path",
                            type="string",
                            description="Path to the file",
                            required=True,
                        ),
                        "content": ParamSpec(
                            name="content",
                            type="string",
                            description="Content to write",
                            required=True,
                        ),
                    },
                ),
            ]
        elif "browser" in self._app_id.lower():
            return [
                AppAction(
                    name="navigate",
                    description="Navigate to a URL",
                    parameters={
                        "url": ParamSpec(
                            name="url",
                            type="string",
                            description="URL to navigate to",
                            required=True,
                        ),
                    },
                ),
                AppAction(
                    name="click",
                    description="Click an element",
                    parameters={
                        "selector": ParamSpec(
                            name="selector",
                            type="string",
                            description="CSS selector for the element",
                            required=True,
                        ),
                    },
                ),
                AppAction(
                    name="type_text",
                    description="Type text into an input",
                    parameters={
                        "selector": ParamSpec(
                            name="selector",
                            type="string",
                            description="CSS selector for the input",
                            required=True,
                        ),
                        "text": ParamSpec(
                            name="text",
                            type="string",
                            description="Text to type",
                            required=True,
                        ),
                    },
                ),
            ]
        else:
            # Generic step action
            return [
                AppAction(
                    name="step",
                    description="Execute a step in the environment",
                    parameters={
                        "action": ParamSpec(
                            name="action",
                            type="object",
                            description="Action to execute",
                            required=True,
                        ),
                    },
                ),
            ]

    def _schema_to_params(self, schema: dict[str, Any]) -> dict[str, ParamSpec]:
        """Convert JSON schema to ParamSpec dictionary."""
        params = {}
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        for name, prop in properties.items():
            param_type = prop.get("type", "string")
            # Map JSON schema types to our types
            type_map = {
                "string": "string",
                "integer": "number",
                "number": "number",
                "boolean": "boolean",
                "array": "array",
                "object": "object",
            }

            params[name] = ParamSpec(
                name=name,
                type=type_map.get(param_type, "string"),
                description=prop.get("description", ""),
                required=name in required,
                default=prop.get("default"),
                enum=prop.get("enum"),
            )

        return params

    async def _initialize_state(
        self,
        agents: list[str],
        config: dict[str, Any],
    ) -> None:
        """Initialize OpenEnv environment state."""
        # Reset the OpenEnv environment
        try:
            reset_kwargs = config.get("openenv_reset_kwargs", {})
            self._env_client.reset(**reset_kwargs)
            self._episode_active = True
            self._episode_done = False
            self._last_observation = {}
            self._last_reward = None
            logger.info(f"Reset OpenEnv environment: {self._app_id}")
        except Exception as e:
            logger.error(f"Failed to reset OpenEnv environment: {e}")
            raise

    async def _execute_action(
        self,
        agent_id: str,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute an action in the OpenEnv environment."""
        if self._episode_done:
            return AppResult.fail("Episode has ended. Reset the environment first.")

        try:
            if self._env_type == "mcp":
                return await self._execute_mcp_action(action, params)
            else:
                return await self._execute_typed_action(action, params)
        except Exception as e:
            logger.exception(f"OpenEnv action failed: {e}")
            return AppResult.fail(str(e))

    async def _execute_mcp_action(
        self,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute an MCP tool call."""
        try:
            # Handle generic call_tool action
            if action == "call_tool":
                tool_name = params.get("tool_name")
                arguments = params.get("arguments", {})
            else:
                # Direct tool call
                tool_name = action
                arguments = params

            result = self._env_client.call_tool(tool_name, **arguments)

            # Extract observation data
            data = {
                "result": result,
                "tool_name": tool_name,
            }

            # Check if episode ended
            if hasattr(result, 'done'):
                self._episode_done = result.done
                data["done"] = result.done
            if hasattr(result, 'reward'):
                self._last_reward = result.reward
                data["reward"] = result.reward

            return AppResult.ok(data)

        except Exception as e:
            return AppResult.fail(f"MCP tool call failed: {e}")

    async def _execute_typed_action(
        self,
        action: str,
        params: dict[str, Any],
    ) -> AppResult:
        """Execute a typed action (step-based)."""
        try:
            # Build the action object based on environment type
            if "coding" in self._app_id.lower():
                from coding_env import CodeAction
                if action == "run_code":
                    openenv_action = CodeAction(code=params.get("code", ""))
                else:
                    openenv_action = CodeAction(code=params.get("code", ""))

            elif "tbench" in self._app_id.lower() or "tb2" in self._app_id.lower():
                from tbench2_env import Tbench2Action
                if action == "execute":
                    openenv_action = Tbench2Action(
                        action_type=params.get("action_type", "exec"),
                        command=params.get("command", ""),
                    )
                elif action == "read_file":
                    openenv_action = Tbench2Action(
                        action_type="read",
                        file_path=params.get("file_path", ""),
                    )
                elif action == "write_file":
                    openenv_action = Tbench2Action(
                        action_type="write",
                        file_path=params.get("file_path", ""),
                        content=params.get("content", ""),
                    )
                else:
                    openenv_action = Tbench2Action(**params)

            else:
                # Generic action - pass params directly
                openenv_action = params.get("action", params)

            # Execute step
            result = self._env_client.step(openenv_action)

            # Parse result
            if hasattr(result, 'observation'):
                obs = result.observation
                if hasattr(obs, 'model_dump'):
                    obs_dict = obs.model_dump()
                elif hasattr(obs, '__dict__'):
                    obs_dict = vars(obs)
                else:
                    obs_dict = {"raw": str(obs)}
            else:
                obs_dict = {"raw": str(result)}

            self._last_observation = obs_dict
            self._episode_done = getattr(result, 'done', False)
            self._last_reward = getattr(result, 'reward', None)

            data = {
                **obs_dict,
                "done": self._episode_done,
            }
            if self._last_reward is not None:
                data["reward"] = self._last_reward

            return AppResult.ok(data)

        except ImportError as e:
            # Fall back to raw step if specific env not available
            logger.warning(f"Specific env import failed, using raw step: {e}")
            result = self._env_client.step(params)
            return AppResult.ok({"raw": str(result)})

        except Exception as e:
            return AppResult.fail(f"Action execution failed: {e}")

    async def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Get environment state for an agent."""
        state = {
            "episode_active": self._episode_active,
            "episode_done": self._episode_done,
            "last_observation": self._last_observation,
        }

        if self._last_reward is not None:
            state["last_reward"] = self._last_reward

        # Try to get environment state
        try:
            env_state = self._env_client.state
            if hasattr(env_state, 'model_dump'):
                state["env_state"] = env_state.model_dump()
            elif hasattr(env_state, '__dict__'):
                state["env_state"] = vars(env_state)
        except Exception:
            pass

        return state

    def _get_state_dict(self) -> dict[str, Any]:
        """Get state for serialization."""
        return {
            "episode_active": self._episode_active,
            "episode_done": self._episode_done,
            "last_observation": self._last_observation,
            "last_reward": self._last_reward,
        }

    def _restore_state_dict(self, state: dict[str, Any]) -> None:
        """Restore state from serialization."""
        self._episode_active = state.get("episode_active", False)
        self._episode_done = state.get("episode_done", False)
        self._last_observation = state.get("last_observation", {})
        self._last_reward = state.get("last_reward")

    def close(self) -> None:
        """Close the OpenEnv environment connection."""
        try:
            self._env_client.close()
            logger.info(f"Closed OpenEnv environment: {self._app_id}")
        except Exception as e:
            logger.warning(f"Error closing OpenEnv environment: {e}")


# ==============================================================================
# Convenience Functions
# ==============================================================================


def create_openenv_app(
    env_source: str,
    app_id: str | None = None,
    env_type: str = "auto",
) -> OpenEnvApp:
    """Create an OpenEnv app from a Hub repo or URL.

    Args:
        env_source: Either a Hub repo ID (e.g., "openenv/coding-env")
                   or a URL (e.g., "http://localhost:8001")
        app_id: Optional custom app ID
        env_type: Environment type ("mcp", "action", or "auto")

    Returns:
        OpenEnvApp instance

    Example:
        >>> app = create_openenv_app("openenv/coding-env")
        >>> app = create_openenv_app("http://localhost:8001", env_type="mcp")
    """
    if env_source.startswith("http://") or env_source.startswith("https://"):
        return OpenEnvApp.from_url(env_source, env_type=env_type, app_id=app_id)
    else:
        return OpenEnvApp.from_hub(env_source, app_id=app_id, env_type=env_type)


def list_available_openenv_apps() -> list[dict[str, str]]:
    """List known OpenEnv environments available on Hugging Face Hub.

    Returns:
        List of app info dicts with id, name, repo_id, description
    """
    return [
        {
            "id": "openenv:coding",
            "name": "OpenEnv Coding",
            "repo_id": "openenv/coding-env",
            "description": "Execute Python code in a sandboxed environment",
            "env_type": "action",
        },
        {
            "id": "openenv:echo",
            "name": "OpenEnv Echo",
            "repo_id": "openenv/echo-env",
            "description": "Simple echo environment for testing",
            "env_type": "mcp",
        },
        {
            "id": "openenv:tbench2",
            "name": "OpenEnv TB2",
            "repo_id": "openenv/tbench2-env",
            "description": "τ²-bench task environment",
            "env_type": "action",
        },
        {
            "id": "openenv:browsergym",
            "name": "OpenEnv BrowserGym",
            "repo_id": "openenv/browsergym-env",
            "description": "Web browser automation environment",
            "env_type": "action",
        },
        {
            "id": "openenv:textarena",
            "name": "OpenEnv TextArena",
            "repo_id": "openenv/textarena-env",
            "description": "Text-based games (Wordle, etc.)",
            "env_type": "action",
        },
        {
            "id": "openenv:repl",
            "name": "OpenEnv REPL",
            "repo_id": "openenv/repl-env",
            "description": "Interactive REPL environment",
            "env_type": "action",
        },
    ]
