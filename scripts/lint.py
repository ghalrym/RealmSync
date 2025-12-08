#!/usr/bin/env python3
"""Script to run all linting checks."""

import subprocess
import sys
from pathlib import Path


def main():
    """Main entry point for lint script."""
    # Ensure we're running from the project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Run ruff check (linting)
    print("Running ruff check...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=project_root,
    )
    if result.returncode != 0:
        print("[FAIL] ruff check failed")
        print("\n[FAIL] Linting failed. Please fix the issues above.")
        sys.exit(1)

    # Run ruff format (formatting check)
    print("\nRunning ruff format (check mode)...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", "."],
        cwd=project_root,
    )
    if result.returncode != 0:
        print("[FAIL] ruff format check failed")
        print("\n[FAIL] Linting failed. Please fix the issues above.")
        sys.exit(1)

    # Run mypy (non-blocking)
    print("\nRunning mypy...")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "realm_sync_api"],
        cwd=project_root,
    )
    if result.returncode != 0:
        print("[WARN] mypy found issues (non-blocking)")

    # Run check-imports
    print("\nRunning check-imports...")
    result = subprocess.run(
        [
            "rs-imports",
            ".",
            "--exclude",
            "htmlcov",
            "--exclude",
            "dist",
            "--exclude",
            "scripts",
        ],
        cwd=project_root,
    )
    if result.returncode != 0:
        print("[FAIL] check-imports failed")
        print("\n[FAIL] Linting failed. Please fix the issues above.")
        sys.exit(1)

    # All checks passed
    print("\n[PASS] All linting checks passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
