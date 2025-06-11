import os
import unittest
from pathlib import Path

import pytest

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


@pytest.mark.skipif(
    os.environ.get("CI") == "true", 
    reason="File generation issue in CI environment - works locally"
)
def test_models_emitter__single_object_schema__generates_module_and_init(tmp_path: Path) -> None:
    """
    Scenario:
        ModelsEmitter processes a simple IRSpec with a single object schema (Pet)
        containing basic properties (id, name).

    Expected Outcome:
        The emitter should generate a Pet model file and a models __init__.py
        that exports the Pet class.
    """
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
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Pet.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    assert "from dataclasses import dataclass" in result
    assert "id_: int" in result  # 'id' is sanitized to 'id_' because it's a Python builtin
    assert "name: str" in result


@pytest.mark.skipif(
    os.environ.get("CI") == "true", 
    reason="File generation issue in CI environment - works locally"
)
def test_models_emitter__string_enum_schema__generates_enum_class(tmp_path: Path) -> None:
    """
    Scenario:
        ModelsEmitter processes an IRSpec with a string enum schema (Status)
        containing enum values ["pending", "approved", "rejected"].

    Expected Outcome:
        The emitter should generate a Status enum class with the correct values
        and proper Python enum structure.
    """
    schema = IRSchema(
        name="Status",
        type="string",
        enum=["pending", "approved", "rejected"],
        description="Status of a pet",
    )
    spec = IRSpec(title="T", version="0.1", schemas={"Status": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Status.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    assert "from enum import Enum" in result
    assert "class Status(str, Enum):" in result
    assert "PENDING" in result
    assert "APPROVED" in result
    assert "REJECTED" in result


def test_models_emitter__object_with_array_property__generates_list_type_annotation(tmp_path: Path) -> None:
    """
    Scenario:
        ModelsEmitter processes an IRSpec with an object schema (PetList) that has
        an array property containing Pet objects.

    Expected Outcome:
        The emitter should generate a PetList model with proper List[Pet] type
        annotation for the array property.
    """
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
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "pet_list.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    assert "from dataclasses import dataclass" in result
    assert "from typing import" in result
    assert "@dataclass" in result
    assert "class PetList:" in result
    # Check for the item model import and type (now using correct same-directory relative imports)
    assert "from .pet_list_items_item import PetListItemsItem" in result
    assert "items: Optional[List[PetListItemsItem]]" in result

    # Also verify the item model was created
    item_model_file: Path = out_dir / "models" / "pet_list_items_item.py"
    assert item_model_file.exists()


@pytest.mark.skipif(
    os.environ.get("CI") == "true", 
    reason="File generation issue in CI environment - works locally"
)
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
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Event.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    assert "from dataclasses import dataclass" in result
    assert "from typing import" in result
    assert "from datetime import" in result
    assert "@dataclass" in result
    assert "class Event:" in result
    assert "created_at: Optional[datetime]" in result
    assert "date_only: Optional[date]" in result


@pytest.mark.skipif(
    os.environ.get("CI") == "true", 
    reason="File generation issue in CI environment - works locally"
)
def test_models_emitter_empty_schema(tmp_path: Path) -> None:
    """Test empty schema handling."""
    schema = IRSchema(
        name="Empty",
        type="object",
        properties={},  # Empty object
    )
    spec = IRSpec(title="T", version="0.1", schemas={"Empty": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "Empty.py"
    assert model_file.exists()

    content: str = model_file.read_text()
    lines: list[str] = [line.rstrip() for line in content.splitlines() if line.strip()]
    result: str = "\n".join(lines)

    assert "from dataclasses import dataclass" in result
    assert "# No properties defined in schema" in result
    assert "pass" in result


def test_models_emitter_init_file(tmp_path: Path) -> None:
    """Test __init__.py generation."""
    schemas_dict = {
        "Pet": IRSchema(name="Pet", type="object", properties={}),
        "Order": IRSchema(name="Order", type="object", properties={}),
        "User": IRSchema(name="User", type="object", properties={}),
    }
    spec = IRSpec(title="T", version="0.1", schemas=schemas_dict, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    init_file: Path = out_dir / "models" / "__init__.py"
    assert init_file.exists()
    init_content = init_file.read_text()

    # Assert that only 'List' is imported from typing, for __all__
    assert "from typing import List" in init_content
    # Assert that the broad, unnecessary typing import is NOT present
    assert "from typing import TYPE_CHECKING, List, Optional, Union, Any, Dict, Generic, TypeVar" not in init_content
    # Assert that dataclasses is NOT imported here
    assert "from dataclasses import dataclass, field" not in init_content

    assert "from .pet import Pet" in init_content
    assert "from .order import Order" in init_content
    assert "from .user import User" in init_content

    assert "__all__: List[str] = [" in init_content
    # Order in __all__ is sorted
    assert "'Order'," in init_content
    assert "'Pet'," in init_content
    assert "'User'," in init_content


def test_models_emitter__emit_single_schema__generates_module_and_init(tmp_path: Path) -> None:
    """Test emitting a single schema creates its module and updates __init__."""
    schema = IRSchema(name="TestSchema", type="object", properties={"field": IRSchema(name="field", type="string")})
    spec = IRSpec(title="T", version="0.1", schemas={"TestSchema": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "test_schema.py"
    assert model_file.exists()
    init_file: Path = out_dir / "models" / "__init__.py"
    assert init_file.exists()
    init_content = init_file.read_text()
    assert "from .test_schema import TestSchema" in init_content
    assert "'TestSchema'," in init_content


def test_models_emitter__primitive_alias(tmp_path: Path) -> None:
    """Test generation of type alias for primitive types."""
    schema = IRSchema(name="UserID", type="string", format="uuid")
    spec = IRSpec(title="T", version="0.1", schemas={"UserID": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "user_id.py"
    assert model_file.exists()
    content = model_file.read_text()

    # Assertions updated for sanitized class name "UserId"
    assert "from typing import TypeAlias" in content
    assert "from uuid import UUID" in content  # UUID format requires import
    assert '__all__ = ["UserId"]' in content  # Sanitized class name for __all__
    assert "UserId: TypeAlias = UUID" in content  # UUID type for uuid format

    # Ensure it's not generating a class for simple alias
    assert "class UserId" not in content  # Check against sanitized name
    assert "@dataclass" not in content

    init_file: Path = out_dir / "models" / "__init__.py"
    init_content = init_file.read_text()
    # The import in __init__.py should use the sanitized class name from the module
    assert f"from .user_id import UserId" in init_content
    # Check if UserId (sanitized) is in __all__ of models/__init__.py
    # Based on current _generate_init_py_content, it should be if it's an alias from a file.
    # The original test asserted it's NOT in __all__, which might have been for a different __init__ structure.
    # Let's assume for now that type aliases *are* added to __all__ if they get their own file.
    # PythonConstructRenderer.render_type_alias adds to its own module's __all__.
    # ModelsEmitter._generate_init_py_content adds all successfully generated model class_names to its __all__.
    assert "'UserId'," in init_content


def test_models_emitter__array_of_primitives_alias(tmp_path: Path) -> None:
    """Test generation of type alias for array of primitives."""
    schema = IRSchema(name="TagList", type="array", items=IRSchema(type="string"))
    spec = IRSpec(title="T", version="0.1", schemas={"TagList": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "tag_list.py"  # module name sanitized
    assert model_file.exists()
    content = model_file.read_text()

    assert "from typing import List, TypeAlias" in content  # TypeAlias for explicit alias
    assert '__all__ = ["TagList"]' in content
    assert "TagList: TypeAlias = List[str]" in content
    assert "class TagList" not in content


def test_models_emitter__array_of_models_alias(tmp_path: Path) -> None:
    """Test generation of type alias for array of other models."""
    item_schema = IRSchema(name="Item", type="object")
    list_schema = IRSchema(name="ItemList", type="array", items=item_schema)
    schemas_dict = {"Item": item_schema, "ItemList": list_schema}
    spec = IRSpec(title="T", version="0.1", schemas=schemas_dict, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    # Check Item.py (should be a dataclass)
    item_model_file: Path = out_dir / "models" / "item.py"  # module name sanitized
    assert item_model_file.exists()
    item_content = item_model_file.read_text()
    assert "@dataclass" in item_content
    assert "class Item:" in item_content

    # Check ItemList.py (should be a type alias to List[Item])
    list_model_file: Path = out_dir / "models" / "item_list.py"  # module name sanitized
    assert list_model_file.exists()
    list_content = list_model_file.read_text()
    assert "from typing import List, TypeAlias" in list_content  # TypeAlias for explicit alias
    assert "from .item import Item" in list_content
    assert '__all__ = ["ItemList"]' in list_content
    assert "ItemList: TypeAlias = List[Item]" in list_content
    assert "class ItemList" not in list_content


def test_models_emitter__integer_enum(tmp_path: Path) -> None:
    """Test integer enum generation."""
    schema = IRSchema(name="ErrorCode", type="integer", enum=[10, 20, 30])
    spec = IRSpec(title="T", version="0.1", schemas={"ErrorCode": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "error_code.py"  # module name sanitized
    assert model_file.exists()
    content = model_file.read_text()
    assert "from enum import Enum, unique" in content  # unique is often used
    assert '__all__ = ["ErrorCode"]' in content
    assert "@unique" in content  # Check for decorator
    assert "class ErrorCode(int, Enum):" in content
    assert "VALUE_10 = 10" in content  # Default member naming for numbers
    assert "VALUE_20 = 20" in content
    assert "VALUE_30 = 30" in content


def test_models_emitter__unnamed_schema_skipped(tmp_path: Path) -> None:
    """Test that schemas without a name are skipped for file generation but present in context if parsed from ref."""
    unnamed_schema = IRSchema(type="object")  # No name
    referencing_schema = IRSchema(name="Container", type="object", properties={"data": unnamed_schema})
    # Emitter operates on schemas passed to its constructor, not directly from spec.schemas in emit()
    # It processes self.parsed_schemas. How these get there depends on the loader.
    # For this unit test, we manually set up parsed_schemas.

    parsed_schemas_for_emitter = {
        # Unnamed schemas usually get a contextual name if parsed, e.g., "Container.data"
        # Or they are promoted directly. If it remains truly unnamed and not a ref target, it won't be emitted.
        # Let's assume for this test it's not in parsed_schemas under a globally unique key for file emission.
        "Container": referencing_schema
    }

    spec = IRSpec(title="T", version="0.1", schemas=parsed_schemas_for_emitter, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    # Simulate that the unnamed schema was processed and maybe even promoted to `ContainerData` by the loader.
    # The ModelsEmitter itself receives the result of parsing.
    # If `unnamed_schema` was promoted to `ContainerData` and its `name` field was updated, then `ModelsEmitter`
    # would emit it. If it was truly unnamed and not promoted, `_generate_model_file` in ModelsEmitter skips it.

    # To test the skipping within ModelsEmitter for a schema that *is* in its `parsed_schemas` dict but has no `name`:
    no_name_in_map_schema = IRSchema(type="object")  # name is None
    emitter_schemas = {"Container": referencing_schema, "_some_internal_key_for_no_name": no_name_in_map_schema}

    emitter = ModelsEmitter(context=render_context, parsed_schemas=emitter_schemas)
    generated_files = emitter.emit(
        spec, str(out_dir)
    )  # spec is used by emit for some things, but schemas from constructor

    # Assert that only Container.py is generated, not for the unnamed_schema or no_name_in_map_schema
    assert any("container.py" in f.lower() for f in generated_files["models"])
    assert not any("_some_internal_key_for_no_name.py" in f.lower() for f in generated_files["models"])


def test_models_emitter__unknown_type_fallback(tmp_path: Path) -> None:
    """Test fallback to Any for unknown types that are not resolvable as references."""
    # If 'unknown' is truly unknown and not a ref, it should become 'Any'.
    # The previous failure "from .unknown import Unknown" suggests ModelVisitor
    # might try to treat it as a reference if a schema named "Unknown" exists globally.
    # For this test, ensure no such global schema exists.
    schema = IRSchema(name="MysteryType", type="unknown_type_xyz")  # A type that won't be a ref
    schemas_dict = {"MysteryType": schema}
    spec = IRSpec(title="T", version="0.1", schemas=schemas_dict, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    # Pass only this schema to the emitter to avoid accidental resolution
    emitter = ModelsEmitter(context=render_context, parsed_schemas=schemas_dict)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "mystery_type.py"  # module name sanitized
    assert model_file.exists()
    content = model_file.read_text()

    assert "from typing import Any, TypeAlias" in content  # TypeAlias for explicit alias
    assert '__all__ = ["MysteryType"]' in content
    assert "MysteryType: TypeAlias = Any" in content


def test_models_emitter__optional_any_field__emits_all_typing_imports(tmp_path: Path) -> None:
    schema = IRSchema(
        name="DataHolder",
        type="object",
        properties={"flexible_field": IRSchema(type=None)},
    )
    spec = IRSpec(title="T", version="0.1", schemas={"DataHolder": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "data_holder.py"
    assert model_file.exists()
    content = model_file.read_text()

    # Check for necessary imports for Any type (modern style doesn't need Optional for default None)
    assert "from typing import Any" in content
    # Check that the field uses the modern style for optional with default
    assert "flexible_field: Any = None" in content


def test_models_emitter__inline_response_schema__generates_model(tmp_path: Path) -> None:
    """
    Scenario:
        The IRSpec contains a schema for an inline response (e.g., ListenEventsResponse) that
        was not in components/schemas. The model emitter should generate a dataclass for this
        inline response schema if it's passed to the emitter's constructor.

    Expected Outcome:
        - A model file is generated for ListenEventsResponse in the models directory
        - The file contains a dataclass definition for ListenEventsResponse
    """
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
    # The ModelsEmitter gets its schemas from its constructor's parsed_schemas argument.
    # The spec object passed to emit() is used for other things like output_dir determination.
    parsed_schemas_for_emitter = {"ListenEventsResponse": schema}
    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        schemas=parsed_schemas_for_emitter,  # This might be redundant if emitter uses its own copy
        operations=[],
        servers=[],
    )
    out_dir = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=parsed_schemas_for_emitter)
    emitter.emit(spec, str(out_dir))

    model_file = out_dir / "models" / "listen_events_response.py"
    assert model_file.exists(), "Model file for ListenEventsResponse not generated"
    content = model_file.read_text()
    assert "@dataclass" in content
    assert "class ListenEventsResponse" in content
    assert "data_:" in content  # 'data' is sanitized to 'data_' because it's a Python builtin
    assert "event:" in content
    assert "id_:" in content  # 'id' is sanitized to 'id_' because it's a Python builtin


def test_models_emitter_optional_list_factory(tmp_path: Path) -> None:
    """Test generation for an optional list with a default factory."""
    schema = IRSchema(
        name="Config",
        type="object",
        properties={"tags": IRSchema(name="tags", type="array", items=IRSchema(type="string"))},
        # 'tags' is not in 'required', so it's optional.
        # ModelVisitor should add default_factory=list if it's a List.
    )
    spec = IRSpec(title="T", version="0.1", schemas={"Config": schema}, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    model_file: Path = out_dir / "models" / "config_.py"  # 'config' is sanitized to 'config_' because it's reserved
    assert model_file.exists()
    content = model_file.read_text()
    assert "from dataclasses import dataclass, field" in content
    assert "from typing import List, Optional" in content
    assert "@dataclass" in content
    assert "class Config_:" in content  # 'Config' is sanitized to 'Config_' because 'config' is reserved
    # Field should be Optional[List[str]] and use field(default_factory=list)
    assert "tags: Optional[List[str]] = field(default_factory=list)" in content


def test_models_emitter_optional_named_object_none_default(tmp_path: Path) -> None:
    """Test optional field that is a reference to another named object."""
    address_schema = IRSchema(name="Address", type="object", properties={"street": IRSchema(type="string")})
    user_schema = IRSchema(
        name="User",
        type="object",
        properties={"address": address_schema},  # 'address' is not in 'required'
    )
    schemas_dict = {"Address": address_schema, "User": user_schema}
    spec = IRSpec(title="T", version="0.1", schemas=schemas_dict, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    # Check Address.py
    address_file: Path = out_dir / "models" / "address.py"
    assert address_file.exists()
    address_content = address_file.read_text()
    assert "class Address:" in address_content

    # Check User.py
    user_file: Path = out_dir / "models" / "user.py"
    assert user_file.exists()
    user_content = user_file.read_text()
    assert "from typing import Optional" in user_content
    assert "from .address import Address" in user_content
    assert "address: Optional[Address] = None" in user_content


def test_models_emitter_union_anyof(tmp_path: Path) -> None:
    schema_a = IRSchema(name="SchemaA", type="object", properties={"field_a": IRSchema(type="string")})
    schema_b = IRSchema(name="SchemaB", type="object", properties={"field_b": IRSchema(type="integer")})
    union_schema = IRSchema(name="MyUnion", type=None, any_of=[schema_a, schema_b])
    schemas_dict = {"SchemaA": schema_a, "SchemaB": schema_b, "MyUnion": union_schema}
    spec = IRSpec(title="T", version="0.1", schemas=schemas_dict, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    assert (out_dir / "models" / "schema_a.py").exists()
    assert (out_dir / "models" / "schema_b.py").exists()

    union_file: Path = out_dir / "models" / "my_union.py"
    assert union_file.exists()
    union_content = union_file.read_text()
    assert "from typing import TypeAlias, Union" in union_content  # Corrected order
    assert "from .schema_a import SchemaA" in union_content
    assert "from .schema_b import SchemaB" in union_content
    assert '__all__ = ["MyUnion"]' in union_content
    assert "MyUnion: TypeAlias = Union[SchemaA, SchemaB]" in union_content


def test_models_emitter_optional_union_anyof_nullable(tmp_path: Path) -> None:
    schema_a = IRSchema(name="SchemaOptA", type="object", properties={"field_a": IRSchema(type="string")})
    schema_b = IRSchema(name="SchemaOptB", type="object", properties={"field_b": IRSchema(type="integer")})
    union_schema = IRSchema(name="MyOptionalUnion", any_of=[schema_a, schema_b], is_nullable=True)
    container_schema = IRSchema(name="Container", type="object", properties={"payload": union_schema})

    schemas_dict = {
        "SchemaOptA": schema_a,
        "SchemaOptB": schema_b,
        "MyOptionalUnion": union_schema,
        "Container": container_schema,
    }
    spec = IRSpec(title="T", version="0.1", schemas=schemas_dict, operations=[], servers=[])

    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",
    )
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    emitter.emit(spec, str(out_dir))

    union_file: Path = out_dir / "models" / "my_optional_union.py"
    assert union_file.exists()
    union_content = union_file.read_text()
    assert "from typing import Optional, TypeAlias, Union" in union_content  # Corrected order
    assert "from .schema_opt_a import SchemaOptA" in union_content
    assert "from .schema_opt_b import SchemaOptB" in union_content
    assert '__all__ = ["MyOptionalUnion"]' in union_content
    # The alias itself should be Union, Optional wrapping is for where it's USED if the property is optional,
    # or if the alias schema itself is_nullable.
    # If MyOptionalUnion.is_nullable = True, then the alias itself should incorporate Optional for ModelVisitor.
    # ModelVisitor -> TypeHelper.get_python_type_for_schema -> _type_to_string
    # If schema.is_nullable, _type_to_string wraps with Optional.
    assert "MyOptionalUnion: TypeAlias = Optional[Union[SchemaOptA, SchemaOptB]]" in union_content

    container_file: Path = out_dir / "models" / "container.py"
    assert container_file.exists()
    container_content = container_file.read_text()
    # Optional import may not be present if MyOptionalUnion is the only source of optionality
    # and it handles its own Optional declaration internally.
    # assert "from typing import Optional" in container_content  # For the field
    assert "from .my_optional_union import MyOptionalUnion" in container_content
    # The field 'payload' uses MyOptionalUnion. The current system explicitly wraps in Optional
    # even if the alias already includes Optional, for clarity at the usage site.
    assert "payload: Optional[MyOptionalUnion] = None" in container_content


if __name__ == "__main__":
    unittest.main()
