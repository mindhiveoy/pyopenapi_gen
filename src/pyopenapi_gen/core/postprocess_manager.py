import subprocess
import sys
from pathlib import Path
from typing import List, Union


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
        print(f"Removing unused imports for {target}...")
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
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        print(result.stderr, file=sys.stderr)

    def sort_imports(self, target: Union[str, Path]) -> None:
        """Sort imports in the target using Ruff."""
        print(f"Sorting imports for {target}...")
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
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        print(result.stderr, file=sys.stderr)

    def format_code(self, target: Union[str, Path]) -> None:
        """Format code in the target using Ruff."""
        print(f"Formatting code for {target}...")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
                str(target),
            ],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            print(f"Formatting found and fixed issues in {target}.", file=sys.stderr)
        else:
            print(f"No formatting issues found in {target}.")

    def type_check(self, target: Union[str, Path]) -> None:
        """Type check the target using mypy."""
        print(f"Type checking {target}...")
        result = subprocess.run(
            [sys.executable, "-m", "mypy", str(target), "--strict"],
            capture_output=True,
            text=True,
        )
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
    print("Post-processing complete.")
