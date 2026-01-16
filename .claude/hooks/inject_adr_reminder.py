#!/usr/bin/env python3
"""
UserPromptSubmit hook: Inject ADR tracker reminder when working on ADRs.

When user prompts mention ADR work, this hook adds a reminder to update
the implementation tracker after the work is complete.
"""

import json
import os
import re
import sys
from pathlib import Path


def get_pending_adr_changes() -> list[str]:
    """Get list of ADRs with recent changes from the log."""
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    log_file = project_dir / ".claude" / "adr_changes.log"

    if not log_file.exists():
        return []

    try:
        with open(log_file) as f:
            lines = f.readlines()[-100:]  # Last 100 entries

        adrs = set()
        for line in lines:
            parts = line.strip().split("|")
            if len(parts) >= 2:
                # Handle comma-separated ADRs like "ADR-009,ADR-011"
                for adr in parts[1].split(","):
                    adrs.add(adr.strip())

        return sorted(adrs)
    except Exception:
        return []


def prompt_mentions_adr(prompt: str) -> bool:
    """Check if the prompt mentions ADR-related work."""
    adr_patterns = [
        r'\bADR[-\s]?\d+\b',
        r'\bimplementation\s+tracker\b',
        r'\bcompliance\s+check\b',
        r'\bfix\s+.*\bgaps?\b',
        r'\bimplement\s+.*\b(evaluation|plugin|reasoning|memory|topology)\b',
    ]

    prompt_lower = prompt.lower()
    return any(re.search(pattern, prompt_lower, re.IGNORECASE) for pattern in adr_patterns)


def main():
    """Main hook entry point."""
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print('{}')
        return 0

    prompt = hook_input.get("prompt", "")

    # Check if this is ADR-related work
    if prompt_mentions_adr(prompt):
        pending_adrs = get_pending_adr_changes()

        # Build the context injection
        context_parts = []

        if pending_adrs:
            context_parts.append(
                f"<adr-tracker-context>\n"
                f"Recent changes detected in ADR modules: {', '.join(pending_adrs)}\n"
                f"Remember to update adrs/IMPLEMENTATION_TRACKER.md after completing ADR work.\n"
                f"</adr-tracker-context>"
            )

        if context_parts:
            # Inject context via additionalContext
            result = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": "\n".join(context_parts)
                }
            }
            print(json.dumps(result))
            return 0

    print('{}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
