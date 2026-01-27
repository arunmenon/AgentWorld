"""App quality metrics for ADR-021.

This module provides quality scoring for app definitions based on:
- Completeness: All required fields populated
- Documentation: Actions have descriptions
- Validation: Actions validate inputs
- Error Handling: Logic handles error cases
- State Safety: No unbounded state growth
- Consistency: Naming conventions followed
"""

from dataclasses import dataclass, field
from typing import Any
import re


@dataclass
class QualitySuggestion:
    """A suggestion for improving app quality.

    Attributes:
        dimension: Which quality dimension this affects
        priority: 'high', 'medium', 'low'
        message: Human-readable suggestion
        action_name: Which action this applies to (if any)
    """
    dimension: str
    priority: str
    message: str
    action_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimension": self.dimension,
            "priority": self.priority,
            "message": self.message,
            "action_name": self.action_name,
        }


@dataclass
class QualityReport:
    """Quality assessment report for an app definition.

    Attributes:
        app_id: The app being evaluated
        overall_score: Weighted average score (0-100)
        level: Quality level ('Excellent', 'Good', 'Acceptable', 'Needs Work')
        dimension_scores: Score per dimension
        suggestions: List of improvement suggestions
        details: Detailed breakdown per dimension
    """
    app_id: str
    overall_score: float
    level: str
    dimension_scores: dict[str, float] = field(default_factory=dict)
    suggestions: list[QualitySuggestion] = field(default_factory=list)
    details: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "app_id": self.app_id,
            "overall_score": self.overall_score,
            "level": self.level,
            "dimension_scores": self.dimension_scores,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "details": self.details,
        }


# Quality dimension weights
QUALITY_WEIGHTS = {
    "completeness": 0.25,
    "documentation": 0.20,
    "validation": 0.20,
    "error_handling": 0.15,
    "state_safety": 0.10,
    "consistency": 0.10,
}


def get_quality_level(score: float) -> str:
    """Get quality level from score.

    Args:
        score: Overall quality score (0-100)

    Returns:
        Quality level string
    """
    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Acceptable"
    else:
        return "Needs Work"


def score_completeness(app_def: dict) -> tuple[float, dict[str, Any], list[QualitySuggestion]]:
    """Score app completeness.

    Checks for required fields:
    - app_id, name, description, category, icon
    - At least one action
    - Actions have names and descriptions
    - Parameters have types

    Args:
        app_def: App definition dictionary

    Returns:
        Tuple of (score, details, suggestions)
    """
    suggestions = []
    details = {"missing_fields": [], "action_issues": []}

    # Required top-level fields
    required_fields = ["app_id", "name", "description", "category"]
    optional_fields = ["icon", "state_schema", "initial_config"]

    present_required = 0
    for f in required_fields:
        if app_def.get(f):
            present_required += 1
        else:
            details["missing_fields"].append(f)
            suggestions.append(QualitySuggestion(
                dimension="completeness",
                priority="high",
                message=f"Add required field '{f}'"
            ))

    # Optional fields bonus
    present_optional = sum(1 for f in optional_fields if app_def.get(f))

    # Actions
    actions = app_def.get("actions", [])
    if not actions:
        details["action_issues"].append("No actions defined")
        suggestions.append(QualitySuggestion(
            dimension="completeness",
            priority="high",
            message="Add at least one action"
        ))
        action_score = 0
    else:
        action_scores = []
        for action in actions:
            action_name = action.get("name", "unnamed")
            action_fields = 0
            total_action_fields = 4  # name, description, parameters, logic

            if action.get("name"):
                action_fields += 1
            if action.get("description"):
                action_fields += 1
            if "parameters" in action:
                action_fields += 1
                # Check parameter completeness
                params = action.get("parameters", {})
                for pname, pspec in params.items():
                    if not pspec.get("type"):
                        details["action_issues"].append(f"{action_name}: param '{pname}' missing type")
                        suggestions.append(QualitySuggestion(
                            dimension="completeness",
                            priority="medium",
                            message=f"Add type for parameter '{pname}'",
                            action_name=action_name
                        ))
            if action.get("logic"):
                action_fields += 1
            else:
                details["action_issues"].append(f"{action_name}: no logic defined")
                suggestions.append(QualitySuggestion(
                    dimension="completeness",
                    priority="high",
                    message="Add logic blocks",
                    action_name=action_name
                ))

            action_scores.append(action_fields / total_action_fields * 100)

        action_score = sum(action_scores) / len(action_scores) if action_scores else 0

    # Calculate final score
    base_score = (present_required / len(required_fields)) * 70
    optional_bonus = (present_optional / len(optional_fields)) * 10
    action_contribution = action_score * 0.2

    score = min(100, base_score + optional_bonus + action_contribution)
    details["required_fields_present"] = present_required
    details["optional_fields_present"] = present_optional
    details["action_count"] = len(actions)

    return score, details, suggestions


def score_documentation(app_def: dict) -> tuple[float, dict[str, Any], list[QualitySuggestion]]:
    """Score app documentation quality.

    Checks:
    - App has description
    - Actions have descriptions
    - Parameters have descriptions
    - Returns are documented

    Args:
        app_def: App definition dictionary

    Returns:
        Tuple of (score, details, suggestions)
    """
    suggestions = []
    details = {"undocumented_actions": [], "undocumented_params": []}

    scores = []

    # App description
    if app_def.get("description"):
        desc_len = len(app_def["description"])
        if desc_len < 20:
            scores.append(50)
            suggestions.append(QualitySuggestion(
                dimension="documentation",
                priority="low",
                message="App description is very short, consider adding more detail"
            ))
        else:
            scores.append(100)
    else:
        scores.append(0)
        suggestions.append(QualitySuggestion(
            dimension="documentation",
            priority="medium",
            message="Add app description"
        ))

    # Action documentation
    actions = app_def.get("actions", [])
    for action in actions:
        action_name = action.get("name", "unnamed")

        # Action description
        if action.get("description"):
            desc_len = len(action["description"])
            if desc_len < 10:
                scores.append(50)
            else:
                scores.append(100)
        else:
            scores.append(0)
            details["undocumented_actions"].append(action_name)
            suggestions.append(QualitySuggestion(
                dimension="documentation",
                priority="medium",
                message=f"Add description",
                action_name=action_name
            ))

        # Parameter documentation
        params = action.get("parameters", {})
        for pname, pspec in params.items():
            if pspec.get("description"):
                scores.append(100)
            else:
                scores.append(0)
                details["undocumented_params"].append(f"{action_name}.{pname}")
                suggestions.append(QualitySuggestion(
                    dimension="documentation",
                    priority="low",
                    message=f"Add description for parameter '{pname}'",
                    action_name=action_name
                ))

    score = sum(scores) / len(scores) if scores else 0
    details["documented_actions"] = len(actions) - len(details["undocumented_actions"])
    details["total_actions"] = len(actions)

    return score, details, suggestions


def score_validation(app_def: dict) -> tuple[float, dict[str, Any], list[QualitySuggestion]]:
    """Score input validation coverage.

    Checks:
    - Actions with parameters have VALIDATE blocks
    - Required parameters are validated
    - Type-appropriate validation (e.g., number ranges)

    Args:
        app_def: App definition dictionary

    Returns:
        Tuple of (score, details, suggestions)
    """
    suggestions = []
    details = {"actions_with_validation": [], "actions_without_validation": []}

    actions = app_def.get("actions", [])
    if not actions:
        return 0, details, suggestions

    scores = []

    for action in actions:
        action_name = action.get("name", "unnamed")
        params = action.get("parameters", {})
        required_params = [p for p, spec in params.items() if spec.get("required", False)]

        logic = action.get("logic", [])
        validate_blocks = [b for b in logic if b.get("type") == "validate"]

        if not params:
            # No parameters = no validation needed
            scores.append(100)
            continue

        if not validate_blocks:
            scores.append(0)
            details["actions_without_validation"].append(action_name)
            suggestions.append(QualitySuggestion(
                dimension="validation",
                priority="high",
                message="Add VALIDATE blocks for input parameters",
                action_name=action_name
            ))
        else:
            # Check if required params are likely validated
            validate_conditions = " ".join(b.get("condition", "") for b in validate_blocks)
            validated_params = 0

            for param in required_params:
                if param in validate_conditions or f"params.{param}" in validate_conditions:
                    validated_params += 1

            if required_params:
                param_coverage = validated_params / len(required_params)
            else:
                param_coverage = 1.0

            score = (len(validate_blocks) > 0) * 50 + param_coverage * 50
            scores.append(score)

            if score >= 80:
                details["actions_with_validation"].append(action_name)
            else:
                details["actions_without_validation"].append(action_name)

                missing = [p for p in required_params if p not in validate_conditions and f"params.{p}" not in validate_conditions]
                if missing:
                    suggestions.append(QualitySuggestion(
                        dimension="validation",
                        priority="medium",
                        message=f"Add validation for required params: {', '.join(missing)}",
                        action_name=action_name
                    ))

    final_score = sum(scores) / len(scores) if scores else 0
    details["validation_coverage"] = f"{len(details['actions_with_validation'])}/{len(actions)}"

    return final_score, details, suggestions


def score_error_handling(app_def: dict) -> tuple[float, dict[str, Any], list[QualitySuggestion]]:
    """Score error handling coverage.

    Checks:
    - Actions have ERROR blocks
    - BRANCH blocks have else paths
    - Validate failures have messages

    Args:
        app_def: App definition dictionary

    Returns:
        Tuple of (score, details, suggestions)
    """
    suggestions = []
    details = {"actions_with_error_handling": [], "actions_without_error_handling": []}

    actions = app_def.get("actions", [])
    if not actions:
        return 0, details, suggestions

    scores = []

    for action in actions:
        action_name = action.get("name", "unnamed")
        logic = action.get("logic", [])

        def count_blocks(blocks: list, block_type: str) -> int:
            count = 0
            for block in blocks:
                if block.get("type") == block_type:
                    count += 1
                # Check nested blocks
                if block.get("type") == "branch":
                    count += count_blocks(block.get("then", []), block_type)
                    count += count_blocks(block.get("else", []), block_type)
                if block.get("type") == "loop":
                    count += count_blocks(block.get("body", []), block_type)
            return count

        def count_branches_without_else(blocks: list) -> int:
            count = 0
            for block in blocks:
                if block.get("type") == "branch":
                    if not block.get("else"):
                        count += 1
                    count += count_branches_without_else(block.get("then", []))
                    count += count_branches_without_else(block.get("else", []))
                if block.get("type") == "loop":
                    count += count_branches_without_else(block.get("body", []))
            return count

        error_blocks = count_blocks(logic, "error")
        validate_blocks = count_blocks(logic, "validate")
        branches_without_else = count_branches_without_else(logic)

        # Score based on error handling presence
        if error_blocks > 0 or validate_blocks > 0:
            base_score = 50
            # Bonus for each error block
            base_score += min(50, error_blocks * 10)
            # Penalty for branches without else
            base_score -= branches_without_else * 5
            scores.append(max(0, min(100, base_score)))
            details["actions_with_error_handling"].append(action_name)
        else:
            scores.append(0)
            details["actions_without_error_handling"].append(action_name)
            suggestions.append(QualitySuggestion(
                dimension="error_handling",
                priority="medium",
                message="Add ERROR blocks or VALIDATE blocks for error cases",
                action_name=action_name
            ))

        if branches_without_else > 0:
            suggestions.append(QualitySuggestion(
                dimension="error_handling",
                priority="low",
                message=f"{branches_without_else} BRANCH block(s) missing 'else' path",
                action_name=action_name
            ))

    final_score = sum(scores) / len(scores) if scores else 0

    return final_score, details, suggestions


def score_state_safety(app_def: dict) -> tuple[float, dict[str, Any], list[QualitySuggestion]]:
    """Score state safety.

    Checks for potential issues:
    - Unbounded array growth (append without limit)
    - Missing state schema
    - Update operations on undefined fields

    Args:
        app_def: App definition dictionary

    Returns:
        Tuple of (score, details, suggestions)
    """
    suggestions = []
    details = {"issues": [], "state_schema_defined": False}

    score = 100  # Start with perfect score, deduct for issues

    # Check state schema
    state_schema = app_def.get("state_schema", [])
    if state_schema:
        details["state_schema_defined"] = True
        details["state_fields"] = len(state_schema)
    else:
        score -= 20
        details["state_schema_defined"] = False
        suggestions.append(QualitySuggestion(
            dimension="state_safety",
            priority="medium",
            message="Define state_schema to document state structure"
        ))

    # Check for unbounded growth patterns
    actions = app_def.get("actions", [])

    def check_unbounded_growth(blocks: list, action_name: str) -> list[str]:
        issues = []
        for block in blocks:
            if block.get("type") == "update" and block.get("operation") == "append":
                # Check if there's a corresponding remove or limit
                target = block.get("target", "")
                issues.append(f"{action_name}: 'append' to {target} without visible limit")

            # Check nested
            if block.get("type") == "branch":
                issues.extend(check_unbounded_growth(block.get("then", []), action_name))
                issues.extend(check_unbounded_growth(block.get("else", []), action_name))
            if block.get("type") == "loop":
                issues.extend(check_unbounded_growth(block.get("body", []), action_name))

        return issues

    growth_issues = []
    for action in actions:
        action_name = action.get("name", "unnamed")
        logic = action.get("logic", [])
        growth_issues.extend(check_unbounded_growth(logic, action_name))

    if growth_issues:
        # Reduce score but don't be too harsh - this is a heuristic
        score -= len(growth_issues) * 10
        details["issues"].extend(growth_issues)
        suggestions.append(QualitySuggestion(
            dimension="state_safety",
            priority="low",
            message="Consider adding limits for array growth operations"
        ))

    return max(0, score), details, suggestions


def score_consistency(app_def: dict) -> tuple[float, dict[str, Any], list[QualitySuggestion]]:
    """Score naming and style consistency.

    Checks:
    - app_id follows snake_case
    - Action names follow snake_case
    - Parameter names follow snake_case
    - State fields follow snake_case

    Args:
        app_def: App definition dictionary

    Returns:
        Tuple of (score, details, suggestions)
    """
    suggestions = []
    details = {"violations": []}

    snake_case_pattern = re.compile(r'^[a-z][a-z0-9_]*$')

    violations = []
    total_names = 0

    # Check app_id
    app_id = app_def.get("app_id", "")
    if app_id:
        total_names += 1
        if not snake_case_pattern.match(app_id):
            violations.append(f"app_id '{app_id}' should be snake_case")

    # Check action names
    actions = app_def.get("actions", [])
    for action in actions:
        action_name = action.get("name", "")
        if action_name:
            total_names += 1
            if not snake_case_pattern.match(action_name):
                violations.append(f"Action name '{action_name}' should be snake_case")

        # Check parameter names
        params = action.get("parameters", {})
        for pname in params.keys():
            total_names += 1
            if not snake_case_pattern.match(pname):
                violations.append(f"Parameter '{pname}' in {action_name} should be snake_case")

    # Check state schema
    state_schema = app_def.get("state_schema", [])
    for field in state_schema:
        field_name = field.get("name", "")
        if field_name:
            total_names += 1
            if not snake_case_pattern.match(field_name):
                violations.append(f"State field '{field_name}' should be snake_case")

    details["violations"] = violations
    details["total_names_checked"] = total_names
    details["violations_count"] = len(violations)

    if violations:
        for v in violations[:3]:  # Limit suggestions
            suggestions.append(QualitySuggestion(
                dimension="consistency",
                priority="low",
                message=v
            ))

    if total_names == 0:
        score = 100
    else:
        score = max(0, 100 - (len(violations) / total_names * 100))

    return score, details, suggestions


def calculate_quality_score(app_def: dict) -> QualityReport:
    """Calculate overall quality score for an app definition.

    Evaluates the app across six dimensions:
    - Completeness (25%): Required fields populated
    - Documentation (20%): Actions have descriptions
    - Validation (20%): Actions validate inputs
    - Error Handling (15%): Logic handles error cases
    - State Safety (10%): No unbounded state growth
    - Consistency (10%): Naming conventions followed

    Args:
        app_def: App definition dictionary (or AppDefinition dataclass)

    Returns:
        QualityReport with scores and suggestions
    """
    # Convert dataclass to dict if needed
    if hasattr(app_def, "to_dict"):
        app_def = app_def.to_dict()

    app_id = app_def.get("app_id", "unknown")

    # Score each dimension
    completeness_score, completeness_details, completeness_suggestions = score_completeness(app_def)
    documentation_score, documentation_details, documentation_suggestions = score_documentation(app_def)
    validation_score, validation_details, validation_suggestions = score_validation(app_def)
    error_handling_score, error_handling_details, error_handling_suggestions = score_error_handling(app_def)
    state_safety_score, state_safety_details, state_safety_suggestions = score_state_safety(app_def)
    consistency_score, consistency_details, consistency_suggestions = score_consistency(app_def)

    # Aggregate scores
    dimension_scores = {
        "completeness": completeness_score,
        "documentation": documentation_score,
        "validation": validation_score,
        "error_handling": error_handling_score,
        "state_safety": state_safety_score,
        "consistency": consistency_score,
    }

    # Calculate weighted average
    overall_score = sum(
        dimension_scores[dim] * weight
        for dim, weight in QUALITY_WEIGHTS.items()
    )

    # Aggregate details
    details = {
        "completeness": completeness_details,
        "documentation": documentation_details,
        "validation": validation_details,
        "error_handling": error_handling_details,
        "state_safety": state_safety_details,
        "consistency": consistency_details,
    }

    # Aggregate and prioritize suggestions
    all_suggestions = (
        completeness_suggestions +
        documentation_suggestions +
        validation_suggestions +
        error_handling_suggestions +
        state_safety_suggestions +
        consistency_suggestions
    )

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_suggestions.sort(key=lambda s: priority_order.get(s.priority, 3))

    return QualityReport(
        app_id=app_id,
        overall_score=round(overall_score, 2),
        level=get_quality_level(overall_score),
        dimension_scores={k: round(v, 2) for k, v in dimension_scores.items()},
        suggestions=all_suggestions,
        details=details,
    )
