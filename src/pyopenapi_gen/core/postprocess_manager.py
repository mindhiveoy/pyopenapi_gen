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

    def __init__(self, project_root: str):
        self.project_root = project_root  # Store project root
        pass

    def run(self, targets: List[Union[str, Path]]) -> None:
        """
        Run Ruff checks on individual files, then run Mypy on the package root.
        """
        if not targets:
            return

        # Ensure all targets are Path objects
        target_paths = [Path(t) for t in targets]

        # --- RE-ENABLE RUFF CHECKS ---
        for target_path in target_paths:
            if target_path.is_file() and target_path.suffix == ".py":
                self.remove_unused_imports(target_path)
                self.sort_imports(target_path)
                self.format_code(target_path)
        # --- END RE-ENABLE ---

        # Determine the package root directory(s) for Mypy
        package_roots = set()
        for target_path in target_paths:
            if target_path.is_file():
                # Find the first ancestor directory *without* __init__.py
                # (or stop at workspace root)
                current = target_path.parent
                package_root = current
                while current != Path(self.project_root) and (current / "__init__.py").exists():
                    package_root = current
                    current = current.parent
                package_roots.add(package_root)
            elif target_path.is_dir():
                # If a directory is passed, assume it's a package root or contains packages
                # For simplicity, let's assume it *is* the root to run mypy on
                package_roots.add(target_path)

        # Run Mypy on each identified package root
        if package_roots:
            print(f"Running Mypy on package root(s): {package_roots}")
        for root_dir in package_roots:
            print(f"Running mypy on {root_dir}...")
            self.type_check(root_dir)

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

    def type_check(self, target_dir: Path) -> None:
        """Type check the target directory using mypy."""
        if not target_dir.is_dir():
            print(f"Skipping Mypy on non-directory: {target_dir}", file=sys.stderr)
            return

        print(f"Running mypy on {target_dir}...")
        # Find all Python files in the target directory
        python_files = list(target_dir.rglob("*.py"))
        if not python_files:
            print(f"No Python files found in {target_dir}, skipping type check.")
            return

        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict"] + [str(f) for f in python_files],
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
                print(f"Type checking failed for {target_dir}. Please fix the above issues.", file=sys.stderr)
                sys.exit(result.returncode)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Postprocess generated Python files/directories.")
    parser.add_argument("targets", nargs="+", help="Files or directories to postprocess.")
    args = parser.parse_args()
    PostprocessManager(args.project_root).run(args.targets)
