/**
 * State diff utility for computing differences between state snapshots.
 *
 * Used by the EpisodeHistoryPanel and StateDiffView components to show
 * what changed between steps instead of full state dumps.
 */

export interface ChangedField {
  path: string
  before: unknown
  after: unknown
  type: 'added' | 'removed' | 'modified'
}

export interface StateDiff {
  changes: ChangedField[]
  hasChanges: boolean
  addedCount: number
  removedCount: number
  modifiedCount: number
}

/**
 * Compute the difference between two state objects.
 *
 * @param before - State before the action
 * @param after - State after the action
 * @returns StateDiff with all changes
 */
export function computeStateDiff(
  before: Record<string, unknown>,
  after: Record<string, unknown>
): StateDiff {
  const changes: ChangedField[] = []

  function compare(path: string, a: unknown, b: unknown) {
    // Handle null/undefined
    if (a === undefined && b !== undefined) {
      changes.push({ path, before: a, after: b, type: 'added' })
      return
    }
    if (a !== undefined && b === undefined) {
      changes.push({ path, before: a, after: b, type: 'removed' })
      return
    }
    if (a === null && b === null) return
    if (a === null || b === null) {
      if (a !== b) {
        changes.push({ path, before: a, after: b, type: 'modified' })
      }
      return
    }

    // Handle primitives
    if (typeof a !== 'object' || typeof b !== 'object') {
      if (a !== b) {
        changes.push({ path, before: a, after: b, type: 'modified' })
      }
      return
    }

    // Handle arrays
    if (Array.isArray(a) && Array.isArray(b)) {
      if (JSON.stringify(a) !== JSON.stringify(b)) {
        // For simplicity, treat array differences as modifications
        changes.push({ path, before: a, after: b, type: 'modified' })
      }
      return
    }

    // Handle objects
    const aObj = a as Record<string, unknown>
    const bObj = b as Record<string, unknown>
    const allKeys = new Set([...Object.keys(aObj), ...Object.keys(bObj)])

    for (const key of allKeys) {
      const newPath = path ? `${path}.${key}` : key
      compare(newPath, aObj[key], bObj[key])
    }
  }

  compare('', before, after)

  return {
    changes,
    hasChanges: changes.length > 0,
    addedCount: changes.filter((c) => c.type === 'added').length,
    removedCount: changes.filter((c) => c.type === 'removed').length,
    modifiedCount: changes.filter((c) => c.type === 'modified').length,
  }
}

/**
 * Format a value for display in diff view.
 *
 * @param value - Value to format
 * @param maxLength - Maximum string length before truncation
 * @returns Formatted string
 */
export function formatValue(value: unknown, maxLength: number = 50): string {
  if (value === undefined) return 'undefined'
  if (value === null) return 'null'

  if (typeof value === 'string') {
    if (value.length > maxLength) {
      return `"${value.substring(0, maxLength)}..."`
    }
    return `"${value}"`
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return '[]'
    if (value.length <= 3) {
      return `[${value.map((v) => formatValue(v, 20)).join(', ')}]`
    }
    return `[${value.length} items]`
  }

  if (typeof value === 'object') {
    const keys = Object.keys(value)
    if (keys.length === 0) return '{}'
    if (keys.length <= 2) {
      const pairs = keys.map((k) => `${k}: ${formatValue((value as Record<string, unknown>)[k], 20)}`)
      return `{${pairs.join(', ')}}`
    }
    return `{${keys.length} fields}`
  }

  return String(value)
}

/**
 * Get a summary of changes for display in compact view.
 *
 * @param diff - StateDiff to summarize
 * @returns Summary string
 */
export function getDiffSummary(diff: StateDiff): string {
  if (!diff.hasChanges) return 'No changes'

  const parts: string[] = []
  if (diff.addedCount > 0) parts.push(`+${diff.addedCount}`)
  if (diff.removedCount > 0) parts.push(`-${diff.removedCount}`)
  if (diff.modifiedCount > 0) parts.push(`~${diff.modifiedCount}`)

  return parts.join(' ')
}

/**
 * Get color class for a change type.
 *
 * @param type - Type of change
 * @returns Tailwind color class
 */
export function getChangeColor(type: ChangedField['type']): string {
  switch (type) {
    case 'added':
      return 'text-green-600 dark:text-green-400'
    case 'removed':
      return 'text-red-600 dark:text-red-400'
    case 'modified':
      return 'text-amber-600 dark:text-amber-400'
    default:
      return 'text-muted-foreground'
  }
}

/**
 * Get background color class for a change type.
 *
 * @param type - Type of change
 * @returns Tailwind background color class
 */
export function getChangeBgColor(type: ChangedField['type']): string {
  switch (type) {
    case 'added':
      return 'bg-green-100 dark:bg-green-900/20'
    case 'removed':
      return 'bg-red-100 dark:bg-red-900/20'
    case 'modified':
      return 'bg-amber-100 dark:bg-amber-900/20'
    default:
      return ''
  }
}

/**
 * Check if two states are equal (deep comparison).
 *
 * @param a - First state
 * @param b - Second state
 * @returns True if states are equal
 */
export function statesEqual(
  a: Record<string, unknown>,
  b: Record<string, unknown>
): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

/**
 * Extract changed field paths as a flat list.
 *
 * @param diff - StateDiff to extract from
 * @returns Array of field paths that changed
 */
export function getChangedPaths(diff: StateDiff): string[] {
  return diff.changes.map((c) => c.path)
}

/**
 * Filter diff to only include changes matching a pattern.
 *
 * @param diff - StateDiff to filter
 * @param pattern - Regex pattern to match paths
 * @returns Filtered StateDiff
 */
export function filterDiff(diff: StateDiff, pattern: RegExp): StateDiff {
  const filtered = diff.changes.filter((c) => pattern.test(c.path))
  return {
    changes: filtered,
    hasChanges: filtered.length > 0,
    addedCount: filtered.filter((c) => c.type === 'added').length,
    removedCount: filtered.filter((c) => c.type === 'removed').length,
    modifiedCount: filtered.filter((c) => c.type === 'modified').length,
  }
}
