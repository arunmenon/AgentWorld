/**
 * Goal type definitions for dual-control simulations.
 *
 * Provides a structured taxonomy of goal types for defining success criteria
 * in τ²-bench style evaluations per ADR-020.1.
 */

/**
 * Taxonomy of goal types for dual-control tasks.
 *
 * Categories:
 *   State Goals: Check app data values
 *   Action Goals: Check what user did
 *   Coordination Goals: Check agent-user interaction
 *   Output Goals: Check what agent said
 */
export type GoalType =
  // State-based goals (checking app data)
  | 'state_equals'       // App field equals expected value
  | 'state_contains'     // App field contains substring/item
  | 'state_greater'      // Numeric comparison (>)
  | 'state_less'         // Numeric comparison (<)
  | 'state_exists'       // Field exists (not None)
  // Action-based goals (checking what user did)
  | 'action_executed'    // Specific app action was called
  | 'action_succeeded'   // Action was called AND returned success
  // Coordination-based goals (checking agent-user interaction)
  | 'handoff_completed'  // Specific handoff happened
  | 'all_handoffs_done'  // All required handoffs done
  // Output-based goals (checking what agent said)
  | 'output_contains'    // Agent said specific phrase

/**
 * Comparison operators for goal conditions.
 */
export type GoalOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'not_contains'
  | 'gt'
  | 'lt'
  | 'gte'
  | 'lte'
  | 'exists'
  | 'not_exists'

/**
 * A single goal condition to check.
 */
export interface GoalCondition {
  /** Unique identifier for the condition */
  id?: string
  /** Type of goal (state, action, coordination, output) */
  goalType: GoalType
  /** Human-readable description of the condition */
  description: string

  // For state/action goals
  /** App ID for state/action goals */
  appId?: string
  /** Path to field in app state (e.g., "balance" or "bookings.ABC123.seat") */
  fieldPath?: string
  /** Comparison operator for state goals */
  operator?: GoalOperator
  /** Expected value for comparison */
  expectedValue?: unknown

  // For handoff goals
  /** Handoff ID for coordination goals */
  handoffId?: string

  // For output goals
  /** Required phrase for output goals */
  requiredPhrase?: string
}

/**
 * Complete goal specification for a task.
 */
export interface GoalSpec {
  /** List of goal conditions to evaluate */
  conditions: GoalCondition[]
  /** "all" requires all conditions, "any" requires at least one */
  successMode: 'all' | 'any'
  /** Overall goal description */
  description: string
}

/**
 * Result of evaluating a single goal condition.
 */
export interface ConditionResult {
  /** The condition that was evaluated */
  conditionDescription: string
  /** Whether the condition was met */
  met: boolean
  /** Actual value found (for state conditions) */
  actualValue?: unknown
  /** Step when condition was met */
  stepMet?: number
  /** Additional details */
  details?: string
}

/**
 * Result of evaluating all goal conditions.
 */
export interface GoalEvaluationResult {
  /** Whether the goal was achieved (per success_mode) */
  achieved: boolean
  /** Results for each condition */
  conditionsMet: [string, boolean][]
  /** Count of conditions that are met */
  metCount: number
  /** Total number of conditions */
  totalCount: number
  /** Step number when goal was achieved (if achieved) */
  stepAchieved?: number
  /** Additional details about the evaluation */
  details?: string
}

/**
 * Goal progress information for UI display.
 */
export interface GoalProgress {
  /** Goal specification */
  goalSpec?: GoalSpec
  /** Whether the goal has been achieved */
  goalAchieved: boolean
  /** Step at which goal was achieved */
  goalAchievedStep?: number
  /** Termination mode setting */
  terminationMode: 'max_steps' | 'goal' | 'hybrid'
}

/**
 * Termination mode for simulations.
 */
export type TerminationMode = 'max_steps' | 'goal' | 'hybrid'

/**
 * Get display label for a goal type.
 */
export function getGoalTypeLabel(goalType: GoalType): string {
  const labels: Record<GoalType, string> = {
    state_equals: 'State Equals',
    state_contains: 'State Contains',
    state_greater: 'State Greater Than',
    state_less: 'State Less Than',
    state_exists: 'State Exists',
    action_executed: 'Action Executed',
    action_succeeded: 'Action Succeeded',
    handoff_completed: 'Handoff Completed',
    all_handoffs_done: 'All Handoffs Done',
    output_contains: 'Output Contains',
  }
  return labels[goalType] || goalType
}

/**
 * Get display label for an operator.
 */
export function getOperatorLabel(operator: GoalOperator): string {
  const labels: Record<GoalOperator, string> = {
    equals: 'equals',
    not_equals: 'not equals',
    contains: 'contains',
    not_contains: 'does not contain',
    gt: '>',
    lt: '<',
    gte: '>=',
    lte: '<=',
    exists: 'exists',
    not_exists: 'does not exist',
  }
  return labels[operator] || operator
}

/**
 * Get description of termination mode.
 */
export function getTerminationModeDescription(mode: TerminationMode): string {
  const descriptions: Record<TerminationMode, string> = {
    max_steps: 'Run for exactly the specified number of steps',
    goal: 'Stop when goal conditions are met',
    hybrid: 'Stop at goal OR max steps, whichever comes first',
  }
  return descriptions[mode]
}

/**
 * Convert API goal condition to frontend format.
 */
export function fromApiGoalCondition(data: Record<string, unknown>): GoalCondition {
  return {
    id: data.id as string | undefined,
    goalType: data.goal_type as GoalType,
    description: (data.description as string) || '',
    appId: data.app_id as string | undefined,
    fieldPath: data.field_path as string | undefined,
    operator: data.operator as GoalOperator | undefined,
    expectedValue: data.expected_value,
    handoffId: data.handoff_id as string | undefined,
    requiredPhrase: data.required_phrase as string | undefined,
  }
}

/**
 * Convert frontend goal condition to API format.
 */
export function toApiGoalCondition(condition: GoalCondition): Record<string, unknown> {
  return {
    id: condition.id,
    goal_type: condition.goalType,
    description: condition.description,
    app_id: condition.appId,
    field_path: condition.fieldPath,
    operator: condition.operator,
    expected_value: condition.expectedValue,
    handoff_id: condition.handoffId,
    required_phrase: condition.requiredPhrase,
  }
}

/**
 * Convert API goal spec to frontend format.
 */
export function fromApiGoalSpec(data: Record<string, unknown>): GoalSpec {
  const conditions = (data.conditions as Record<string, unknown>[]) || []
  return {
    conditions: conditions.map(fromApiGoalCondition),
    successMode: (data.success_mode as 'all' | 'any') || 'all',
    description: (data.description as string) || '',
  }
}

/**
 * Convert frontend goal spec to API format.
 */
export function toApiGoalSpec(spec: GoalSpec): Record<string, unknown> {
  return {
    conditions: spec.conditions.map(toApiGoalCondition),
    success_mode: spec.successMode,
    description: spec.description,
  }
}
