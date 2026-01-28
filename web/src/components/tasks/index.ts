/**
 * Task Definition & Results Components
 *
 * Per ADR-020.1 Phase 10h-8: UI - Task Definition & Results
 *
 * Components for creating dual-control evaluation tasks
 * and analyzing their results.
 */

// Task Definition
export { DualControlTaskForm } from './DualControlTaskForm'
export type { DualControlTask, GoalStateCondition, ExpectedHandoff } from './DualControlTaskForm'

export { HandoffEditor } from './HandoffEditor'
export { GoalStateEditor } from './GoalStateEditor'

// Results & Analysis
export { SoloDualComparison } from './SoloDualComparison'
export type { TaskRunResult, SoloDualComparisonProps } from './SoloDualComparison'

export { CoordinationAnalysis } from './CoordinationAnalysis'
export type { HandoffResult, CoordinationAnalysisProps } from './CoordinationAnalysis'
