from pathlib import Path

from pyopenapi_gen import IRSchema, IRSpec, HTTPMethod, IROperation, IRResponse
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


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
    spec = IRSpec(title="T", version="0.1", schemas={"Pet": schema}, operations=[], servers=[])

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
    assert "id: int" in result
    assert "name: str" in result


def test_models_emitter_enum(tmp_path: Path) -> None:
    """Test enum model generation."""
    schema = IRSchema(
        name="Status",
        type="string",
        enum=["pending", "approved", "rejected"],
        description="Status of a pet",
    )
    spec = IRSpec(title="T", version="0.1", schemas={"Status": schema}, operations=[], servers=[])

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
    spec = IRSpec(title="T", version="0.1", schemas={"PetList": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "pet_list.py"
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
    spec = IRSpec(title="T", version="0.1", schemas={"Event": schema}, operations=[], servers=[])

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
    spec = IRSpec(title="T", version="0.1", schemas={"Empty": schema}, operations=[], servers=[])

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
    assert "# No properties defined in schema" in result
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
        assert f"from .{NameSanitizer.sanitize_module_name(model)} import {model}" in content


def test_models_emitter__emit_single_schema__generates_module_and_init(tmp_path: Path) -> None:
    """
    Scenario:
        A single schema in IRSpec should produce one model file with a sanitized filename and
        corresponding __init__.py exports entry.

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
    spec = IRSpec(title="API", version="1.0.0", schemas={schema_name: schema}, operations=[])
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
    assert (
        '__all__ = ["TestSchema"]' in init_content or '__all__: list[str] = ["TestSchema"]' in init_content
    ), "__all__ missing class name"
    assert (
        f"from .{NameSanitizer.sanitize_module_name(schema_name)} import TestSchema" in init_content
    ), "Import statement missing or incorrect"


def test_models_emitter__primitive_alias(tmp_path: Path) -> None:
    """
    Scenario:
        A named primitive schema should emit a type alias (e.g., MyString = str).
    Expected Outcome:
        The generated file contains the correct alias and import.
    """
    schema = IRSchema(name="MyString", type="string")
    spec = IRSpec(
        title="T",
        version="0.1",
        schemas={"MyString": schema},
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    ModelsEmitter().emit(spec, str(out_dir))
    model_file = out_dir / "models" / "my_string.py"
    assert model_file.exists()
    content = model_file.read_text()
    assert "MyString = str" in content


def test_models_emitter__array_of_primitives_alias(tmp_path: Path) -> None:
    """
    Scenario:
        A named array-of-primitive schema should emit a List alias (e.g., MyStrings = List[str]).
    Expected Outcome:
        The generated file contains the correct alias and import.
    """
    schema = IRSchema(name="MyStrings", type="array", items=IRSchema(name=None, type="string"))
    spec = IRSpec(
        title="T",
        version="0.1",
        schemas={"MyStrings": schema},
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    ModelsEmitter().emit(spec, str(out_dir))
    model_file = out_dir / "models" / "my_strings.py"
    assert model_file.exists()
    content = model_file.read_text()
    assert "MyStrings = List[str]" in content
    assert "List" in content and "from typing" in content


def test_models_emitter__array_of_models_alias(tmp_path: Path) -> None:
    """
    Scenario:
        A named array-of-model schema should emit a List[Model] alias and import the model.
    Expected Outcome:
        The generated file contains the correct alias and import.
    """
    item_schema = IRSchema(name="Pet", type="object", properties={})
    schema = IRSchema(name="PetList", type="array", items=item_schema)
    spec = IRSpec(
        title="T",
        version="0.1",
        schemas={"Pet": item_schema, "PetList": schema},
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    ModelsEmitter().emit(spec, str(out_dir))
    model_file = out_dir / "models" / "pet_list.py"
    assert model_file.exists()
    content = model_file.read_text()
    assert "PetList = List[Pet]" in content
    assert "from .Pet import Pet" in content or "from .pet import Pet" in content


def test_models_emitter__integer_enum(tmp_path: Path) -> None:
    """
    Scenario:
        A named integer enum schema should emit an Enum class.
    Expected Outcome:
        The generated file contains the correct Enum class and values.
    """
    schema = IRSchema(
        name="StatusCode",
        type="integer",
        enum=[200, 404, 500],
        description="HTTP status codes",
    )
    spec = IRSpec(
        title="T",
        version="0.1",
        schemas={"StatusCode": schema},
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    ModelsEmitter().emit(spec, str(out_dir))
    model_file = out_dir / "models" / "status_code.py"
    assert model_file.exists()
    content = model_file.read_text()
    assert "from enum import Enum" in content
    assert "class StatusCode(int, Enum):" in content or "class StatusCode(Enum):" in content
    assert "200 = 200" in content or "_200 = 200" in content
    assert "404 = 404" in content or "_404 = 404" in content
    assert "500 = 500" in content or "_500 = 500" in content


def test_models_emitter__unnamed_schema_skipped(tmp_path: Path) -> None:
    """
    Scenario:
        A schema with no name should be skipped and not generate a file.
    Expected Outcome:
        No file is generated for the unnamed schema.
    """
    schema = IRSchema(name=None, type="string")
    spec = IRSpec(title="T", version="0.1", schemas={"": schema}, operations=[], servers=[])
    out_dir = tmp_path / "out"
    ModelsEmitter().emit(spec, str(out_dir))
    model_file = out_dir / "models" / ".py"
    assert not model_file.exists()


def test_models_emitter__unknown_type_fallback(tmp_path: Path) -> None:
    """
    Scenario:
        A schema with an unknown type should be skipped (fallback logic).
    Expected Outcome:
        No file is generated for the unknown type schema.
    """
    schema = IRSchema(name="Mystery", type="unknown")
    spec = IRSpec(title="T", version="0.1", schemas={"Mystery": schema}, operations=[], servers=[])
    out_dir = tmp_path / "out"
    ModelsEmitter().emit(spec, str(out_dir))
    model_file = out_dir / "models" / "Mystery.py"
    assert not model_file.exists()


def test_models_emitter__optional_any_field__emits_all_typing_imports(tmp_path: Path) -> None:
    """
    Scenario:
        A model schema has a field with type 'object' (maps to Any) and is not required (maps to Optional[Any]).
        We want to verify that the generated model file includes both 'Optional' and 'Any' in the typing import.

    Expected Outcome:
        The generated file should have a line 'from typing import Optional, Any' (order may vary),
        and the field should be annotated as 'Optional[Any]'.
    """
    # Arrange
    schema = IRSchema(
        name="TestModel",
        type="object",
        required=["id"],
        properties={
            "id": IRSchema(name=None, type="string"),
            "meta": IRSchema(name=None, type="object"),  # not required, so Optional[Any]
        },
    )
    spec = IRSpec(
        title="T",
        version="0.1",
        schemas={"TestModel": schema},
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    emitter = ModelsEmitter()
    # Act
    emitter.emit(spec, str(out_dir))
    model_file = out_dir / "models" / "test_model.py"
    assert model_file.exists()
    content = model_file.read_text()
    # Assert
    assert "from typing import" in content
    assert "Optional" in content
    assert "Any" in content
    assert "meta: Optional[Any] = field(default_factory=dict)" in content


def test_models_emitter__inline_response_schema__generates_model(tmp_path: Path) -> None:
    """
    Scenario:
        The IRSpec contains a schema for an inline response (e.g., ListenEventsResponse) that
        was not in components/schemas. The model emitter should generate a dataclass for this
        inline response schema.

    Expected Outcome:
        - A model file is generated for ListenEventsResponse in the models directory
        - The file contains a dataclass definition for ListenEventsResponse
    """

    from pyopenapi_gen import IRSchema, IRSpec
    from pyopenapi_gen.emitters.models_emitter import ModelsEmitter

    # Simulate an inline response schema named ListenEventsResponse
    schema = IRSchema(
        name="ListenEventsResponse",
        type="object",
        properties={
            "data": IRSchema(name=None, type="object"),
            "event": IRSchema(name=None, type="string"),
            "id": IRSchema(name=None, type="string"),
        },
        required=["data", "event", "id"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        schemas={"ListenEventsResponse": schema},
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))
    model_file = out_dir / "models" / "listen_events_response.py"
    assert model_file.exists(), "Model file for ListenEventsResponse not generated"
    content = model_file.read_text()
    assert "@dataclass" in content
    assert "class ListenEventsResponse" in content
    assert "data:" in content
    assert "event:" in content
    assert "id:" in content


def test_models_emitter_optional_list_factory(tmp_path: Path) -> None:
    """
    Scenario:
        - A schema has an optional property of type array.
    Expected Outcome:
        - The generated dataclass field uses `Optional[List[...]]`.
        - The field defaults to `field(default_factory=list)`.
    """
    # Arrange
    item_schema = IRSchema(name=None, type="string")
    schema = IRSchema(
        name="DataHolder",
        type="object",
        required=[],  # tags is optional
        properties={"tags": IRSchema(name=None, type="array", items=item_schema)},
    )
    spec = IRSpec(title="T", version="0.1", schemas={"DataHolder": schema}, operations=[])
    out_dir = tmp_path / "out"

    # Act
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    # Assert
    model_file = out_dir / "models" / "data_holder.py"
    assert model_file.exists()
    content = model_file.read_text()

    # Check for Optional and List in the typing import line (order independent)
    typing_import_line = next((line for line in content.splitlines() if line.startswith("from typing import")), None)
    assert typing_import_line is not None
    assert "Optional" in typing_import_line
    assert "List" in typing_import_line

    assert "tags: Optional[List[str]] = field(default_factory=list)" in content


def test_models_emitter_optional_named_object_none_default(tmp_path: Path) -> None:
    """
    Scenario:
        - A schema has an optional property that is a reference to another named schema.
    Expected Outcome:
        - The generated dataclass field uses `Optional[ReferencedType]`.
        - The field defaults to `= None`.
    """
    # Arrange
    ref_schema = IRSchema(name="Address", type="object", properties={"street": IRSchema(name=None, type="string")})
    schema = IRSchema(
        name="Person",
        type="object",
        required=["name"],
        properties={
            "name": IRSchema(name=None, type="string"),
            "address": ref_schema,  # Optional reference
        },
    )
    spec = IRSpec(title="T", version="0.1", schemas={"Person": schema, "Address": ref_schema}, operations=[])
    out_dir = tmp_path / "out"

    # Act
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    # Assert
    model_file = out_dir / "models" / "person.py"
    assert model_file.exists()
    content = model_file.read_text()

    # Check for Optional import robustly
    typing_imports = [line for line in content.splitlines() if line.startswith("from typing import")]
    assert any("Optional" in line for line in typing_imports), "'Optional' not found in typing imports"
    assert "address: Optional[Address] = None" in content  # Check field definition


def test_models_emitter_union_anyof(tmp_path: Path) -> None:
    """
    Scenario:
        - A schema property uses `anyOf` with two different types.
    Expected Outcome:
        - The generated dataclass field uses `Union[TypeA, TypeB]`.
    """
    # Arrange
    type_a = IRSchema(name="TypeA", type="string")
    type_b = IRSchema(name="TypeB", type="integer")
    schema = IRSchema(
        name="Container",
        type="object",
        required=["value"],
        properties={
            "value": IRSchema(
                name=None,
                any_of=[type_a, type_b],
            )
        },
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"Container": schema, "TypeA": type_a, "TypeB": type_b}, operations=[]
    )
    out_dir = tmp_path / "out"

    # Act
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    # Assert
    model_file = out_dir / "models" / "container.py"
    assert model_file.exists()
    content = model_file.read_text()

    # Check for Union import robustly
    typing_imports = [line for line in content.splitlines() if line.startswith("from typing import")]
    assert any("Union" in line for line in typing_imports), "'Union' not found in typing imports"
    assert "value: Union[TypeA, TypeB]" in content  # Correct assertion for required field


def test_models_emitter_optional_union_anyof_nullable(tmp_path: Path) -> None:
    """
    Scenario:
        - A schema property uses `anyOf` with two types AND is nullable.
    Expected Outcome:
        - The generated dataclass field uses `Union[TypeA, TypeB, None]` or `Optional[Union[TypeA, TypeB]]`.
    """
    # Arrange
    type_a = IRSchema(name="TypeA", type="string")
    type_b = IRSchema(name="TypeB", type="integer")
    schema = IRSchema(
        name="Container",
        type="object",
        required=[],  # value is optional
        properties={
            "value": IRSchema(
                name=None,
                any_of=[type_a, type_b],
                is_nullable=True,  # Explicitly nullable
            )
        },
    )
    spec = IRSpec(
        title="T", version="0.1", schemas={"Container": schema, "TypeA": type_a, "TypeB": type_b}, operations=[]
    )
    out_dir = tmp_path / "out"

    # Act
    emitter = ModelsEmitter()
    emitter.emit(spec, str(out_dir))

    # Assert
    model_file = out_dir / "models" / "container.py"
    assert model_file.exists()
    content = model_file.read_text()

    # Check for Union import robustly
    typing_imports = [line for line in content.splitlines() if line.startswith("from typing import")]
    assert any("Union" in line for line in typing_imports), "'Union' not found in typing imports"
    # Optional should also be imported due to is_nullable=True combined with the Union
    assert any(
        "Optional" in line for line in typing_imports
    ), "'Optional' not found in typing imports for nullable union"
    assert "value: Union[TypeA, TypeB, None] = None" in content  # Check the actual type hint
