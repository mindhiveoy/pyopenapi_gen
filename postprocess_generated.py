import subprocess
import sys
from pathlib import Path

GENERATED_DIR = Path("generated")


def run_mypy() -> None:
    print("Running mypy for type checking...")
    result = subprocess.run(
        [sys.executable, "-m", "mypy", str(GENERATED_DIR), "--strict"],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print("Type checking failed. Please fix the above issues.", file=sys.stderr)
        sys.exit(result.returncode)


def run_ruff() -> None:
    print("Removing unused imports with ruff...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select=F401",
            "--fix",
            str(GENERATED_DIR),
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)

    print("Sorting imports with ruff...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--select=I",
            "--fix",
            str(GENERATED_DIR),
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)

    print("Formatting code with ruff...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            str(GENERATED_DIR),
        ],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        print("Ruff found and fixed issues.", file=sys.stderr)
    else:
        print("No issues found by Ruff.")


if __name__ == "__main__":
    run_ruff()
    run_mypy()
    print("Post-processing complete.")
