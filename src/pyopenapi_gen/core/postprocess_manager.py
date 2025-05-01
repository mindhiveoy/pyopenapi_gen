import subprocess
import sys
from pathlib import Path
from typing import List, Union

SUCCESS_LINE = "Success: no issues found in 1 source file"


def _print_filtered_stdout(stdout: str) -> None:
    lines = [line for line in stdout.splitlines() if line.strip() and line.strip() != SUCCESS_LINE]
    if lines:
        print("\n".join(lines))


class PostprocessManager:
    """
    Handles post-processing of generated Python files: import cleanup, formatting, and type checking.
    Can be used programmatically or as a script.
    """

    def __init__(self) -> None:
        pass

    def run(self, targets: List[Union[str, Path]]) -> None:
        """
        For each target (file or directory), remove unused imports, sort imports, format code, and type check.
        """
        for target in targets:
            self.remove_unused_imports(target)
            self.sort_imports(target)
            self.format_code(target)
        for target in targets:
            self.type_check(target)

    def remove_unused_imports(self, target: Union[str, Path]) -> None:
        """Remove unused imports from the target using Ruff."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select=F401",
                "--fix",
                str(target),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            if result.stdout:
                _print_filtered_stdout(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    def sort_imports(self, target: Union[str, Path]) -> None:
        """Sort imports in the target using Ruff."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select=I",
                "--fix",
                str(target),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            if result.stdout:
                _print_filtered_stdout(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    def format_code(self, target: Union[str, Path]) -> None:
        """Format code in the target using Ruff."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
                str(target),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            if result.stdout:
                _print_filtered_stdout(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            print(f"Formatting found and fixed issues in {target}.", file=sys.stderr)

    def type_check(self, target: Union[str, Path]) -> None:
        """Type check the target using mypy."""
        result = subprocess.run(
            [sys.executable, "-m", "mypy", str(target), "--strict"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.stdout or result.stderr or result.returncode != 0:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            if result.returncode != 0:
                print(f"Type checking failed for {target}. Please fix the above issues.", file=sys.stderr)
                sys.exit(result.returncode)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Postprocess generated Python files/directories.")
    parser.add_argument("targets", nargs="+", help="Files or directories to postprocess.")
    args = parser.parse_args()
    PostprocessManager().run(args.targets)
