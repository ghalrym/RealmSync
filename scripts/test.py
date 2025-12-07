#!/usr/bin/env python3
"""Script to run tests with coverage."""

import subprocess
import sys
from pathlib import Path


def main():
    """Main entry point for test script."""
    # Ensure we're running from the project root
    # Get the directory containing this file (scripts/)
    script_dir = Path(__file__).parent
    # Go up one level to get project root
    project_root = script_dir.parent

    # Build pytest command - use subprocess to ensure proper coverage calculation
    # pytest.ini_options.addopts already includes coverage options
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov-fail-under=95",
    ] + sys.argv[1:]

    # Run pytest as subprocess to ensure coverage is calculated correctly
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
