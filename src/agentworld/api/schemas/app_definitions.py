"""API schemas for app definitions per ADR-018."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ==============================================================================
# Logic Block Schemas
# ==============================================================================


class ValidateBlockSchema(BaseModel):
    """Schema for a validate logic block."""

    type: Literal["validate"] = "validate"
    condition: str = Field(..., description="Boolean expression to evaluate")
    errorMessage: str = Field(..., description="Error message if validation fails")


class UpdateBlockSchema(BaseModel):
    """Schema for an update logic block."""

    type: Literal["update"] = "update"
    target: str = Field(..., description="State path to update")
    operation: Literal["set", "add", "subtract", "append", "remove", "merge"] = Field(
        ..., description="Update operation"
    )
    value: Any = Field(..., description="Value to use in operation")


class NotifyBlockSchema(BaseModel):
    """Schema for a notify logic block."""

    type: Literal["notify"] = "notify"
    to: str = Field(..., description="Target agent ID expression")
    message: str = Field(..., description="Message template with interpolation")
    data: dict[str, Any] | None = Field(None, description="Optional structured data")


class ReturnBlockSchema(BaseModel):
    """Schema for a return logic block."""

    type: Literal["return"] = "return"
    value: dict[str, Any] = Field(..., description="Return value with expressions")


class ErrorBlockSchema(BaseModel):
    """Schema for an error logic block."""

    type: Literal["error"] = "error"
    message: str = Field(..., description="Error message")


class BranchBlockSchema(BaseModel):
    """Schema for a branch logic block."""

    type: Literal["branch"] = "branch"
    condition: str = Field(..., description="Boolean condition")
    then: list[dict[str, Any]] = Field(..., description="Blocks to execute if true")
    else_: list[dict[str, Any]] | None = Field(
        None, alias="else", description="Blocks to execute if false"
    )

    class Config:
        populate_by_name = True


class LoopBlockSchema(BaseModel):
    """Schema for a loop logic block."""

    type: Literal["loop"] = "loop"
    collection: str = Field(..., description="Array expression to iterate")
    item: str = Field(..., description="Variable name for current item")
    body: list[dict[str, Any]] = Field(..., description="Blocks to execute per item")


# Generic logic block (union type via dict)
LogicBlockSchema = dict[str, Any]


# ==============================================================================
# Parameter and State Schemas
# ==============================================================================


class ParamSpecSchema(BaseModel):
    """Schema for a parameter specification."""

    type: Literal["string", "number", "boolean", "array", "object"] = Field(
        ..., description="Parameter type"
    )
    description: str = Field("", description="Parameter description")
    required: bool = Field(False, description="Whether parameter is required")
    default: Any = Field(None, description="Default value")
    minValue: float | None = Field(None, description="Minimum value for numbers")
    maxValue: float | None = Field(None, description="Maximum value for numbers")
    minLength: int | None = Field(None, description="Minimum length for strings")
    maxLength: int | None = Field(None, description="Maximum length for strings")
    pattern: str | None = Field(None, description="Regex pattern for strings")
    enum: list[Any] | None = Field(None, description="Allowed values")


class StateFieldSchema(BaseModel):
    """Schema for a state field definition."""

    name: str = Field(..., description="Field name")
    type: Literal["string", "number", "boolean", "array", "object"] = Field(
        ..., description="Field type"
    )
    default: Any = Field(None, description="Default value")
    perAgent: bool = Field(True, description="Whether field is per-agent or shared")
    description: str = Field("", description="Field description")


class ConfigFieldSchema(BaseModel):
    """Schema for a config field definition."""

    name: str = Field(..., description="Field name")
    label: str = Field(..., description="Display label")
    type: Literal["string", "number", "boolean", "select"] = Field(
        ..., description="Field type"
    )
    description: str = Field("", description="Field description")
    default: Any = Field(None, description="Default value")
    required: bool = Field(False, description="Whether field is required")
    min: float | None = Field(None, description="Minimum value")
    max: float | None = Field(None, description="Maximum value")
    step: float | None = Field(None, description="Step value for numbers")
    options: list[dict[str, str]] | None = Field(
        None, description="Options for select type"
    )


# ==============================================================================
# Action Schema
# ==============================================================================


class ActionDefinitionSchema(BaseModel):
    """Schema for an action definition."""

    name: str = Field(..., description="Action name (snake_case)")
    description: str = Field(..., description="Action description")
    parameters: dict[str, ParamSpecSchema] = Field(
        default_factory=dict, description="Parameter specifications"
    )
    returns: dict[str, Any] = Field(
        default_factory=dict, description="Return value specification"
    )
    logic: list[LogicBlockSchema] = Field(
        default_factory=list, description="Logic blocks"
    )


# ==============================================================================
# App Definition Schemas
# ==============================================================================


class AppDefinitionBase(BaseModel):
    """Base schema for app definition."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: str = Field("", max_length=500, description="App description")
    category: Literal[
        "payment", "shopping", "communication", "calendar", "social", "custom"
    ] = Field(..., description="App category")
    icon: str = Field("", description="Emoji or icon key")
    actions: list[ActionDefinitionSchema] = Field(
        default_factory=list, description="Available actions"
    )
    state_schema: list[StateFieldSchema] = Field(
        default_factory=list, description="State field definitions"
    )
    initial_config: dict[str, Any] = Field(
        default_factory=dict, description="Default config values"
    )
    config_schema: list[ConfigFieldSchema] = Field(
        default_factory=list, description="Config field definitions for UI"
    )


class CreateAppDefinitionRequest(AppDefinitionBase):
    """Request schema for creating an app definition."""

    app_id: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique app identifier (snake_case)",
    )


class UpdateAppDefinitionRequest(BaseModel):
    """Request schema for updating an app definition."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    category: Literal[
        "payment", "shopping", "communication", "calendar", "social", "custom"
    ] | None = None
    icon: str | None = None
    actions: list[ActionDefinitionSchema] | None = None
    state_schema: list[StateFieldSchema] | None = None
    initial_config: dict[str, Any] | None = None
    config_schema: list[ConfigFieldSchema] | None = None


class AppDefinitionResponse(AppDefinitionBase):
    """Response schema for an app definition."""

    id: str = Field(..., description="Database ID")
    app_id: str = Field(..., description="Unique app identifier")
    version: int = Field(1, description="Definition version")
    is_builtin: bool = Field(False, description="Whether this is a built-in app")
    is_active: bool = Field(True, description="Whether app is active")
    created_by: str | None = Field(None, description="Creator user ID")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class AppDefinitionListResponse(BaseModel):
    """Response schema for listing app definitions."""

    definitions: list[AppDefinitionResponse] = Field(
        default_factory=list, description="List of app definitions"
    )
    total: int = Field(0, description="Total count")


class AppDefinitionVersionResponse(BaseModel):
    """Response schema for an app definition version."""

    id: str = Field(..., description="Version record ID")
    app_definition_id: str = Field(..., description="App definition ID")
    version: int = Field(..., description="Version number")
    definition: dict[str, Any] = Field(..., description="Full definition JSON")
    created_at: datetime | None = Field(None, description="Creation timestamp")


class AppDefinitionVersionListResponse(BaseModel):
    """Response schema for listing version history."""

    versions: list[AppDefinitionVersionResponse] = Field(
        default_factory=list, description="List of versions"
    )
    total: int = Field(0, description="Total count")


# ==============================================================================
# Test Endpoint Schemas
# ==============================================================================


class TestActionRequest(BaseModel):
    """Request schema for testing an action."""

    action: str = Field(..., description="Action name to test")
    agent_id: str = Field(..., description="Test agent ID")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    state: dict[str, Any] | None = Field(
        None, description="Optional initial state override"
    )
    config: dict[str, Any] | None = Field(
        None, description="Optional config override"
    )


class TestActionResponse(BaseModel):
    """Response schema for test action result."""

    success: bool = Field(..., description="Whether action succeeded")
    data: dict[str, Any] | None = Field(None, description="Result data if successful")
    error: str | None = Field(None, description="Error message if failed")
    state_before: dict[str, Any] = Field(..., description="State before action")
    state_after: dict[str, Any] = Field(..., description="State after action")
    observations: list[dict[str, Any]] = Field(
        default_factory=list, description="Notifications generated"
    )


# ==============================================================================
# Duplicate Request Schema
# ==============================================================================


class DuplicateAppRequest(BaseModel):
    """Request schema for duplicating an app."""

    new_app_id: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="New app identifier",
    )
    new_name: str = Field(..., min_length=1, max_length=100, description="New display name")
