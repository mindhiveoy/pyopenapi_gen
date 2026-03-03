"""Tests for __init__.py generation issues.

Covers:
- Issue #299: generated __init__.py contains literal \\n instead of real newlines
- Issue #296: generated model files have circular imports
"""

import json
from pathlib import Path

import pytest

from pyopenapi_gen.generator.client_generator import ClientGenerator

# Minimal spec with one schema and one path
MINIMAL_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {
        "/items": {
            "get": {
                "operationId": "listItems",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": {"type": "array", "items": {"type": "string"}}}},
                    }
                },
            }
        }
    },
}

# Spec with mutually-referencing schemas to trigger circular import
CIRCULAR_REF_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Circular", "version": "1.0.0"},
    "paths": {},
    "components": {
        "schemas": {
            "App": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "version": {"$ref": "#/components/schemas/AppVersion"},
                },
            },
            "AppVersion": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "app": {"$ref": "#/components/schemas/App"},
                },
            },
        }
    },
}


def _write_spec(directory: Path, spec: dict) -> Path:
    spec_path = directory / "spec.json"
    spec_path.write_text(json.dumps(spec))
    return spec_path


class TestIssue299LiteralNewlines:
    """Issue #299: generated __init__.py uses literal \\n instead of real newlines."""

    def test_client_init_py__with_core_package__uses_real_newlines(self, tmp_path: Path) -> None:
        """
        Scenario:
            Generator is run with --core-package (external core), which triggers
            the rich __init__.py generation path in ClientGenerator.

        Expected Outcome:
            The generated __init__.py must contain real newline characters (0x0A),
            not the two-character literal sequence backslash-n (0x5C 0x6E).
            The file must be parseable as valid Python (i.e. not a single-line comment).
        """
        spec_path = _write_spec(tmp_path, MINIMAL_SPEC)
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=tmp_path,
            output_package="test_client.api",
            core_package="test_client.core",
            force=True,
            no_postprocess=True,
        )

        init_path = tmp_path / "test_client" / "api" / "__init__.py"
        assert init_path.exists(), "__init__.py must be generated"

        raw_bytes = init_path.read_bytes()

        # Must contain real newlines
        assert b"\n" in raw_bytes, (
            "Generated __init__.py must contain real newline characters (0x0A), "
            f"but none were found. File content repr: {raw_bytes[:200]!r}"
        )

        # Must NOT contain literal backslash-n sequences
        assert b"\\n" not in raw_bytes, (
            "Generated __init__.py must not contain literal \\\\n sequences (0x5C 0x6E), "
            f"but they were found. File content repr: {raw_bytes[:200]!r}"
        )

    def test_client_init_py__with_core_package__is_valid_python(self, tmp_path: Path) -> None:
        """
        Scenario:
            Same generation as above.

        Expected Outcome:
            The generated __init__.py can be compiled as valid Python source,
            which means it is not collapsed to a single-line comment.
        """
        spec_path = _write_spec(tmp_path, MINIMAL_SPEC)
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=tmp_path,
            output_package="test_client.api",
            core_package="test_client.core",
            force=True,
            no_postprocess=True,
        )

        init_path = tmp_path / "test_client" / "api" / "__init__.py"
        content = init_path.read_text()

        # Must compile without error
        try:
            compile(content, str(init_path), "exec")
        except SyntaxError as exc:
            pytest.fail(f"Generated __init__.py is not valid Python: {exc}\n" f"Content:\n{content[:500]}")

    def test_client_init_py__with_core_package__exports_api_client(self, tmp_path: Path) -> None:
        """
        Scenario:
            Generator is run with an external core package.

        Expected Outcome:
            The generated __init__.py must export 'APIClient' in __all__ and
            contain the import statement 'from .client import APIClient'.
        """
        spec_path = _write_spec(tmp_path, MINIMAL_SPEC)
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=tmp_path,
            output_package="test_client.api",
            core_package="test_client.core",
            force=True,
            no_postprocess=True,
        )

        content = (tmp_path / "test_client" / "api" / "__init__.py").read_text()
        assert "from .client import APIClient" in content
        assert '"APIClient"' in content


class TestIssue296CircularImports:
    """Issue #296: generated model files cause circular imports at runtime."""

    def test_model_file__with_circular_references__has_future_annotations(self, tmp_path: Path) -> None:
        """
        Scenario:
            An OpenAPI spec contains two schemas that reference each other:
            App references AppVersion, and AppVersion references App.

        Expected Outcome:
            Every generated model .py file must start with
            'from __future__ import annotations' so that Python defers
            annotation evaluation and circular imports are avoided.
        """
        spec_path = _write_spec(tmp_path, CIRCULAR_REF_SPEC)
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=tmp_path,
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        models_dir = tmp_path / "test_client" / "models"
        assert models_dir.exists(), "models/ directory must be generated"

        model_files = [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]
        assert model_files, "At least one model file must be generated"

        for model_file in model_files:
            content = model_file.read_text()
            assert "from __future__ import annotations" in content, (
                f"Model file {model_file.name} must contain "
                "'from __future__ import annotations' to prevent circular import errors. "
                f"First 300 chars:\n{content[:300]}"
            )

    def test_model_file__simple_schema__has_future_annotations(self, tmp_path: Path) -> None:
        """
        Scenario:
            A simple spec with no circular references.

        Expected Outcome:
            Even without circular references, every model file has
            'from __future__ import annotations' for consistency and safety.
        """
        spec_path = _write_spec(tmp_path, MINIMAL_SPEC)
        # Add a schema to the minimal spec
        spec_with_model = dict(MINIMAL_SPEC)
        spec_with_model["components"] = {
            "schemas": {"Item": {"type": "object", "properties": {"id": {"type": "string"}}}}
        }
        spec_path = _write_spec(tmp_path, spec_with_model)

        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=tmp_path,
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        models_dir = tmp_path / "test_client" / "models"
        if models_dir.exists():
            for model_file in models_dir.glob("*.py"):
                if model_file.name == "__init__.py":
                    continue
                content = model_file.read_text()
                assert "from __future__ import annotations" in content, (
                    f"Model file {model_file.name} must contain "
                    "'from __future__ import annotations'. "
                    f"First 300 chars:\n{content[:300]}"
                )
