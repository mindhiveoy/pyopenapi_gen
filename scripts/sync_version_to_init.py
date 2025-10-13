#!/usr/bin/env python3
"""Sync version from pyproject.toml to __init__.py.

This script reads the version from pyproject.toml (project.version) and
updates src/pyopenapi_gen/__init__.py (__version__) to match.

This is used after semantic-release updates pyproject.toml to ensure
the __init__.py version stays in sync.

Exit codes:
    0: Success (version synced or already in sync)
    1: Error (file not found, parse error, etc.)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_pyproject_version(pyproject_path: Path) -> str | None:
    """Extract version from pyproject.toml.

    Returns:
        Version string or None if not found
    """
    try:
        content = pyproject_path.read_text()
    except FileNotFoundError:
        print(f"❌ File not found: {pyproject_path}")
        return None

    # Extract project.version (line 7: version = "0.15.0")
    project_version_match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return project_version_match.group(1) if project_version_match else None


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

    # Extract __version__ (line 53: __version__: str = "0.15.0")
    version_match = re.search(r'^__version__\s*:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return version_match.group(1) if version_match else None


def update_init_version(init_path: Path, new_version: str) -> bool:
    """Update version in __init__.py.

    Args:
        init_path: Path to __init__.py
        new_version: New version string

    Returns:
        True if updated successfully, False otherwise
    """
    try:
        content = init_path.read_text()
    except FileNotFoundError:
        print(f"❌ File not found: {init_path}")
        return False

    # Replace version with new version
    new_content = re.sub(
        r'^(__version__\s*:\s*str\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        content,
        flags=re.MULTILINE,
    )

    if new_content == content:
        print(f"⚠️  No version pattern found in {init_path}")
        return False

    # Write updated content
    try:
        init_path.write_text(new_content)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"❌ Failed to write {init_path}: {e}")
        return False


def sync_version() -> int:
    """Sync version from pyproject.toml to __init__.py.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    # Define file paths
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    init_path = project_root / "src" / "pyopenapi_gen" / "__init__.py"

    print("🔄 Syncing version from pyproject.toml to __init__.py...")
    print()

    # Extract versions
    pyproject_version = extract_pyproject_version(pyproject_path)
    init_version = extract_init_version(init_path)

    if pyproject_version is None:
        print("❌ Failed to extract version from pyproject.toml")
        return 1

    if init_version is None:
        print("❌ Failed to extract version from __init__.py")
        return 1

    print(f"📦 pyproject.toml version: {pyproject_version}")
    print(f"📦 __init__.py version: {init_version}")
    print()

    # Check if already in sync
    if pyproject_version == init_version:
        print("✅ Versions already in sync!")
        return 0

    # Update __init__.py
    print(f"🔧 Updating __init__.py to version {pyproject_version}...")
    if update_init_version(init_path, pyproject_version):
        print(f"✅ Successfully updated __init__.py to version {pyproject_version}")
        return 0

    print("❌ Failed to update __init__.py")
    return 1


if __name__ == "__main__":
    sys.exit(sync_version())
