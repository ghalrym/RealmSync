#!/usr/bin/env python3
"""
Custom linter to check for imports inside functions instead of global scope.

This script uses AST to parse Python files and detect import statements
that are inside function definitions rather than at the module level.
"""

import ast
import sys
from collections.abc import Iterator
from pathlib import Path


class ImportChecker(ast.NodeVisitor):
    """AST visitor that detects imports inside functions."""

    def __init__(self, file_path: Path, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: list[tuple[int, int, str]] = []  # (line, col, message)
        self.function_stack: list[str] = []  # Track nested functions

    def _has_noqa_comment(self, node: ast.AST) -> bool:
        """Check if the import line has a noqa comment to ignore this check."""
        line_num = node.lineno - 1  # Convert to 0-based index
        if line_num < len(self.source_lines):
            line = self.source_lines[line_num]
            # Check for # noqa: I001 or # noqa comment
            return "# noqa: I001" in line or "# noqa" in line
        return False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions and track them in the stack."""
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions and track them in the stack."""
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        """Check if import is inside a function."""
        if self.function_stack and not self._has_noqa_comment(node):
            function_name = self.function_stack[-1]
            imports = ", ".join(alias.name for alias in node.names)
            self.violations.append(
                (
                    node.lineno,
                    node.col_offset,
                    f"Import '{imports}' found inside function '{function_name}' "
                    f"(line {node.lineno}). Move to module level.",
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check if import from is inside a function."""
        if self.function_stack and not self._has_noqa_comment(node):
            function_name = self.function_stack[-1]
            module = node.module or ""
            imports = ", ".join(alias.name for alias in node.names)
            import_str = f"from {module} import {imports}" if module else f"import {imports}"
            self.violations.append(
                (
                    node.lineno,
                    node.col_offset,
                    f"Import '{import_str}' found inside function '{function_name}' "
                    f"(line {node.lineno}). Move to module level.",
                )
            )
        self.generic_visit(node)


def check_file(file_path: Path) -> list[tuple[int, int, str]]:
    """Check a single Python file for imports inside functions."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            source_lines = content.splitlines()
        tree = ast.parse(content, filename=str(file_path))
        checker = ImportChecker(file_path, source_lines)
        checker.visit(tree)
        return checker.violations
    except SyntaxError as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error checking {file_path}: {e}", file=sys.stderr)
        return []


def find_python_files(directory: Path, exclude_patterns: list[str] | None = None) -> Iterator[Path]:
    """Find all Python files in a directory, excluding certain patterns."""
    if exclude_patterns is None:
        exclude_patterns = ["__pycache__", ".git", ".venv", "venv", "build", "dist", ".eggs"]

    for path in directory.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in exclude_patterns):
            continue
        yield path


def main() -> int:
    """Main entry point for the linter."""
    import argparse  # noqa: I001 - argparse imported here to avoid importing when script is imported as module

    parser = argparse.ArgumentParser(
        description="Check for imports inside functions instead of global scope"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to check (default: current directory)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional patterns to exclude (can be specified multiple times)",
    )
    parser.add_argument(
        "--format",
        choices=["default", "ruff"],
        default="default",
        help="Output format (default: default, ruff: ruff-compatible format)",
    )

    args = parser.parse_args()

    exclude_patterns = [
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "build",
        "dist",
        ".eggs",
    ] + args.exclude

    all_violations: list[tuple[Path, int, int, str]] = []

    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            violations = check_file(path)
            for line, col, message in violations:
                all_violations.append((path, line, col, message))
        elif path.is_dir():
            for py_file in find_python_files(path, exclude_patterns):
                violations = check_file(py_file)
                for line, col, message in violations:
                    all_violations.append((py_file, line, col, message))
        else:
            print(f"Warning: {path} is not a file or directory", file=sys.stderr)

    if not all_violations:
        return 0

    # Print violations
    cwd = Path.cwd()
    for file_path, line, col, message in all_violations:
        if args.format == "ruff":
            # Ruff format: file:line:col: code: message
            try:
                rel_path = file_path.relative_to(cwd)
            except ValueError:
                rel_path = file_path
            print(f"{rel_path}:{line}:{col}: I001: {message}")
        else:
            # Default format
            try:
                rel_path = file_path.relative_to(cwd)
            except ValueError:
                rel_path = file_path
            print(f"{rel_path}:{line}:{col}: {message}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
