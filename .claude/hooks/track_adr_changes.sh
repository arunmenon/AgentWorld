#!/bin/bash
# Track ADR-related file changes and log them
# Triggered by PostToolUse on Edit|Write operations

set -e

# Read JSON input from stdin
INPUT=$(cat)

# Extract file path from the tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [ -z "$FILE_PATH" ]; then
    echo '{}'
    exit 0
fi

# Function to get ADR for a module
get_adr_for_module() {
    local module="$1"
    case "$module" in
        evaluation) echo "ADR-010" ;;
        plugins) echo "ADR-014" ;;
        reasoning) echo "ADR-015" ;;
        memory) echo "ADR-006" ;;
        topology) echo "ADR-005" ;;
        simulation) echo "ADR-009,ADR-011" ;;
        scenarios) echo "ADR-009" ;;
        llm) echo "ADR-003" ;;
        personas) echo "ADR-004" ;;
        persistence) echo "ADR-008" ;;
        api) echo "ADR-012" ;;
        security) echo "ADR-013" ;;
        cli) echo "UI-ADR-005" ;;
        *) echo "" ;;
    esac
}

# Extract module name from path like /agentworld/evaluation/file.py
MODULE=$(echo "$FILE_PATH" | grep -oE '/agentworld/[^/]+/' | sed 's|/agentworld/||' | sed 's|/||')

if [ -n "$MODULE" ]; then
    ADR=$(get_adr_for_module "$MODULE")

    if [ -n "$ADR" ]; then
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

        # Ensure hooks directory exists
        mkdir -p "$PROJECT_DIR/.claude"

        # Log the change
        LOG_FILE="$PROJECT_DIR/.claude/adr_changes.log"
        echo "$TIMESTAMP|$ADR|$FILE_PATH" >> "$LOG_FILE"

        echo "{\"reason\": \"Tracked change to $ADR module: $FILE_PATH\"}"
        exit 0
    fi
fi

echo '{}'
exit 0
