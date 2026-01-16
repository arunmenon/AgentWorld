#!/usr/bin/env python
"""
Phase 1 Verification Script

Run this script to verify Phase 1 is complete.
Exit code 0 = all checks pass
Exit code 1 = one or more checks failed

Usage:
    python scripts/verify_phase1.py
"""

import subprocess
import sys
import json
from pathlib import Path


class PhaseVerifier:
    def __init__(self):
        self.checks = []
        self.failed = False

    def run(self, cmd: str, timeout: int = 60) -> tuple[bool, str, str]:
        """Run a command and return (success, stdout, stderr)."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)

    def check(self, name: str, condition: bool, error_msg: str = ""):
        """Record a check result."""
        self.checks.append((name, condition, error_msg))
        if not condition:
            self.failed = True

    def report(self) -> int:
        """Print results and return exit code."""
        print("\n" + "=" * 60)
        print("PHASE 1 VERIFICATION RESULTS")
        print("=" * 60)

        for name, passed, error in self.checks:
            status = "\u2713" if passed else "\u2717"
            print(f"  {status} {name}")
            if not passed and error:
                # Truncate long errors
                error_short = error[:200] + "..." if len(error) > 200 else error
                print(f"      Error: {error_short}")

        print("=" * 60)
        if self.failed:
            print("\u2717 PHASE 1 INCOMPLETE")
            return 1
        else:
            print("\u2713 PHASE 1 COMPLETE")
            return 0


def main():
    v = PhaseVerifier()
    project_root = Path(__file__).parent.parent

    print("Verifying Phase 1 implementation...")
    print(f"Project root: {project_root}")

    # Check 1: Package can be imported
    print("\n[1/8] Checking package imports...")
    ok, out, err = v.run("python -c \"from agentworld import Agent, Simulation, TraitVector\"")
    v.check("Package imports work", ok, err)

    # Check 2: CLI exists and shows help
    print("[2/8] Checking CLI installation...")
    ok, out, err = v.run("python -m agentworld --help")
    v.check("CLI --help works", ok and "agentworld" in out.lower(), err)

    # Check 3: Example config exists
    print("[3/8] Checking example config...")
    example_path = project_root / "examples" / "two_agents.yaml"
    v.check("Example config exists", example_path.exists(), f"Not found: {example_path}")

    # Check 4: Can parse example config
    print("[4/8] Checking config parsing...")
    ok, out, err = v.run(
        f"python -c \""
        f"from agentworld.cli.config import load_simulation_config; "
        f"c = load_simulation_config('{example_path}'); "
        f"print(c.name)\""
    )
    v.check("Config parsing works", ok and "Two Agents" in out, err)

    # Check 5: TraitVector works
    print("[5/8] Checking trait system...")
    ok, out, err = v.run(
        "python -c \""
        "from agentworld.personas.traits import TraitVector; "
        "t = TraitVector(openness=0.8); "
        "print(t.to_prompt_description())\""
    )
    v.check("TraitVector works", ok, err)

    # Check 6: Database initializes
    print("[6/8] Checking database...")
    ok, out, err = v.run(
        "python -c \""
        "from agentworld.persistence.database import init_db; "
        "init_db(in_memory=True); "
        "print('OK')\""
    )
    v.check("Database initializes", ok and "OK" in out, err)

    # Check 7: Repository works
    print("[7/8] Checking repository...")
    ok, out, err = v.run(
        "python -c \""
        "from agentworld.persistence.database import init_db; "
        "from agentworld.persistence.repository import Repository; "
        "init_db(in_memory=True); "
        "r = Repository(); "
        "sims = r.list_simulations(); "
        "print(f'Found {len(sims)} simulations')\""
    )
    v.check("Repository works", ok, err)

    # Check 8: LLM provider loads (doesn't need API key)
    print("[8/8] Checking LLM provider...")
    ok, out, err = v.run(
        "python -c \""
        "from agentworld.llm.provider import LLMProvider; "
        "p = LLMProvider(); "
        "print(f'Default model: {p.default_model}')\""
    )
    v.check("LLM provider initializes", ok, err)

    return v.report()


if __name__ == "__main__":
    sys.exit(main())
