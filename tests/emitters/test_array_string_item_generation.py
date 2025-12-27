"""Test for consistent array item type generation.

This test addresses issue: Inconsistent Array Item Type Generation

When an OpenAPI schema has array properties with `items: {type: string}`,
the generated code should be consistent across all property names.

Bug: Properties named "tags" correctly generate as List[str],
but other identically-defined properties like "classes", "ids", "tagClasses"
incorrectly generate empty dataclass wrappers or inconsistent types.
"""

import re
import tempfile
from pathlib import Path

import yaml

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.core.loader.schemas.extractor import extract_inline_array_items
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


class TestArrayStringItemGeneration:
    """Tests for consistent generation of array-of-string properties."""

    def test_extract_inline_array_items__array_with_string_items__not_extracted(self) -> None:
        """
        Scenario:
            A schema has multiple array properties with string items.
            All properties have identical definitions: {type: array, items: {type: string}}

        Expected Outcome:
            String array items should NOT be extracted as they are primitives.
            The original schema should remain unchanged with all arrays
            having inline string items.
        """
        # Arrange - Create schema matching the issue description
        parent_schema = IRSchema(
            name="DataSourceCreateConfigCleaningFilters",
            type="object",
            properties={
                "tags": IRSchema(type="array", items=IRSchema(type="string")),
                "ids": IRSchema(type="array", items=IRSchema(type="string")),
                "classes": IRSchema(type="array", items=IRSchema(type="string")),
                "tagClasses": IRSchema(type="array", items=IRSchema(type="string")),
            },
        )
        schemas = {"DataSourceCreateConfigCleaningFilters": parent_schema}

        # Act
        result = extract_inline_array_items(schemas)

        # Assert - Only the original schema should exist
        assert len(result) == 1, (
            f"Expected only original schema, got {len(result)} schemas: {list(result.keys())}. "
            "Primitive string array items should not be extracted."
        )
        assert "DataSourceCreateConfigCleaningFilters" in result

        # All array items should remain as inline string types
        for prop_name in ["tags", "ids", "classes", "tagClasses"]:
            array_prop = result["DataSourceCreateConfigCleaningFilters"].properties[prop_name]
            assert array_prop.type == "array"
            assert array_prop.items is not None
            assert array_prop.items.type == "string", (
                f"Property '{prop_name}' items should have type 'string', " f"got '{array_prop.items.type}'"
            )
            # Items should NOT have a name (should remain inline)
            assert array_prop.items.name is None, (
                f"Property '{prop_name}' items should not have a name (inline primitive), "
                f"got '{array_prop.items.name}'"
            )

    def test_models_emitter__dataclass_with_string_arrays__all_fields_are_list_str(self) -> None:
        """
        Scenario:
            ModelsEmitter processes a schema with multiple array-of-string properties.

        Expected Outcome:
            The generated dataclass should have all array properties typed as List[str].
            No separate item type files should be created for primitive string arrays.
        """
        # Arrange
        parent_schema = IRSchema(
            name="CleaningFilters",
            type="object",
            properties={
                "tags": IRSchema(type="array", items=IRSchema(type="string")),
                "ids": IRSchema(type="array", items=IRSchema(type="string")),
                "classes": IRSchema(type="array", items=IRSchema(type="string")),
                "tagClasses": IRSchema(type="array", items=IRSchema(type="string")),
            },
        )

        # Set generation names
        parent_schema.generation_name = "CleaningFilters"
        parent_schema.final_module_stem = "cleaning_filters"

        schemas = {"CleaningFilters": parent_schema}
        spec = IRSpec(
            title="Test API",
            version="1.0.0",
            schemas=schemas,
            operations=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            context = RenderContext(
                overall_project_root=tmpdir,
                package_root_for_generated_code=tmpdir,
                core_package_name="core",
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=schemas)

            # Act
            result = emitter.emit(spec, tmpdir)

            # Assert
            models_dir = Path(tmpdir) / "models"
            assert models_dir.exists()

            # Check the main dataclass file
            main_file = models_dir / "cleaning_filters.py"
            assert main_file.exists(), f"Expected {main_file} to exist"
            content = main_file.read_text()

            # All array properties should be List[str]
            for prop_name in ["tags", "ids", "classes", "tag_classes"]:
                assert (
                    f"List[str]" in content or f"list[str]" in content
                ), f"Property '{prop_name}' should be List[str], content: {content}"

            # No separate item files should exist for primitive types
            item_files = list(models_dir.glob("*_item.py"))
            assert len(item_files) == 0, (
                f"No item files should be created for primitive string arrays, "
                f"but found: {[f.name for f in item_files]}"
            )

    def test_models_emitter__named_array_alias_with_string_items__generates_type_alias(
        self,
    ) -> None:
        """
        Scenario:
            Top-level schema is a named array type with string items.
            Example: Tags = {type: array, items: {type: string}}

        Expected Outcome:
            Should generate: Tags: TypeAlias = List[str]
            NOT an empty dataclass or a complex wrapper.
        """
        # Arrange - Top-level array schemas (not properties)
        tags_schema = IRSchema(
            name="Tags",
            type="array",
            items=IRSchema(type="string"),
        )
        classes_schema = IRSchema(
            name="Classes",
            type="array",
            items=IRSchema(type="string"),
        )
        ids_schema = IRSchema(
            name="Ids",
            type="array",
            items=IRSchema(type="string"),
        )

        schemas = {
            "Tags": tags_schema,
            "Classes": classes_schema,
            "Ids": ids_schema,
        }

        # Set generation names
        for name, schema in schemas.items():
            schema.generation_name = name
            schema.final_module_stem = NameSanitizer.sanitize_module_name(name)

        spec = IRSpec(
            title="Test API",
            version="1.0.0",
            schemas=schemas,
            operations=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            context = RenderContext(
                overall_project_root=tmpdir,
                package_root_for_generated_code=tmpdir,
                core_package_name="core",
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=schemas)

            # Act
            result = emitter.emit(spec, tmpdir)

            # Assert
            models_dir = Path(tmpdir) / "models"

            # Each array alias should generate correctly
            for name in ["Tags", "Classes", "Ids"]:
                module_name = NameSanitizer.sanitize_module_name(name)
                file_path = models_dir / f"{module_name}.py"
                assert file_path.exists(), f"Expected {file_path} to exist"
                content = file_path.read_text()

                # Should be a TypeAlias to List[str], NOT a dataclass
                assert "TypeAlias" in content, f"{name} should be a TypeAlias, got: {content}"
                assert (
                    "List[str]" in content or "list[str]" in content
                ), f"{name} should be TypeAlias = List[str], got: {content}"
                assert "@dataclass" not in content, f"{name} should NOT be a dataclass for List[str], got: {content}"
                # Should NOT have "pass" indicating an empty class
                assert (
                    "pass" not in content or "# No properties" not in content
                ), f"{name} should not have empty class body, got: {content}"

    def test_all_string_array_properties_generate_identically(self) -> None:
        """
        Scenario:
            The core issue - identically-defined array properties should
            generate identical code regardless of the property name.

        Expected Outcome:
            Properties "tags", "classes", "ids", "tagClasses" with identical
            {type: array, items: {type: string}} definitions should all
            generate as List[str] fields.
        """
        # Arrange
        parent_schema = IRSchema(
            name="TestSchema",
            type="object",
            properties={
                # All these have IDENTICAL definitions
                "tags": IRSchema(type="array", items=IRSchema(type="string")),
                "classes": IRSchema(type="array", items=IRSchema(type="string")),
                "ids": IRSchema(type="array", items=IRSchema(type="string")),
                "tagClasses": IRSchema(type="array", items=IRSchema(type="string")),
                # Also test with some variation in property names
                "values": IRSchema(type="array", items=IRSchema(type="string")),
                "data": IRSchema(type="array", items=IRSchema(type="string")),
                "items": IRSchema(type="array", items=IRSchema(type="string")),
            },
        )

        parent_schema.generation_name = "TestSchema"
        parent_schema.final_module_stem = "test_schema"

        schemas = {"TestSchema": parent_schema}
        spec = IRSpec(
            title="Test API",
            version="1.0.0",
            schemas=schemas,
            operations=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            context = RenderContext(
                overall_project_root=tmpdir,
                package_root_for_generated_code=tmpdir,
                core_package_name="core",
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=schemas)

            # Act
            result = emitter.emit(spec, tmpdir)

            # Assert
            models_dir = Path(tmpdir) / "models"
            main_file = models_dir / "test_schema.py"
            assert main_file.exists()
            content = main_file.read_text()

            # Count how many List[str] fields we have
            import re

            list_str_matches = re.findall(r":\s*List\[str\]", content)

            # Should have exactly 7 List[str] fields (one for each property)
            # Note: Some might be optional (List[str] | None)
            all_matches = re.findall(r"List\[str\]", content)
            assert len(all_matches) >= 7, (
                f"Expected at least 7 List[str] fields (one for each property), "
                f"found {len(all_matches)}. Content:\n{content}"
            )

            # None of the properties should reference separate Item types
            for prop_name in ["tags", "classes", "ids", "tag_classes", "values", "data", "items_"]:
                # Check that no property references a separate *Item type
                item_type_pattern = rf"{prop_name}.*Item"
                assert not re.search(item_type_pattern, content, re.IGNORECASE), (
                    f"Property '{prop_name}' should NOT reference a separate Item type. " f"Content:\n{content}"
                )


class TestArrayStringItemGenerationE2E:
    """End-to-end tests that parse actual OpenAPI specs."""

    def test_e2e__openapi_spec_with_string_arrays__parsed_correctly(self) -> None:
        """
        Scenario:
            Parse a complete OpenAPI spec with an object containing
            multiple array-of-string properties.

        Expected Outcome:
            All properties should be parsed with type="array" and items.type="string".
            No separate item schemas should be created during parsing.
        """
        # Arrange - YAML spec matching the issue description
        spec_yaml = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths: {}
components:
  schemas:
    DataSourceCreateConfigCleaningFilters:
      type: object
      properties:
        tags:
          type: array
          items:
            type: string
        ids:
          type: array
          items:
            type: string
        classes:
          type: array
          items:
            type: string
        tagClasses:
          type: array
          items:
            type: string
"""
        spec_dict = yaml.safe_load(spec_yaml)

        # Act
        ir_spec = load_ir_from_spec(spec_dict)

        # Assert
        assert "DataSourceCreateConfigCleaningFilters" in ir_spec.schemas

        parent_schema = ir_spec.schemas["DataSourceCreateConfigCleaningFilters"]
        assert parent_schema.type == "object"

        # All properties should be arrays with string items
        for prop_name in ["tags", "ids", "classes", "tagClasses"]:
            assert prop_name in parent_schema.properties, f"Property '{prop_name}' should exist in schema"
            prop = parent_schema.properties[prop_name]
            assert prop.type == "array", f"Property '{prop_name}' should have type 'array', got '{prop.type}'"
            assert prop.items is not None, f"Property '{prop_name}' should have items defined"
            assert prop.items.type == "string", (
                f"Property '{prop_name}' items should have type 'string', " f"got '{prop.items.type}'"
            )

        # No extra *Item schemas should be created for primitive string arrays
        item_schemas = [name for name in ir_spec.schemas if "Item" in name]
        assert len(item_schemas) == 0, (
            f"No separate Item schemas should be created for primitive arrays, " f"but found: {item_schemas}"
        )

    def test_e2e__full_generation_from_openapi_spec__list_str_fields(self) -> None:
        """
        Scenario:
            Full end-to-end generation from OpenAPI YAML spec to Python code.

        Expected Outcome:
            Generated dataclass should have all array properties as List[str].
            No separate *_item.py files should be generated.
        """
        # Arrange
        spec_yaml = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths: {}
components:
  schemas:
    CleaningFilters:
      type: object
      properties:
        tags:
          type: array
          items:
            type: string
        classes:
          type: array
          items:
            type: string
        ids:
          type: array
          items:
            type: string
        tagClasses:
          type: array
          items:
            type: string
"""
        spec_dict = yaml.safe_load(spec_yaml)
        ir_spec = load_ir_from_spec(spec_dict)

        with tempfile.TemporaryDirectory() as tmpdir:
            context = RenderContext(
                overall_project_root=tmpdir,
                package_root_for_generated_code=tmpdir,
                core_package_name="core",
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=ir_spec.schemas)

            # Act
            result = emitter.emit(ir_spec, tmpdir)

            # Assert
            models_dir = Path(tmpdir) / "models"
            assert models_dir.exists()

            # Find the main schema file
            py_files = list(models_dir.glob("*.py"))
            main_files = [f for f in py_files if "cleaning_filters" in f.name]
            assert len(main_files) == 1, f"Expected one cleaning_filters.py file, got: {[f.name for f in py_files]}"

            content = main_files[0].read_text()

            # Should contain List[str] for all array properties
            assert "List[str]" in content, f"Generated content should contain List[str]:\n{content}"

            # No *_item.py files should exist
            item_files = list(models_dir.glob("*_item.py"))
            assert len(item_files) == 0, f"No item files should be created, but found: {[f.name for f in item_files]}"

            # Should not contain any *Item type references (except in imports if any)
            # Split content to check class body only
            class_body_start = content.find("class CleaningFilters")
            if class_body_start != -1:
                class_content = content[class_body_start:]
                # Should not have TagsItem, ClassesItem, etc. in the class body
                item_refs = re.findall(r"\b\w+Item\b", class_content)
                # Filter out legitimate ItemsView from dict methods
                item_refs = [r for r in item_refs if r != "ItemsView"]
                assert len(item_refs) == 0, (
                    f"Class body should not reference *Item types, found: {item_refs}. " f"Content:\n{content}"
                )

    def test_e2e__top_level_array_schemas__generate_type_aliases(self) -> None:
        """
        Scenario:
            OpenAPI spec has top-level array schemas that alias List[str].

        Expected Outcome:
            Should generate TypeAlias = List[str] for each, NOT dataclasses.
        """
        # Arrange
        spec_yaml = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths: {}
components:
  schemas:
    Tags:
      type: array
      items:
        type: string
    Classes:
      type: array
      items:
        type: string
    Ids:
      type: array
      items:
        type: string
"""
        spec_dict = yaml.safe_load(spec_yaml)
        ir_spec = load_ir_from_spec(spec_dict)

        with tempfile.TemporaryDirectory() as tmpdir:
            context = RenderContext(
                overall_project_root=tmpdir,
                package_root_for_generated_code=tmpdir,
                core_package_name="core",
            )

            emitter = ModelsEmitter(context=context, parsed_schemas=ir_spec.schemas)

            # Act
            result = emitter.emit(ir_spec, tmpdir)

            # Assert
            models_dir = Path(tmpdir) / "models"

            for name in ["tags", "classes", "ids"]:
                file_path = models_dir / f"{name}.py"
                assert file_path.exists(), f"Expected {file_path} to exist"
                content = file_path.read_text()

                # Should be a TypeAlias
                assert "TypeAlias" in content, f"{name}.py should contain TypeAlias:\n{content}"
                assert "List[str]" in content, f"{name}.py should contain List[str]:\n{content}"
                # Should NOT be a dataclass
                assert "@dataclass" not in content, f"{name}.py should NOT be a dataclass:\n{content}"

            # No *_item.py files should exist
            item_files = list(models_dir.glob("*_item.py"))
            assert len(item_files) == 0, f"No item files should be created, but found: {[f.name for f in item_files]}"
