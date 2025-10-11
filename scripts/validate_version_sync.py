#!/usr/bin/env python3
"""Validate that all version files are synchronised.

This script ensures that the version number is consistent across:
- pyproject.toml (project.version)
- pyproject.toml (tool.commitizen.version)
- src/pyopenapi_gen/__init__.py (__version__)

Exit codes:
    0: All versions are synchronised
    1: Version mismatch detected
    2: Script error (file not found, parse error, etc.)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple


class VersionLocation(NamedTuple):
    """Location of a version string in the codebase."""

    file: Path
    description: str
    version: str | None


def extract_pyproject_version(pyproject_path: Path) -> tuple[str | None, str | None]:
    """Extract version from pyproject.toml.

    Returns:
        Tuple of (project.version, tool.commitizen.version)
    """
    try:
        content = pyproject_path.read_text()
    except FileNotFoundError:
        print(f"❌ File not found: {pyproject_path}")
        return None, None

    # Extract project.version (line 7: version = "0.14.3")
    project_version_match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    project_version = project_version_match.group(1) if project_version_match else None

    # Extract tool.commitizen.version (line 143: version = "0.14.3")
    cz_version_match = re.search(r'^\[tool\.commitizen\].*?^version\s*=\s*"([^"]+)"', content, re.MULTILINE | re.DOTALL)
    cz_version = cz_version_match.group(1) if cz_version_match else None

    return project_version, cz_version


def extract_init_version(init_path: Path) -> str | None:
    """Extract version from __init__.py.

    Returns:
        Version string or None if not found
    """
    try:
        content = init_path.read_text()
    except FileNotFoundError:
        print(f"❌ File not found: {init_path}")
        return None

    # Extract __version__ (line 46: __version__: str = "0.14.3")
    version_match = re.search(r'^__version__\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return version_match.group(1) if version_match else None


def validate_versions() -> int:
    """Validate that all version files are synchronised.

    Returns:
        Exit code (0 = success, 1 = mismatch, 2 = error)
    """
    # Define file paths
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    init_path = project_root / "src" / "pyopenapi_gen" / "__init__.py"

    print("🔍 Validating version synchronisation across project files...")
    print()

    # Extract versions
    project_version, cz_version = extract_pyproject_version(pyproject_path)
    init_version = extract_init_version(init_path)

    # Build version locations list
    locations = [
        VersionLocation(pyproject_path, "pyproject.toml (project.version)", project_version),
        VersionLocation(pyproject_path, "pyproject.toml (tool.commitizen.version)", cz_version),
        VersionLocation(init_path, "src/pyopenapi_gen/__init__.py (__version__)", init_version),
    ]

    # Check if any version extraction failed
    if any(loc.version is None for loc in locations):
        print("❌ Failed to extract versions from one or more files:")
        for loc in locations:
            status = "✅" if loc.version else "❌"
            print(f"  {status} {loc.description}: {loc.version or 'NOT FOUND'}")
        print()
        print("This indicates a parsing error or missing version declaration.")
        return 2

    # Check if all versions match
    versions = [loc.version for loc in locations]
    if len(set(versions)) == 1:
        print("✅ All versions are synchronised:")
        for loc in locations:
            print(f"  ✅ {loc.description}: {loc.version}")
        print()
        print(f"📦 Current version: {versions[0]}")
        return 0

    # Version mismatch detected
    print("❌ Version mismatch detected:")
    print()
    for loc in locations:
        print(f"  • {loc.description}")
        print(f"    File: {loc.file}")
        print(f"    Version: {loc.version}")
    print()

    # Determine canonical version (most common)
    from collections import Counter

    version_counts = Counter(versions)
    canonical_version, _ = version_counts.most_common(1)[0]

    print(f"💡 Suggested fix: Update all files to version '{canonical_version}'")
    print()

    # Provide specific fix instructions
    for loc in locations:
        if loc.version != canonical_version:
            print(f"  ❌ {loc.description}")
            print(f"     Current: {loc.version}")
            print(f"     Expected: {canonical_version}")
            print(f"     File: {loc.file}")
            print()

    print("🔧 To fix manually:")
    print(f"  1. Edit the files above to use version '{canonical_version}'")
    print("  2. Commit with: git commit -m \"fix(version): sync version across all files\"")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(validate_versions())
