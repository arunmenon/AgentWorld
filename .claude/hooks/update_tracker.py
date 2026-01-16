#!/usr/bin/env python3
"""
Hook script to update IMPLEMENTATION_TRACKER.md based on ADR compliance results.

This script is triggered by:
- SubagentStop: After adr-compliance-checker agent completes
- Stop: When Claude finishes responding (checks if ADR work was done)

Input (via stdin): JSON with hook event data
Output: JSON with decision and optional message
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def get_project_dir() -> Path:
    """Get the project directory from environment or cwd."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def parse_compliance_from_transcript(transcript_path: str) -> dict[str, int]:
    """
    Parse the transcript to find ADR compliance percentages.

    Returns dict like: {"ADR-010": 100, "ADR-014": 98, "ADR-015": 99}
    """
    compliance_scores = {}

    try:
        with open(transcript_path, 'r') as f:
            content = f.read()

        # Look for patterns like "ADR-010: 100%" or "ADR-014 Compliance: 98%"
        patterns = [
            r'ADR-(\d+)[:\s]+(\d+)%',
            r'ADR-(\d+)\s+.*?(\d+)%\s+compliance',
            r'Overall Compliance[:\s]+(\d+)%',
            r'Compliance Score[:\s]+(\d+)%',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    adr_num, score = match
                    compliance_scores[f"ADR-{adr_num.zfill(3)}"] = int(score)

    except Exception as e:
        print(f"Error parsing transcript: {e}", file=sys.stderr)

    return compliance_scores


def detect_adr_work_from_files(project_dir: Path) -> list[str]:
    """
    Detect which ADR-related modules have been recently modified.

    Returns list of ADR numbers that may need tracker updates.
    """
    adr_module_mapping = {
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
    }

    affected_adrs = set()
    src_dir = project_dir / "src" / "agentworld"

    if not src_dir.exists():
        return []

    # Check for recently modified files (within last hour)
    now = datetime.now().timestamp()
    hour_ago = now - 3600

    for module, adrs in adr_module_mapping.items():
        module_dir = src_dir / module
        if module_dir.exists():
            for py_file in module_dir.glob("*.py"):
                if py_file.stat().st_mtime > hour_ago:
                    affected_adrs.update(adrs)
                    break

    return sorted(affected_adrs)


def update_tracker(project_dir: Path, adr_updates: dict[str, dict]) -> bool:
    """
    Update the IMPLEMENTATION_TRACKER.md with new ADR status.

    Args:
        project_dir: Path to project root
        adr_updates: Dict of ADR number -> {compliance: int, status: str}

    Returns:
        True if tracker was updated, False otherwise
    """
    tracker_path = project_dir / "adrs" / "IMPLEMENTATION_TRACKER.md"

    if not tracker_path.exists():
        print(f"Tracker not found: {tracker_path}", file=sys.stderr)
        return False

    try:
        content = tracker_path.read_text()
        updated = False

        for adr, info in adr_updates.items():
            compliance = info.get("compliance", 0)

            # Determine status icon based on compliance
            if compliance >= 95:
                new_status = "🟢"
            elif compliance >= 70:
                new_status = "🟡"
            else:
                new_status = "🔴"

            # Update status icons in component tables
            # Pattern: | Component | 🔴 | ... for this ADR section
            # This is complex - we'd need to parse the markdown structure

            # For now, just update the status log with a new entry
            updated = True

        if updated:
            # Add entry to status log
            today = datetime.now().strftime("%Y-%m-%d")
            log_entry = f"| {today} | - | ADR compliance check triggered via hook | Hook |\n"

            # Find the status log table and append
            if "## Appendix C: Status Update Log" in content:
                # Don't duplicate entries for same day
                if f"| {today} |" not in content.split("## Appendix C")[-1]:
                    # Insert before the last line of the table
                    content = content.rstrip() + "\n" + log_entry
                    tracker_path.write_text(content)
                    return True

    except Exception as e:
        print(f"Error updating tracker: {e}", file=sys.stderr)

    return False


def main():
    """Main hook entry point."""
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    event_name = hook_input.get("hook_event_name", "")
    project_dir = get_project_dir()

    result = {
        "decision": "allow",
        "reason": "Tracker check completed"
    }

    # Handle SubagentStop - check if it was an ADR compliance checker
    if event_name == "SubagentStop":
        transcript_path = hook_input.get("transcript_path", "")
        if transcript_path:
            compliance_scores = parse_compliance_from_transcript(transcript_path)
            if compliance_scores:
                adr_updates = {
                    adr: {"compliance": score}
                    for adr, score in compliance_scores.items()
                }
                if update_tracker(project_dir, adr_updates):
                    result["reason"] = f"Updated tracker with compliance: {compliance_scores}"

    # Handle Stop - check if ADR work was done in this session
    elif event_name == "Stop":
        affected_adrs = detect_adr_work_from_files(project_dir)
        if affected_adrs:
            result["reason"] = f"ADR-related modules modified: {affected_adrs}"
            # Could trigger a compliance check here, but that might be too aggressive

    # Output result
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
