from pathlib import Path
from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.models_emitter import ModelsEmitter
import os
import pytest


def test_models_emitter_simple(tmp_path: Path) -> None:
    # Create a simple IRSpec with one schema
    schema = IRSchema(
        name="Pet",
        type="object",
        format=None,
        required=["id", "name"],
        properties={
            "id": IRSchema(name=None, type="integer", format="int64"),
            "name": IRSchema(name=None, type="string"),
        },
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"Pet": schema}, operations=[], servers=[]
    )

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Pet.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    # Normalize whitespace for comparison
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    # Check key lines exist in output
    assert "from dataclasses import dataclass" in result
    assert "from typing import" in result
    assert "@dataclass" in result
    assert "class Pet:" in result
    assert "id:" in result
    assert "name:" in result


def test_models_emitter_enum(tmp_path: Path) -> None:
    """Test enum model generation."""
    schema = IRSchema(
        name="Status",
        type="string",
        enum=["pending", "approved", "rejected"],
        description="Status of a pet",
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"Status": schema}, operations=[], servers=[]
    )

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Status.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    # Normalize whitespace for comparison
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    # Check key lines exist in output
    assert "from enum import Enum" in result
    assert "class Status(str, Enum):" in result
    assert "PENDING" in result
    assert "APPROVED" in result
    assert "REJECTED" in result


def test_models_emitter_array(tmp_path: Path) -> None:
    """Test array type generation."""
    schema = IRSchema(
        name="PetList",
        type="object",
        properties={
            "items": IRSchema(
                name=None,
                type="array",
                items=IRSchema(
                    name=None,
                    type="object",
                    properties={
                        "id": IRSchema(name=None, type="integer"),
                        "name": IRSchema(name=None, type="string"),
                    },
                ),
            ),
        },
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"PetList": schema}, operations=[], servers=[]
    )

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "PetList.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    # Normalize whitespace for comparison
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    # Check key lines exist in output
    assert "from dataclasses import dataclass" in result
    assert "from typing import" in result
    assert "@dataclass" in result
    assert "class PetList:" in result
    assert "items: Optional[List[Dict[str, Any]]]" in result


def test_models_emitter_datetime(tmp_path: Path) -> None:
    """Test datetime type generation."""
    schema = IRSchema(
        name="Event",
        type="object",
        properties={
            "created_at": IRSchema(
                name=None,
                type="string",
                format="date-time",
            ),
            "date_only": IRSchema(
                name=None,
                type="string",
                format="date",
            ),
        },
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"Event": schema}, operations=[], servers=[]
    )

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Event.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    # Normalize whitespace for comparison
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    # Check key lines exist in output
    assert "from dataclasses import dataclass" in result
    assert "from typing import" in result
    assert "from datetime import" in result
    assert "@dataclass" in result
    assert "class Event:" in result
    assert "created_at: Optional[datetime]" in result
    assert "date_only: Optional[date]" in result


def test_models_emitter_empty_schema(tmp_path: Path) -> None:
    """Test empty schema handling."""
    schema = IRSchema(
        name="Empty",
        type="object",
        properties={},  # Empty object
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"Empty": schema}, operations=[], servers=[]
    )

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Empty.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    # Normalize whitespace for comparison
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    # Check key lines exist in output
    assert "from dataclasses import dataclass" in result
    assert "from typing import" in result
    assert "@dataclass" in result
    assert "class Empty:" in result
    assert "pass" in result


def test_models_emitter_init_file(tmp_path: Path) -> None:
    """Test __init__.py generation."""
    schemas = {
        "Pet": IRSchema(name="Pet", type="object", properties={}),
        "Order": IRSchema(name="Order", type="object", properties={}),
        "User": IRSchema(name="User", type="object", properties={}),
    }
    spec = IRSpec(title="T", version="0.1", schemas=schemas, operations=[], servers=[])

    # We're not adding the unnamed schema in this test to keep it simpler

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    init_file: Path = out_dir / "models" / "__init__.py"
    assert init_file.exists()

    content: str = init_file.read_text()

    # Simpler approach: just check that each model is mentioned in the imports
    for model in ["Pet", "Order", "User"]:
        assert f'"{model}"' in content
        assert f"from .{model} import {model}" in content


def test_models_emitter__emit_single_schema__generates_module_and_init(tmp_path):
    """
    Scenario:
        A single schema in IRSpec should produce one model file with a sanitized filename and corresponding __init__.py exports entry.

    Expected Outcome:
        - The models directory contains a file <sanitized>.py.
        - The model file defines a class matching the sanitized schema name.
        - The __init__.py file includes __all__ with the class name and an import statement.
    """
    # Arrange
    schema_name = "Test Schema"
    schema = IRSchema(
        name=schema_name,
        type="object",
        format=None,
        required=["id"],
        properties={"id": IRSchema(name=None, type="integer", format=None)},
        items=None,
        enum=None,
        description="A test schema",
    )
    spec = IRSpec(
        title="API", version="1.0.0", schemas={schema_name: schema}, operations=[]
    )
    out_dir = tmp_path / "out"

    # Act
    ModelsEmitter().emit(spec, str(out_dir))

    # Assert
    models_dir = out_dir / "models"
    assert models_dir.exists() and models_dir.is_dir(), "models directory not created"

    # Sanitized filename should be 'test_schema.py'
    module_file = models_dir / "test_schema.py"
    assert module_file.exists(), f"Expected model file {module_file} to exist"
    content = module_file.read_text()
    # Class name should be 'TestSchema'
    assert "class TestSchema" in content, "Sanitized class definition missing"

    # __init__.py checks
    init_file = models_dir / "__init__.py"
    assert init_file.exists(), "__init__.py not generated in models/"
    init_content = init_file.read_text()
    assert '__all__ = ["TestSchema"]' in init_content, "__all__ missing class name"
    assert (
        "from .test_schema import TestSchema" in init_content
    ), "Import statement missing or incorrect"
