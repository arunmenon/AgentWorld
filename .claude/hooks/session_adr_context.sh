#!/bin/bash
# SessionStart hook: Check for pending ADR tracker updates
# Provides context about which ADRs may need tracker updates

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
LOG_FILE="$PROJECT_DIR/.claude/adr_changes.log"
TRACKER_FILE="$PROJECT_DIR/adrs/IMPLEMENTATION_TRACKER.md"

# Check if there are recent ADR changes not yet reflected in tracker
if [ -f "$LOG_FILE" ]; then
    # Get unique ADRs changed in the last session
    RECENT_ADRS=$(tail -50 "$LOG_FILE" 2>/dev/null | cut -d'|' -f2 | sort -u | tr '\n' ' ')

    if [ -n "$RECENT_ADRS" ]; then
        echo "{\"reason\": \"Recent ADR changes detected: $RECENT_ADRS - Consider updating IMPLEMENTATION_TRACKER.md\"}"
        exit 0
    fi
fi

echo '{}'
exit 0
