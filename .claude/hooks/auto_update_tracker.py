#!/usr/bin/env python3
"""
Stop hook: Automatically update IMPLEMENTATION_TRACKER.md based on file changes.

This hook runs when Claude finishes responding. It:
1. Checks if ADR-related files were modified
2. Parses the changes to determine which ADRs were affected
3. Updates the tracker's status log
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# Mapping of module directories to ADR numbers
ADR_MODULE_MAPPING = {
    "evaluation": ["ADR-010"],
    "plugins": ["ADR-014"],
    "reasoning": ["ADR-015"],
    "memory": ["ADR-006"],
    "topology": ["ADR-005"],
    "simulation": ["ADR-009", "ADR-011"],
    "scenarios": ["ADR-009"],
    "llm": ["ADR-003"],
    "personas": ["ADR-004"],
    "persistence": ["ADR-008"],
    "api": ["ADR-012"],
    "security": ["ADR-013"],
    "cli": ["UI-ADR-005"],
}


def get_recent_changes(project_dir: Path) -> dict[str, list[str]]:
    """
    Get ADRs with recent file changes from the change log.

    Returns: Dict of ADR -> list of changed files
    """
    log_file = project_dir / ".claude" / "adr_changes.log"

    if not log_file.exists():
        return {}

    adr_files: dict[str, list[str]] = {}

    try:
        with open(log_file) as f:
            lines = f.readlines()

        # Get entries from last hour
        now = datetime.utcnow()
        hour_ago = now.timestamp() - 3600

        for line in lines:
            parts = line.strip().split("|")
            if len(parts) >= 3:
                timestamp_str, adr_str, file_path = parts[0], parts[1], parts[2]
                try:
                    # Parse ISO timestamp
                    ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if ts.timestamp() > hour_ago:
                        for adr in adr_str.split(","):
                            adr = adr.strip()
                            if adr not in adr_files:
                                adr_files[adr] = []
                            if file_path not in adr_files[adr]:
                                adr_files[adr].append(file_path)
                except (ValueError, TypeError):
                    continue

    except Exception as e:
        print(f"Error reading change log: {e}", file=sys.stderr)

    return adr_files


def update_tracker_log(project_dir: Path, adr_changes: dict[str, list[str]]) -> bool:
    """
    Update the status log in IMPLEMENTATION_TRACKER.md.

    Returns: True if tracker was updated
    """
    tracker_path = project_dir / "adrs" / "IMPLEMENTATION_TRACKER.md"

    if not tracker_path.exists():
        return False

    if not adr_changes:
        return False

    try:
        content = tracker_path.read_text()
        today = datetime.now().strftime("%Y-%m-%d")

        # Format the ADRs that changed
        adrs_str = ", ".join(sorted(adr_changes.keys()))
        file_count = sum(len(files) for files in adr_changes.values())

        # Check if we already have an entry for today's hook update
        log_marker = f"| {today} | - | Auto-tracked:"
        if log_marker in content:
            # Already logged today
            return False

        # Create the new log entry
        log_entry = f"| {today} | - | Auto-tracked: {adrs_str} ({file_count} files modified) | Hook |\n"

        # Find the status log section and append
        if "## Appendix C: Status Update Log" in content:
            # Find the last line of the table (before any trailing content)
            lines = content.split("\n")
            insert_idx = None

            for i, line in enumerate(lines):
                if "## Appendix C: Status Update Log" in line:
                    # Find the end of the table
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("|"):
                            insert_idx = j + 1
                        elif insert_idx is not None and not lines[j].startswith("|"):
                            break

            if insert_idx is not None:
                lines.insert(insert_idx, log_entry.rstrip())
                tracker_path.write_text("\n".join(lines))
                return True

    except Exception as e:
        print(f"Error updating tracker: {e}", file=sys.stderr)

    return False


def clear_processed_changes(project_dir: Path) -> None:
    """Clear the change log after processing."""
    log_file = project_dir / ".claude" / "adr_changes.log"

    try:
        if log_file.exists():
            # Keep the log but mark entries as processed
            # For now, just truncate old entries
            with open(log_file) as f:
                lines = f.readlines()

            # Keep only last 20 entries for history
            if len(lines) > 20:
                with open(log_file, "w") as f:
                    f.writelines(lines[-20:])
    except Exception:
        pass


def main():
    """Main hook entry point."""
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    # Don't run if we're already in a stop hook chain
    if hook_input.get("stop_hook_active"):
        print('{"decision": "allow"}')
        return 0

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    # Get recent ADR changes
    adr_changes = get_recent_changes(project_dir)

    if adr_changes:
        # Update the tracker
        updated = update_tracker_log(project_dir, adr_changes)

        if updated:
            adrs_str = ", ".join(sorted(adr_changes.keys()))
            result = {
                "reason": f"Auto-updated tracker for: {adrs_str}"
            }
            # Clear processed changes
            clear_processed_changes(project_dir)
            print(json.dumps(result))
            return 0

    print('{}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
