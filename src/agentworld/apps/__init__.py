"""Simulated applications for AgentWorld.

This package provides the framework for simulated apps that agents
can interact with during simulations, inspired by the AppWorld paper.

Example usage:
    from agentworld.apps import get_app_registry, AppResult

    # Get registry and create app instance
    registry = get_app_registry()
    paypal = registry.get("paypal")

    # Initialize for a simulation
    await paypal.initialize(
        sim_id="sim123",
        agents=["alice", "bob"],
        config={"initial_balance": 1000}
    )

    # Execute an action
    result = await paypal.execute(
        agent_id="alice",
        action="transfer",
        params={"to": "bob", "amount": 50}
    )

Dynamic App Example (ADR-018):
    from agentworld.apps import DynamicApp, AppDefinition

    # Create from JSON definition
    definition = AppDefinition.from_dict({
        "app_id": "my_app",
        "name": "My App",
        "category": "custom",
        "actions": [...]
    })
    app = DynamicApp(definition)
"""

from agentworld.apps.base import (
    # Data structures
    ParamSpec,
    AppAction,
    AppResult,
    AppObservation,
    AppActionLogEntry,
    # Event types
    AppEventType,
    # Protocol and base class
    SimulatedAppPlugin,
    BaseSimulatedApp,
    # Registry
    AppRegistry,
    get_app_registry,
)
from agentworld.apps.paypal import PayPalApp, register_paypal_app
from agentworld.apps.parser import (
    ParsedAction,
    ParseError,
    ParseResult,
    parse_message,
    extract_actions,
    format_action,
)
from agentworld.apps.manager import (
    SimulationAppManager,
    AppExecutionResult,
)

# Dynamic app support (ADR-018)
from agentworld.apps.definition import (
    AppDefinition,
    ActionDefinition,
    AppState,
    ParamSpecDef,
    StateFieldDef,
    ConfigFieldDef,
    # Logic blocks
    LogicBlock,
    ValidateBlock,
    UpdateBlock,
    NotifyBlock,
    ReturnBlock,
    ErrorBlock,
    BranchBlock,
    LoopBlock,
    # Enums (ADR-018)
    AppCategory,
    ParamType,
    LogicBlockType,
    UpdateOperation,
    # Enums (ADR-020.1 dual-control)
    AppAccessType,
    AppStateType,
    ToolType,
    AgentRole,
)
from agentworld.apps.dynamic import DynamicApp, create_dynamic_app
from agentworld.apps.expression import (
    ExpressionEvaluator,
    ExpressionError,
    evaluate,
    interpolate,
)
from agentworld.apps.logic_engine import (
    LogicEngine,
    ExecutionContext,
)

__all__ = [
    # Data structures
    "ParamSpec",
    "AppAction",
    "AppResult",
    "AppObservation",
    "AppActionLogEntry",
    # Event types
    "AppEventType",
    # Protocol and base class
    "SimulatedAppPlugin",
    "BaseSimulatedApp",
    # Registry
    "AppRegistry",
    "get_app_registry",
    # Built-in apps
    "PayPalApp",
    "register_paypal_app",
    # Parser
    "ParsedAction",
    "ParseError",
    "ParseResult",
    "parse_message",
    "extract_actions",
    "format_action",
    # Manager
    "SimulationAppManager",
    "AppExecutionResult",
    # Dynamic app support (ADR-018)
    "AppDefinition",
    "ActionDefinition",
    "AppState",
    "ParamSpecDef",
    "StateFieldDef",
    "ConfigFieldDef",
    # Logic blocks
    "LogicBlock",
    "ValidateBlock",
    "UpdateBlock",
    "NotifyBlock",
    "ReturnBlock",
    "ErrorBlock",
    "BranchBlock",
    "LoopBlock",
    # Enums (ADR-018)
    "AppCategory",
    "ParamType",
    "LogicBlockType",
    "UpdateOperation",
    # Enums (ADR-020.1 dual-control)
    "AppAccessType",
    "AppStateType",
    "ToolType",
    "AgentRole",
    # Dynamic app classes
    "DynamicApp",
    "create_dynamic_app",
    # Expression evaluation
    "ExpressionEvaluator",
    "ExpressionError",
    "evaluate",
    "interpolate",
    # Logic engine
    "LogicEngine",
    "ExecutionContext",
]

# Register built-in apps
register_paypal_app()
