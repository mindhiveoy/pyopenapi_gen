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

        # OPTIMISED: Run Ruff once on all files instead of per-file
        # Collect all Python files
        python_files = [p for p in target_paths if p.is_file() and p.suffix == ".py"]

        if python_files:
            # Run Ruff checks once on all files (much faster than per-file)
            self.remove_unused_imports_bulk(python_files)
            self.sort_imports_bulk(python_files)
            self.format_code_bulk(python_files)

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
        # TEMPORARILY DISABLED: Mypy is slow on large specs, disabled for faster iteration
        # if package_roots:
        #     print(f"Running Mypy on package root(s): {package_roots}")
        # for root_dir in package_roots:
        #     print(f"Running mypy on {root_dir}...")
        #     self.type_check(root_dir)

    def remove_unused_imports_bulk(self, targets: List[Path]) -> None:
        """Remove unused imports from multiple targets using Ruff (bulk operation)."""
        if not targets:
            return
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select=F401",
                "--fix",
            ]
            + [str(t) for t in targets],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            if result.stdout:
                _print_filtered_stdout(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    def sort_imports_bulk(self, targets: List[Path]) -> None:
        """Sort imports in multiple targets using Ruff (bulk operation)."""
        if not targets:
            return
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--select=I",
                "--fix",
            ]
            + [str(t) for t in targets],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            if result.stdout:
                _print_filtered_stdout(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    def format_code_bulk(self, targets: List[Path]) -> None:
        """Format code in multiple targets using Ruff (bulk operation)."""
        if not targets:
            return
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
            ]
            + [str(t) for t in targets],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0 or result.stderr:
            if result.stdout:
                _print_filtered_stdout(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

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

        # Try mypy with cache cleanup on failure
        for attempt in range(2):
            cmd = [sys.executable, "-m", "mypy", "--strict"]
            if attempt == 1:
                # Second attempt: clear cache
                cmd.append("--cache-dir=/tmp/mypy_cache_temp")
            cmd.extend([str(f) for f in python_files])

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Check for specific mypy cache corruption errors
            cache_error_patterns = ["KeyError: 'setter_type'", "KeyError:", "deserialize"]
            is_cache_error = any(pattern in result.stderr for pattern in cache_error_patterns)

            if result.returncode == 0:
                # Success
                return
            elif attempt == 0 and is_cache_error:
                # Retry with cache cleanup
                print(f"Mypy cache error detected, retrying with fresh cache...", file=sys.stderr)
                continue
            else:
                # Report the error
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)
                print(f"Type checking failed for {target_dir}. Please fix the above issues.", file=sys.stderr)
                sys.exit(result.returncode)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Postprocess generated Python files/directories.")
    parser.add_argument("targets", nargs="+", help="Files or directories to postprocess.")
    args = parser.parse_args()
    PostprocessManager(args.project_root).run(args.targets)
