"""
Tests for TypeHelper methods that support type conversion and cleaning.
"""

import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
from unittest.mock import MagicMock

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.file_manager import FileManager
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.helpers.type_helper import TypeHelper
from pyopenapi_gen.helpers.type_resolution.array_resolver import ArrayTypeResolver
from pyopenapi_gen.helpers.type_resolution.composition_resolver import CompositionTypeResolver
from pyopenapi_gen.helpers.type_resolution.finalizer import TypeFinalizer
from pyopenapi_gen.helpers.type_resolution.named_resolver import NamedTypeResolver
from pyopenapi_gen.helpers.type_resolution.object_resolver import ObjectTypeResolver
from pyopenapi_gen.helpers.type_resolution.primitive_resolver import PrimitiveTypeResolver
from pyopenapi_gen.helpers.type_resolution.resolver import SchemaTypeResolver


class TestTypeHelperCleanTypeParameters:
    """Tests for the _clean_type_parameters function in TypeHelper."""

    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def finalizer(self, context: RenderContext) -> TypeFinalizer:
        return TypeFinalizer(context)

    @pytest.mark.parametrize(
        "test_id, input_type, expected_type",
        [
            # Simple cases
            ("simple_dict", "dict[str, Any]", "dict[str, Any]"),
            ("simple_list", "List[str]", "List[str]"),
            ("simple_optional", "str | None", "str | None"),
            # Common error cases from OpenAPI 3.1 nullable handling
            ("dict_with_none", "dict[str, Any, None]", "dict[str, Any]"),
            ("list_with_none", "List[JsonValue, None]", "List[JsonValue]"),
            ("optional_with_none", "Optional[Any, None]", "Any | None"),
            # More complex nested types
            ("nested_dict", "dict[str, dict[str, Any, None]]", "dict[str, dict[str, Any]]"),
            ("nested_list", "List[List[str, None]]", "List[List[str]]"),
            (
                "complex_union",
                "Union[dict[str, Any, None], List[str, None], Optional[int, None]]",
                "Union[dict[str, Any], List[str], int | None]",
            ),
            # OpenAPI 3.1 complex nullable cases
            ("openapi_31_list_none", "List[Union[dict[str, Any], None]]", "List[Union[dict[str, Any], None]]"),
            ("list_with_multi_params", "List[str, int, bool, None]", "List[str]"),
            ("dict_with_multi_params", "dict[str, int, bool, None]", "dict[str, int]"),
            # Deeply nested structures
            (
                "deep_nested_union",
                "Union[dict[str, List[dict[str, Any, None], None]], List[dict[str, Any, None], None]]",
                "Union[dict[str, List[dict[str, Any]]], List[dict[str, Any]]]",
            ),
            # Real-world complex cases from the errors we've encountered
            (
                "embedding_flat_case",
                "Union[dict[str, Any], List[Union[dict[str, Any], List[JsonValue], Any | None, bool, float, str, None], None], Any | None, bool, float, str]",
                "Union[dict[str, Any], List[Union[dict[str, Any], List[JsonValue], Any | None, bool, float, str, None]], Any | None, bool, float, str]",
            ),
            # Edge cases
            ("empty_string", "", ""),
            ("no_brackets", "AnyType", "AnyType"),
            ("incomplete_syntax", "dict[str,", "dict[str,"),
            ("empty_union", "Union[]", "Any"),
            ("optional_none", "Optional[None]", "Any | None"),
        ],
    )
    def test_clean_type_parameters(
        self, test_id: str, input_type: str, expected_type: str, finalizer: TypeFinalizer
    ) -> None:
        """
        Scenario:
            - Test _clean_type (via TypeFinalizer) with various invalid type strings
            - Verify it correctly removes extraneous None parameters

        Expected Outcome:
            - Properly cleaned type strings with no invalid None parameters
        """
        # Act
        result = finalizer._clean_type(input_type)

        # Assert
        assert result == expected_type, f"[{test_id}] Failed to clean type string correctly"

    def test_clean_nested_types_with_complex_structures(self, finalizer: TypeFinalizer) -> None:
        """
        Scenario:
            - Test the clean_nested_types method with complex nested structures

        Expected Outcome:
            - Should handle deeply nested structures correctly
        """
        # The exact string with no whitespace between parts
        complex_type = "Union[dict[str, List[dict[str, Any, None], None]], List[Union[dict[str, Any, None], str, None]], Optional[dict[str, Union[str, int, None], None]]]"

        expected = "Union[dict[str, List[dict[str, Any]]], List[Union[dict[str, Any], str, None]], dict[str, Union[str, int, None]] | None]"

        result = finalizer._clean_type(complex_type)

        assert result == expected, "Failed to clean complex nested type correctly"

    def test_real_world_cases(self, finalizer: TypeFinalizer) -> None:
        """
        Scenario:
            - Test the clean_nested_types method with real-world problem cases

        Expected Outcome:
            - Should handle problematic real-world type strings correctly
        """
        # Case from EmbeddingFlat.py that caused the linter error
        embedding_flat_type = (
            "Union["
            "dict[str, Any], "
            "List["
            "Union["
            "dict[str, Any], List[JsonValue], Any | None, bool, float, str, None"
            "], "
            "None"
            "], "
            "Any | None, "
            "bool, "
            "float, "
            "str"
            "]"
        )

        expected = (
            "Union["
            "dict[str, Any], "
            "List["
            "Union["
            "dict[str, Any], List[JsonValue], Any | None, bool, float, str, None"
            "]"
            "], "
            "Any | None, "
            "bool, "
            "float, "
            "str"
            "]"
        )

        result = finalizer._clean_type(embedding_flat_type)

        assert result == expected, "Failed to clean EmbeddingFlat type string correctly"


class TestTypeHelperWithIRSchema:
    """Tests TypeHelper's schema handling with IRSchema objects."""

    @pytest.fixture
    def finalizer(self, context: RenderContext) -> TypeFinalizer:
        return TypeFinalizer(context)

    @pytest.fixture
    def fresh_finalizer(self) -> TypeFinalizer:
        return TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )

    @pytest.fixture
    def context(self) -> RenderContext:
        """Provides a fresh RenderContext for each test case."""
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def nullable_schema(self) -> IRSchema:
        """Provides a schema that is explicitly nullable."""
        return IRSchema(name="TestNullable", type="string", is_nullable=True)

    @pytest.fixture
    def non_nullable_schema(self) -> IRSchema:
        """Provides a schema that is explicitly not nullable."""
        return IRSchema(name="TestNonNullable", type="string", is_nullable=False)

    @pytest.fixture
    def none_nullable_schema(self) -> IRSchema:
        """Provides a schema where is_nullable is None (should behave as not nullable for optional check)."""
        return IRSchema(name="TestNoneNullable", type="string", is_nullable=None)  # type: ignore

    # Test Scenarios for _finalize_type_with_optional based on Design by Contract

    # Category 1: Not Optional by Usage (required=True, schema.is_nullable=False/None)
    # Postcondition 1.a: result_type == py_type
    # Postcondition 2.a: "typing.Optional" NOT added to context by this call
    @pytest.mark.parametrize(
        "py_type", ["str", "List[int]", "Union[str, bool]", "Any", "str | None", "Union[str, None]"]
    )
    def test_finalize_not_optional_by_usage_remains_unchanged(
        self,
        py_type: str,
        non_nullable_schema: IRSchema,
        none_nullable_schema: IRSchema,
        finalizer: TypeFinalizer,
        fresh_finalizer: TypeFinalizer,
    ) -> None:
        """Contract: If not optional by usage, py_type is returned as is, Optional not imported."""
        # Test with is_nullable = False
        result_false_nullable = finalizer.finalize(py_type, non_nullable_schema, True)
        assert result_false_nullable == py_type
        # Use fresh_finalizer for isolated import check
        fresh_finalizer.finalize(py_type, non_nullable_schema, True)  # Call on fresh instance
        assert not fresh_finalizer.context.import_collector.has_import(
            "typing", "Optional"
        ), f"Optional was incorrectly added for {py_type} with non_nullable_schema, required=True"

        # Test with is_nullable = None
        # Re-create fresh_finalizer for the second isolated check or use a different one
        another_fresh_finalizer = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result_none_nullable = finalizer.finalize(
            py_type, none_nullable_schema, True
        )  # Use general finalizer for main assert
        assert result_none_nullable == py_type
        another_fresh_finalizer.finalize(py_type, none_nullable_schema, True)  # Call on new fresh instance
        assert not another_fresh_finalizer.context.import_collector.has_import(
            "typing", "Optional"
        ), f"Optional was incorrectly added for {py_type} with none_nullable_schema, required=True"

    # Category 2: Optional by Usage
    # Postcondition 1.b

    # Sub-Category 2.1: Optional because `required=False`
    def test_finalize_optional_due_to_not_required(
        self, non_nullable_schema: IRSchema, fresh_finalizer: TypeFinalizer
    ) -> None:
        """Contract: Optional due to required=False."""
        # Postcondition 1.b.v (simple type)
        ff1 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff1.finalize("str", non_nullable_schema, False) == "str | None"

        # Postcondition 1.b.ii ("Any")
        ff2 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff2.finalize("Any", non_nullable_schema, False) == "Any | None"

        # Postcondition 1.b.iii (already "Optional[...]")
        ff3 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff3.finalize("int | None", non_nullable_schema, False) == "int | None"
        assert not ff3.context.import_collector.has_import(
            "typing", "Optional"
        ), "Optional added when py_type was already Optional[]"

        # Postcondition 1.b.iv (already "Union[..., None]")
        ff4 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff4.finalize("Union[int, float, None]", non_nullable_schema, False) == "Union[int, float, None]"
        assert not ff4.context.import_collector.has_import(
            "typing", "Optional"
        ), "Optional added when py_type was Union[..., None]"

        ff5 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff5.finalize("Union[None, int, float]", non_nullable_schema, False) == "Union[None, int, float]"
        assert not ff5.context.import_collector.has_import("typing", "Optional")

        ff6 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff6.finalize("Union[int, None, float]", non_nullable_schema, False) == "Union[int, None, float]"
        assert not ff6.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.v (Union without None)
        ff7 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff7.finalize("Union[int, float]", non_nullable_schema, False) == "Union[int, float] | None"

    # Sub-Category 2.2: Optional because `schema.is_nullable=True`
    def test_finalize_optional_due_to_schema_nullable(
        self, nullable_schema: IRSchema, fresh_finalizer: TypeFinalizer
    ) -> None:
        """Contract: Optional due to schema.is_nullable=True."""
        # Postcondition 1.b.v (simple type)
        ff1 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff1.finalize("str", nullable_schema, True) == "str | None"

        # Postcondition 1.b.ii ("Any")
        ff2 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff2.finalize("Any", nullable_schema, True) == "Any | None"

        # Postcondition 1.b.iii (already "Optional[...]")
        ff3 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff3.finalize("int | None", nullable_schema, True) == "int | None"
        assert not ff3.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.iv (already "Union[..., None]")
        ff4 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff4.finalize("Union[int, float, None]", nullable_schema, True) == "Union[int, float, None]"
        assert not ff4.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.v (Union without None) - Modern union syntax
        ff5 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff5.finalize("Union[int, float]", nullable_schema, True) == "Union[int, float] | None"

    # Sub-Category 2.3: Optional because `required=False` AND `schema.is_nullable=True` (double reason)
    def test_finalize_optional_due_to_not_required_and_schema_nullable(
        self, nullable_schema: IRSchema, fresh_finalizer: TypeFinalizer
    ) -> None:
        """Contract: Optional due to both required=False and schema.is_nullable=True."""
        assert fresh_finalizer.finalize("str", nullable_schema, False) == "str | None"

    # Test original problematic cases explicitly, mapping them to the contract
    def test_finalize_original_cases_mapped_to_contract(
        self, nullable_schema: IRSchema, non_nullable_schema: IRSchema
    ) -> None:
        """Original test cases mapped to new contract understanding."""

        # Case 1: Simple type with nullable schema (required=True)
        # Contract: Optional due to schema.is_nullable=True (Sub-Category 2.2)
        # Expect: "str | None", import Optional
        ff_c1 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c1.finalize("str", nullable_schema, True)
        assert result == "str | None"

        # Case 2: Simple type with non-nullable schema but not required (required=False)
        # Contract: Optional due to required=False (Sub-Category 2.1)
        # Expect: "str | None", import Optional
        ff_c2 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c2.finalize("str", non_nullable_schema, False)
        assert result == "str | None"

        # Case 3: Already Optional type doesn't get double-wrapped (schema nullable, required=True)
        # Contract: Optional by usage, but py_type already "Optional[...]" (Postcondition 1.b.iii)
        # Expect: "str | None", DO NOT import Optional again for this specific call path
        ff_c3 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c3.finalize("str | None", nullable_schema, True)
        assert result == "str | None"
        assert not ff_c3.context.import_collector.has_import(
            "typing", "Optional"
        ), "Optional import was added when py_type was already Optional[]"

        # Case 4: Union type, non-nullable schema, not required (required=False)
        # Contract: Optional due to required=False. py_type is "Union[str, int]" (Postcondition 1.b.v)
        # Expect: "Optional[Union[str, int]]", import Optional
        ff_c4 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c4.finalize("Union[str, int]", non_nullable_schema, False)
        assert result == "Union[str, int] | None"

        # Case 5: Any type, nullable schema (required=True)
        # Contract: Optional due to schema.is_nullable=True. py_type is "Any" (Postcondition 1.b.ii)
        # Expect: "Any | None", import Optional
        ff_c5 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c5.finalize("Any", nullable_schema, True)
        assert result == "Any | None"

        # Case 6: Union type with None already, nullable schema (required=True)
        # Contract: Optional by usage, but py_type is "Union[..., None]" (Postcondition 1.b.iv)
        # Expect: "Union[str, int, None]", DO NOT import Optional again for this specific call path
        ff_c6 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c6.finalize("Union[str, int, None]", nullable_schema, True)
        assert result == "Union[str, int, None]"
        assert not ff_c6.context.import_collector.has_import("typing", "Optional")

        # Case 7: Nullable Union, nullable schema (required=True)
        # Contract: Optional due to schema.is_nullable=True. py_type is "Union[str, int]" (Postcondition 1.b.v)
        # Expect: "Optional[Union[str, int]]", import Optional
        ff_c7 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c7.finalize("Union[str, int]", nullable_schema, True)
        assert result == "Union[str, int] | None"

    def test_openapi31_nullable_handling(self, fresh_finalizer: TypeFinalizer) -> None:
        """
        Scenario:
            - Test the combination of type_parser.extract_primary_type_and_nullability
              and TypeFinalizer.finalize with OpenAPI 3.1 nullable types

        Expected Outcome:
            - Correctly applies Optional[...] based on the effective nullability.
        """
        # Schema: { "type": ["string", "null"] } -> IRSchema(type="string", is_nullable=True)
        string_or_null_schema = IRSchema(name="StringOrNull", type="string", is_nullable=True)

        # Test when required=True - use the provided fresh_finalizer
        result = fresh_finalizer.finalize("str", string_or_null_schema, True)
        assert result == "str | None"

        # Test when required=False
        # Need another fresh finalizer for isolated import check if we were to check imports here
        another_fresh_finalizer = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = another_fresh_finalizer.finalize("str", string_or_null_schema, False)
        assert result == "str | None"

        # Schema: { "type": "string" } (nullable not specified, treated as False by IRSchema default)
        plain_string_schema = IRSchema(name="PlainString", type="string", is_nullable=False)

        ff_plain_req_true = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_plain_req_true.finalize("str", plain_string_schema, True)  # required=True
        assert result == "str"

        ff_plain_req_false = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_plain_req_false.finalize("str", plain_string_schema, False)  # required=False
        assert result == "str | None"

        # Test complex list type that should be wrapped with Optional
        nullable_schema_list = IRSchema(
            name="NullableList", type="array", items=IRSchema(type="object"), is_nullable=True
        )
        ff_list = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_list.finalize("List[dict[str, Any]]", nullable_schema_list, True)
        assert result == "List[dict[str, Any]] | None", "Failed to properly handle nullable array"

        # Test multiple-type Union that should be wrapped with Optional
        nullable_union_schema = IRSchema(
            name="NullableUnion", any_of=[], is_nullable=True
        )  # any_of details not important here
        ff_union = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_union.finalize("Union[dict[str, Any], List[str], int]", nullable_union_schema, True)
        assert result == "Union[dict[str, Any], List[str], int] | None", "Failed to handle nullable union"

    def test_get_python_type_for_schema__schema_is_none__returns_any(self, context: RenderContext) -> None:
        """
        Scenario:
            - Call TypeHelper.get_python_type_for_schema with schema=None.
        Expected Outcome:
            - Returns "Any".
            - Adds "typing.Any" to imports.
        """
        # Arrange
        schemas: dict[str, IRSchema] = {}
        # Act
        result = TypeHelper.get_python_type_for_schema(None, schemas, context, required=True)
        # Assert
        assert result == "Any"
        assert context.import_collector.has_import("typing", "Any")


# Update tests for PrimitiveTypeResolver (formerly TypeHelper._get_primitive_type)
class TestPrimitiveTypeResolver:  # Renamed class
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def primitive_resolver(self, context: RenderContext) -> PrimitiveTypeResolver:
        return PrimitiveTypeResolver(context)

    @pytest.mark.parametrize(
        "schema_type, schema_format, expected_py_type, expected_imports",
        [
            ("integer", None, "int", []),
            ("number", None, "float", []),
            ("number", "float", "float", []),
            ("number", "double", "float", []),
            ("boolean", None, "bool", []),
            ("string", None, "str", []),
            ("string", "date", "date", [("datetime", "date")]),
            ("string", "date-time", "datetime", [("datetime", "datetime")]),
            ("string", "binary", "bytes", []),
            ("string", "byte", "str", []),  # 'byte' format should default to str if not binary
            ("string", "password", "str", []),  # Other string formats default to str
            ("object", None, None, []),  # Not a primitive type
            ("array", None, None, []),  # Not a primitive type
            ("unknown", None, None, []),  # Unknown type
        ],
    )
    def test_get_primitive_type__various_inputs__returns_expected(
        self,
        schema_type: str,
        schema_format: str | None,
        expected_py_type: str | None,
        expected_imports: List[tuple[str, str]],
        context: RenderContext,  # Keep context for direct manipulation if needed by test logic
        primitive_resolver: PrimitiveTypeResolver,  # Use resolver instance
    ) -> None:
        """
        Scenario:
            - Test PrimitiveTypeResolver.resolve with various schema types and formats.
            - Verifies correct Python type string and any necessary imports.
        Expected Outcome:
            - Returns the correct Python primitive type string or None if not a primitive.
            - Adds required imports (e.g., for datetime.date) to the context.
        """
        # Arrange
        schema = IRSchema(name="TestPrimitive", type=schema_type, format=schema_format)
        # Clear any existing imports on the resolver's context for accurate check
        primitive_resolver.context.import_collector = RenderContext(
            overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
        ).import_collector

        # Act
        result = primitive_resolver.resolve(schema)  # Call instance method

        # Assert
        assert result == expected_py_type
        # Check imports on the resolver's context
        for module, name in expected_imports:
            assert primitive_resolver.context.import_collector.has_import(
                module, name
            ), f"Expected import {module}.{name} not found for {schema_type}/{schema_format}"
        if not expected_imports and expected_py_type in ["date", "datetime"]:
            if expected_py_type == "date":
                assert not primitive_resolver.context.import_collector.has_import("datetime", "date")
            if expected_py_type == "datetime":
                assert not primitive_resolver.context.import_collector.has_import("datetime", "datetime")


# Update tests for ArrayTypeResolver (formerly TypeHelper._get_array_type)
class TestArrayTypeResolver:  # Renamed class
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def schemas_fixture(self) -> dict[str, IRSchema]:  # Renamed to avoid conflict with schemas param
        schemas = {
            "MyModel": IRSchema(name="MyModel", type="object", properties={"id": IRSchema(type="integer")}),
            "MyEnum": IRSchema(name="MyEnum", type="string", enum=["A", "B"]),
        }
        for schema in schemas.values():
            if schema.name:
                schema.generation_name = NameSanitizer.sanitize_class_name(schema.name)
                schema.final_module_stem = NameSanitizer.sanitize_module_name(schema.name)
        return schemas

    @pytest.fixture
    def array_resolver(self, context: RenderContext, schemas_fixture: dict[str, IRSchema]) -> ArrayTypeResolver:
        main_resolver = SchemaTypeResolver(context, schemas_fixture)
        return ArrayTypeResolver(context, schemas_fixture, main_resolver)

    @pytest.mark.parametrize(
        "items_schema_dict, expected_py_type, expected_typing_imports",
        [
            ({"type": "integer"}, "List[int]", ["List"]),
            ({"type": "string", "format": "date"}, "List[date]", ["List", "date"]),
            ({"$ref": "#/components/schemas/MyModel"}, "List[MyModel]", ["List"]),
            ({"$ref": "#/components/schemas/MyEnum"}, "List[MyEnum]", ["List"]),
            (
                {"type": "object", "properties": {"key": {"type": "string"}}},
                "List[dict[str, Any]]",
                ["List", "Dict", "Any"],
            ),
            ({"type": "object"}, "List[dict[str, Any]]", ["List", "Dict", "Any"]),
            ({"type": "array", "items": {"type": "string"}}, "List[List[str]]", ["List"]),
            ({}, "List[Any]", ["List", "Any"]),
            ({"items": None}, "List[Any]", ["List", "Any"]),
        ],
    )
    def test_resolve_array_type(  # Renamed method for clarity
        self,
        items_schema_dict: dict[str, Any],
        expected_py_type: str,
        expected_typing_imports: List[str],
        # context: RenderContext, # No longer directly used here, resolver has its own
        schemas_fixture: dict[str, IRSchema],  # Use renamed fixture
        array_resolver: ArrayTypeResolver,
    ) -> None:
        """
        Scenario:
            - Test ArrayTypeResolver.resolve with various 'items' sub-schemas.
        """
        # Arrange
        items_schema: Optional[IRSchema]
        if "$ref" in items_schema_dict:
            ref_name = items_schema_dict["$ref"].split("/")[-1]
            items_schema = schemas_fixture.get(ref_name)
            assert items_schema is not None, f"Test setup error: Referenced schema {ref_name} not in mock schemas."
        elif not items_schema_dict:
            items_schema = None
        # elif items_schema_dict.get("items") is None and "type" not in items_schema_dict:
        #     items_schema = IRSchema(name="AnonymousItems", type=None)
        else:
            # Special case for {"items": None} which should lead to items_schema = None
            if items_schema_dict.get("items") is None and len(items_schema_dict) == 1 and "items" in items_schema_dict:
                items_schema = None
            else:
                item_name = None  # Anonymous items
                items_schema = IRSchema(name=item_name, **items_schema_dict)

        array_schema = IRSchema(name="TestArray", type="array", items=items_schema)

        # Clear imports on the resolver's context for this specific call
        array_resolver.context.import_collector = RenderContext(
            overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
        ).import_collector

        # Act
        result = array_resolver.resolve(array_schema, parent_name_hint=array_schema.name)

        # Assert
        assert result == expected_py_type
        for name in expected_typing_imports:
            assert array_resolver.context.import_collector.has_import(
                "typing", name
            ) or array_resolver.context.import_collector.has_import(
                "datetime", name
            ), f"Expected typing/datetime import '{name}' not found for items: {items_schema_dict}"


# Update tests for CompositionTypeResolver (formerly TypeHelper._get_composition_type)
class TestCompositionTypeResolver:  # Renamed class
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def schemas(self) -> dict[str, IRSchema]:
        schemas_dict = {
            "SchemaA": IRSchema(name="SchemaA", type="object", properties={"a": IRSchema(type="string")}),
            "SchemaB": IRSchema(name="SchemaB", type="object", properties={"b": IRSchema(type="integer")}),
            "SchemaC": IRSchema(name="SchemaC", type="string", format="date"),
            "DataWrapper": IRSchema(
                name="DataWrapper",
                type="object",
                properties={"data": IRSchema(name="SchemaA_ref", type="SchemaA")},  # type here refers to SchemaA
                is_data_wrapper=True,
            ),
            "SimpleObject": IRSchema(name="SimpleObject", type="object"),
        }
        for schema in schemas_dict.values():
            if schema.name:
                schema.generation_name = NameSanitizer.sanitize_class_name(schema.name)
                schema.final_module_stem = NameSanitizer.sanitize_module_name(schema.name)
        return schemas_dict

    @pytest.fixture
    def composition_resolver(self, context: RenderContext, schemas: dict[str, IRSchema]) -> CompositionTypeResolver:
        main_resolver = SchemaTypeResolver(context, schemas)
        return CompositionTypeResolver(context, schemas, main_resolver)

    @pytest.mark.parametrize(
        "composition_type, sub_schemas_dicts, expected_py_type, expected_typing_imports",
        [
            # anyOf scenarios
            ("any_of", [{"type": "string"}, {"type": "integer"}], "Union[int, str]", ["Union"]),
            (
                "any_of",
                [{"$ref": "#/components/schemas/SchemaA"}, {"$ref": "#/components/schemas/SchemaB"}],
                "Union[SchemaA, SchemaB]",
                ["Union"],
            ),
            (
                "any_of",
                [{"type": "string"}, {"type": "null"}],
                "Union[Any, str]",
                ["Union", "Any"],
            ),  # null type resolves to Any, so intermediate is Union[Any, str]
            ("any_of", [], "Any", ["Any"]),  # Empty anyOf
            # oneOf scenarios (currently treated like anyOf by TypeFinalizer for Union)
            ("one_of", [{"type": "string"}, {"type": "integer"}], "Union[int, str]", ["Union"]),
            (
                "one_of",
                [{"$ref": "#/components/schemas/SchemaA"}, {"$ref": "#/components/schemas/SchemaB"}],
                "Union[SchemaA, SchemaB]",
                ["Union"],
            ),
            # allOf scenarios
            # 1. Simple allOf with one item (should effectively be that item's type)
            ("all_of", [{"$ref": "#/components/schemas/SchemaA"}], "SchemaA", []),
            # 2. allOf with a data wrapper (should unwrap to the inner type if helper supports it)
            #    TypeFinalizer._get_composition_type might not do unwrapping itself, but get_python_type_for_schema
            #    might. For now, let's assume _get_composition_type returns the type of the single element for
            #    allOf=[Schema].
            ("all_of", [{"$ref": "#/components/schemas/DataWrapper"}], "DataWrapper", []),
            # 3. allOf with multiple distinct object types - this is complex. TypeFinalizer might return the first, or
            #    Any, or a specific name if one is dominant. The current TypeFinalizer._get_composition_type for allOf
            #    returns the type of the *first* schema in the list.
            (
                "all_of",
                [{"$ref": "#/components/schemas/SchemaA"}, {"$ref": "#/components/schemas/SchemaB"}],
                "SchemaA",
                [],
            ),
            (
                "all_of",
                [
                    {"type": "object", "properties": {"x": {"type": "string"}}},
                    {"$ref": "#/components/schemas/SimpleObject"},
                ],
                "dict[str, Any]",
                ["Dict", "Any"],
            ),  # First is anonymous object
            ("all_of", [], "Any", ["Any"]),  # Empty allOf
        ],
    )
    def test_get_composition_type(
        self,
        composition_type: str,
        sub_schemas_dicts: List[dict[str, Any]],
        expected_py_type: str,
        expected_typing_imports: List[str],
        context: RenderContext,
        schemas: dict[str, IRSchema],
        composition_resolver: CompositionTypeResolver,
    ) -> None:
        """
        Scenario:
            - Test CompositionTypeResolver.resolve with anyOf, oneOf, allOf.
            - Verifies correct Python type string and typing imports.
        Expected Outcome:
            - Returns the correct Python type string (e.g., Union[...], specific type for allOf).
            - Adds required imports to the context.
        """
        # Arrange
        sub_schemas_irs: List[IRSchema] = []
        for sc_dict in sub_schemas_dicts:
            if "$ref" in sc_dict:
                ref_name = sc_dict["$ref"].split("/")[-1]
                ir_sc = schemas.get(ref_name)
                assert ir_sc is not None, f"Test setup error: Referenced schema {ref_name} not in mock schemas."
                sub_schemas_irs.append(ir_sc)
            else:
                sub_schemas_irs.append(IRSchema(name=None, **sc_dict))

        parent_schema_name = f"Test{composition_type.capitalize()}Schema"
        parent_schema_dict = {
            composition_type: sub_schemas_irs,
            "name": parent_schema_name,
            "type": "object",
        }  # Ensure type is set if not a composition keyword
        if composition_type in ["any_of", "one_of", "all_of"]:
            parent_schema_dict["type"] = None  # type: ignore # Type should be None if a composition keyword is present

        parent_schema = IRSchema(**parent_schema_dict)  # type: ignore

        # Clear imports on the resolver's context for this specific call
        composition_resolver.context.import_collector = RenderContext(
            overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
        ).import_collector

        # Act
        result = composition_resolver.resolve(parent_schema)

        # Assert
        if composition_type in ["any_of", "one_of"] and "Optional[" in expected_py_type:
            non_none_type = expected_py_type.replace("Optional[", "").replace("]", "")
            if non_none_type != "Any":
                # Sorting is ['None', 'ActualType'] for Union[None, ActualType]
                actual_types = sorted(["None", non_none_type])
                expected_intermediate_union = f"Union[{', '.join(actual_types)}]"
                assert result == expected_intermediate_union
            else:
                assert result == "Any"
        else:
            assert result == expected_py_type

        for name in expected_typing_imports:
            assert composition_resolver.context.import_collector.has_import(
                "typing", name
            ) or composition_resolver.context.import_collector.has_import(
                "datetime", name
            ), f"Expected typing/datetime import '{name}' not found for {composition_type} with items: {sub_schemas_dicts}"


# Update tests for NamedTypeResolver (formerly TypeHelper._get_named_or_enum_type)
class TestNamedTypeResolver:  # Renamed class
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def base_schemas(self) -> dict[str, IRSchema]:
        schemas_dict = {
            "ReferencedModel": IRSchema(
                name="ReferencedModel", type="object", properties={"id": IRSchema(type="integer")}
            ),
            "MyEnum": IRSchema(name="MyEnum", type="string", enum=["A", "B"]),
            "ComplexModel": IRSchema(name="ComplexModel", type="object", properties={"field": IRSchema(type="string")}),
            "SimpleEnum": IRSchema(name="SimpleEnum", type="string", enum=["S1", "S2"]),
            "MyStringAlias": IRSchema(name="MyStringAlias", type="string"),
            "MyIntegerAlias": IRSchema(name="MyIntegerAlias", type="integer"),
            "MyNumberAlias": IRSchema(name="MyNumberAlias", type="number"),
            "MyBooleanAlias": IRSchema(name="MyBooleanAlias", type="boolean"),
            "MyArrayAlias": IRSchema(name="MyArrayAlias", type="array", items=IRSchema(type="string")),
            "MyComplexArrayAlias": IRSchema(
                name="MyComplexArrayAlias", type="array", items=IRSchema(type="ReferencedModel")
            ),
            "MyObjectAlias": IRSchema(name="MyObjectAlias", type="object"),
        }
        for schema in schemas_dict.values():
            if schema.name:
                schema.generation_name = NameSanitizer.sanitize_class_name(schema.name)
                schema.final_module_stem = NameSanitizer.sanitize_module_name(schema.name)
        return schemas_dict

    @pytest.fixture
    def named_resolver(self, context: RenderContext, base_schemas: dict[str, IRSchema]) -> NamedTypeResolver:
        return NamedTypeResolver(context, base_schemas)

    @pytest.mark.parametrize(
        "test_id, input_schema_dict, expected_return_type, expected_model_imports",
        [
            # 1. Named Complex Model (not an alias-like structure)
            (
                "named_complex_model",
                {"name": "ComplexModel"},
                "ComplexModel",
                [("pkg.models.complex_model", "ComplexModel")],
            ),
            # 2. Named Simple Enum (not an alias-like structure)
            (
                "named_simple_enum",
                {"name": "SimpleEnum"},
                "SimpleEnum",
                [("pkg.models.simple_enum", "SimpleEnum")],
            ),
            # 3. Structurally Alias-like to known primitive (string)
            (
                "alias_to_primitive_string",
                {"name": "MyStringAlias"},
                "MyStringAlias",
                [("pkg.models.my_string_alias", "MyStringAlias")],
            ),
            # 4. Structurally Alias-like to known primitive (integer)
            (
                "alias_to_primitive_integer",
                {"name": "MyIntegerAlias"},
                "MyIntegerAlias",
                [("pkg.models.my_integer_alias", "MyIntegerAlias")],
            ),
            # 5. Structurally Alias-like to known primitive (number)
            (
                "alias_to_primitive_number",
                {"name": "MyNumberAlias"},
                "MyNumberAlias",
                [("pkg.models.my_number_alias", "MyNumberAlias")],
            ),
            # 6. Structurally Alias-like to known primitive (boolean)
            (
                "alias_to_primitive_boolean",
                {"name": "MyBooleanAlias"},
                "MyBooleanAlias",
                [("pkg.models.my_boolean_alias", "MyBooleanAlias")],
            ),
            # 7. Structurally Alias-like to array
            (
                "alias_to_array",
                {"name": "MyArrayAlias"},
                "MyArrayAlias",
                [("pkg.models.my_array_alias", "MyArrayAlias")],
            ),
            # 8. Structurally Alias-like to object (no props) - treated as class reference
            (
                "alias_to_object_no_props",
                {"name": "MyObjectAlias"},
                "MyObjectAlias",
                [("pkg.models.my_object_alias", "MyObjectAlias")],
            ),
            # 9. Structurally Alias-like to UNKNOWN base type
            (
                "alias_to_unknown_type",
                {"name": "MyUnknownAlias", "type": "some_custom_unknown_type"},
                None,
                [],
            ),
            # 10. Named Inline Enum (schema has name and enum, but not in global `schemas` dict)
            # This scenario implies the input `schema` to _get_named_or_enum_type IS the definition.
            (
                "named_inline_enum_string",
                {"name": "StatusEnum", "type": "string", "enum": ["active", "inactive"]},
                "StatusEnum",
                [("pkg.models.status_enum", "StatusEnum")],
            ),
            (
                "named_inline_enum_integer",
                {"name": "NumericStatusEnum", "type": "integer", "enum": [1, 2, 3]},
                "NumericStatusEnum",
                [("pkg.models.numeric_status_enum", "NumericStatusEnum")],
            ),
            # 11. Unnamed Enum (string, type not specified -> defaults to string)
            ("unnamed_enum_default_string", {"enum": ["X", "Y"]}, "str", []),
            # 12. Unnamed Enum (string, type explicitly string)
            ("unnamed_enum_explicit_string", {"type": "string", "enum": ["X", "Y"]}, "str", []),
            # 13. Unnamed Enum (integer)
            ("unnamed_enum_integer", {"type": "integer", "enum": [10, 20]}, "int", []),
            # 14. Schema name not in global schemas, not an inline enum (e.g. an unresolved ref or direct use of a
            #     new named type)
            (
                "named_schema_not_in_globals_not_enum",
                {"name": "NotInGlobals", "type": "object"},
                None,
                [],
            ),
            # 15. Input schema itself has no name (anonymous)
            (
                "anonymous_schema_no_enum",
                {"type": "object", "properties": {"field": {"type": "string"}}},
                None,
                [],
            ),
        ],
    )
    def test_get_named_or_enum_type(
        self,
        test_id: str,
        input_schema_dict: dict[str, Any],
        expected_return_type: str | None,
        expected_model_imports: List[tuple[str, str]],
        context: RenderContext,
        base_schemas: dict[str, IRSchema],
        named_resolver: NamedTypeResolver,
    ) -> None:
        """
        Scenario:
            - Test NamedTypeResolver.resolve with various input schemas:
                - References to globally defined schemas (complex models, enums, aliases to primitives/objects).
                - Inline definitions of named enums.
                - Inline definitions of unnamed enums.
                - Schemas not found in global registry.
        Expected Outcome:
            - Returns the correct Python type string (e.g., a class name for a model/enum, None for aliases to be
              resolved structurally, base types for unnamed enums).
            - Adds necessary model imports to the context if a named model/enum is returned.
            - Handles various structural conditions for alias-like schemas correctly.
        """
        # Arrange
        input_schema = IRSchema(**input_schema_dict)

        # Clear imports on the resolver's context for this specific test run
        # NamedTypeResolver takes all_schemas at init, so the context it uses for imports is the one passed at init.
        # We need a fresh resolver with a fresh context for isolated import checks.
        fresh_context_for_test = RenderContext(
            overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
        )
        current_resolver_for_test = NamedTypeResolver(fresh_context_for_test, base_schemas)

        # Act
        result = current_resolver_for_test.resolve(input_schema)

        # Assert
        assert result == expected_return_type, f"[{test_id}] Return type mismatch"

        # Check imports on the fresh_context_for_test
        if expected_model_imports:
            for module, name in expected_model_imports:
                assert fresh_context_for_test.import_collector.has_import(
                    module, name
                ), f"[{test_id}] Expected model import {module}.{name} not found."
        else:
            # Check for unexpected model imports if none are expected
            if not expected_model_imports:
                all_imported_modules = (
                    set(fresh_context_for_test.import_collector.imports.keys())
                    | set(fresh_context_for_test.import_collector.relative_imports.keys())
                    | fresh_context_for_test.import_collector.plain_imports
                )

                for imp_module in all_imported_modules:
                    # Allow typing, core, and stdlib imports
                    # Construct the expected core module path prefix for comparison
                    core_pkg_prefix = f"{context.get_current_package_name_for_generated_code()}.core"
                    if (
                        imp_module.startswith("typing")
                        or imp_module.startswith(core_pkg_prefix)
                        or imp_module in sys.stdlib_module_names
                    ):
                        continue
                    # Any other import is unexpected if expected_model_imports is empty
                    assert False, (
                        f"[{test_id}] Unexpected model-like import found: '{imp_module}' when none expected. "
                        f"Return type was: '{result}'."
                    )
            else:
                # Existing logic for expected_model_imports
                pass


# Update tests for ObjectTypeResolver (formerly TypeHelper._get_object_type)
class TestObjectTypeResolver:  # Renamed class
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def schemas(self) -> dict[str, IRSchema]:
        schemas_dict = {
            "ReferencedModel": IRSchema(
                name="ReferencedModel", type="object", properties={"id": IRSchema(type="integer")}
            ),
            "StringType": IRSchema(name="StringType", type="string"),
            # Additions for the failing tests:
            "MyNamedObject": IRSchema(name="MyNamedObject", type="object", additional_properties=False),
            "MyNamedEmptyPropsObject": IRSchema(
                name="MyNamedEmptyPropsObject", type="object", additional_properties=False
            ),
        }
        # Ensure ReferencedModel also gets its names set if it's used in ObjectTypeResolver tests
        # All schemas in this dict should be prepared
        for schema in schemas_dict.values():
            if schema.name:  # Should always be true for these
                schema.generation_name = NameSanitizer.sanitize_class_name(schema.name)
                schema.final_module_stem = NameSanitizer.sanitize_module_name(schema.name)
        return schemas_dict

    @pytest.fixture
    def object_resolver(self, context: RenderContext, schemas: dict[str, IRSchema]) -> ObjectTypeResolver:
        main_resolver = SchemaTypeResolver(context, schemas)
        return ObjectTypeResolver(context, schemas, main_resolver)

    @pytest.mark.parametrize(
        "test_id, input_schema_dict, expected_return_type, expected_imports",
        [
            # 1. additionalProperties: true
            (
                "additional_props_true",
                {"type": "object", "additional_properties": True},
                "dict[str, Any]",
                ["Dict", "Any"],
            ),
            # 2. additionalProperties: {schema} (referencing a primitive type)
            (
                "additional_props_schema_primitive",
                {"type": "object", "additional_properties": {"type": "string"}},
                "dict[str, str]",
                ["Dict"],
            ),
            # 3. additionalProperties: {schema} (referencing a named model)
            (
                "additional_props_schema_ref_model",
                {"type": "object", "additional_properties": {"$ref": "#/components/schemas/ReferencedModel"}},
                "dict[str, ReferencedModel]",
                ["Dict", ("..models.referenced_model", "ReferencedModel")],
            ),
            # 4. Anonymous object, no properties, no explicit additionalProperties (should default to dict[str, Any])
            ("anon_obj_no_props_no_add_props", {"type": "object"}, "dict[str, Any]", ["Dict", "Any"]),
            # 5. Anonymous object WITH properties (should warn and become dict[str, Any]) - COVERAGE (lines 254-260)
            (
                "anon_obj_with_props",
                {"type": "object", "properties": {"key": {"type": "string"}}},
                "dict[str, Any]",
                ["Dict", "Any"],
            ),
            # 6. Named object, no properties, additionalProperties: false (should return its own name) - COVERAGE (line 267-272)
            (
                "named_obj_no_props_add_props_false",
                {"name": "MyNamedObject", "type": "object", "additional_properties": False},
                "MyNamedObject",
                [("pkg.models.my_named_object", "MyNamedObject")],
            ),
            # 7. Named object, no properties, additionalProperties: {} (empty schema, restrictive, now False) - COVERAGE (line 267-272)
            (
                "named_obj_no_props_add_props_empty_schema",
                {
                    "name": "MyNamedEmptyPropsObject",
                    "type": "object",
                    "additional_properties": False,
                },
                "MyNamedEmptyPropsObject",
                [("pkg.models.my_named_empty_props_object", "MyNamedEmptyPropsObject")],
            ),
            # 8. Anonymous object, no properties, additionalProperties: false (should become Any) - COVERAGE (line 273-278)
            ("anon_obj_no_props_add_props_false", {"type": "object", "additional_properties": False}, "Any", ["Any"]),
            # 9. Anonymous object, no properties, additionalProperties: {} (empty schema, restrictive) - COVERAGE (line 273-278)
            (
                "anon_obj_no_props_add_props_empty_schema",
                {"type": "object", "additional_properties": {}},
                "Any",
                ["Any"],
            ),
            # 10. Not an object type (should return None)
            ("not_an_object", {"type": "string"}, None, []),
            # 11. Named object with properties (should be handled by _get_named_or_enum_type, so _get_object_type might not see it often directly unless called in specific ways)
            # For _get_object_type, if it gets a named object with props, and it wasn't handled by additionalProperties,
            # it falls through to the `if schema.name:` block, returning its own name.
            (
                "named_obj_with_props_direct_call_fallback",
                {"name": "RegularModel", "type": "object", "properties": {"id": {"type": "integer"}}},
                "RegularModel",
                [],
            ),
        ],
    )
    def test_get_object_type(
        self,
        test_id: str,
        input_schema_dict: dict[str, Any],
        expected_return_type: str | None,
        expected_imports: List[Union[str, Tuple[str, str]]],
        context: RenderContext,
        schemas: dict[str, IRSchema],
        object_resolver: ObjectTypeResolver,
    ) -> None:
        """
        Scenario:
            - Test ObjectTypeResolver.resolve with various object schema configurations:
                - additionalProperties (true, schema, false, empty schema)
                - Anonymous objects (with/without properties)
                - Named objects (with/without properties, different additionalProperties)
                - Non-object types.
        Expected Outcome:
            - Returns the correct Python type string (e.g., dict[str, Any], model name, Any, or None).
            - Adds necessary typing imports (Dict, Any) to the context.
            - Correctly handles fallbacks and specific conditions for object variations.
        """
        # Arrange
        if "additional_properties" in input_schema_dict and isinstance(
            input_schema_dict["additional_properties"], dict
        ):
            ap_dict = input_schema_dict["additional_properties"]
            if "$ref" in ap_dict:
                ref_name = ap_dict["$ref"].split("/")[-1]
                actual_ref_schema = schemas.get(ref_name)
                assert actual_ref_schema is not None, f"Test setup: $ref {ref_name} not found in mock schemas"
                # For testing, create an IRSchema that just holds the name, actual resolution done by resolver
                input_schema_dict["additional_properties"] = IRSchema(name=ref_name, type=actual_ref_schema.type)
            elif ap_dict:  # Non-empty dict, not a $ref
                input_schema_dict["additional_properties"] = IRSchema(**ap_dict)
            # else: empty dict {} for additionalProperties, becomes IRSchema() with defaults

        input_schema = IRSchema(**input_schema_dict)

        # Clear imports on the resolver's context for this specific test run
        object_resolver.context.import_collector = RenderContext(
            overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
        ).import_collector

        # Act
        result = object_resolver.resolve(input_schema, parent_schema_name_for_anon_promotion=None)

        # Assert
        assert result == expected_return_type, f"[{test_id}] Return type mismatch"

        for item in expected_imports:
            if isinstance(item, tuple):
                module, name = item
                assert object_resolver.context.import_collector.has_import(
                    module, name
                ), f"[{test_id}] Expected model import {module}.{name} not found."
            else:
                assert object_resolver.context.import_collector.has_import(
                    "typing", item
                ), f"[{test_id}] Expected typing import '{item}' not found."

        # Check that no unexpected model imports were added if only typing imports were expected
        if all(isinstance(item, str) for item in expected_imports):
            if hasattr(object_resolver.context.import_collector, "imports"):
                for imp_module in object_resolver.context.import_collector.imports.keys():
                    if (
                        imp_module != "typing"
                        and not imp_module.startswith("pkg.")
                        and not imp_module.startswith(object_resolver.context.core_package_name)
                    ):
                        # A bit more nuanced: check if it's an internal non-typing import that wasn't expected
                        is_unexpected_model_import = True
                        # Allow known system/datetime imports
                        if imp_module in [
                            "datetime",
                            "os",
                            "sys",
                            "re",
                            "json",
                            "collections",
                            "enum",
                            "pathlib",
                            "abc",
                            "decimal",
                            "dataclasses",
                        ]:
                            is_unexpected_model_import = False

                        if is_unexpected_model_import:
                            assert not imp_module.startswith(
                                tuple(s.split(".")[0] for s in schemas.keys())
                            ), f"[{test_id}] Unexpected model-like import found: {imp_module} when only typing imports expected. Expected: {expected_imports}"
                            # Stricter check for any non-typing, non-core, non-stdlib import
                            assert (
                                False
                            ), f"[{test_id}] Unexpected non-typing/non-core/non-stdlib import found: {imp_module}. Expected only: {expected_imports}"


class TestTypeHelperGetPythonTypeForSchemaFallthroughs:
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def empty_schemas(self) -> dict[str, IRSchema]:
        return {}

    def test_get_python_type_for_schema__fallthrough_to_primitive(
        self, context: RenderContext, empty_schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario:
            - schema is anonymous (name=None) and not a special enum.
            - resolve_alias_target = False.
            - _get_named_or_enum_type returns None (or its equivalent in new structure).
            - Schema is structurally a primitive type (e.g., type: "string").
        Expected Outcome:
            - Correctly resolves to "str".
        """
        schema = IRSchema(name=None, type="string")
        result = TypeHelper.get_python_type_for_schema(
            schema, empty_schemas, context, required=True, resolve_alias_target=False
        )
        assert result == "str"

    def test_get_python_type_for_schema__fallthrough_to_composition(
        self, context: RenderContext, empty_schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario:
            - schema is anonymous, not an enum, resolve_alias_target=False.
            - Schema is structurally a composition type (e.g., anyOf).
        Expected Outcome:
            - Correctly resolves to Union type.
        """
        schema = IRSchema(
            name=None,
            any_of=[
                IRSchema(type="string"),
                IRSchema(type="integer"),
            ],
        )
        result = TypeHelper.get_python_type_for_schema(
            schema, empty_schemas, context, required=True, resolve_alias_target=False
        )
        assert result == "Union[int, str]"
        assert context.import_collector.has_import("typing", "Union")

    def test_get_python_type_for_schema__fallthrough_to_array(
        self, context: RenderContext, empty_schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario:
            - schema is anonymous, not an enum, resolve_alias_target=False.
            - Schema is structurally an array type.
        Expected Outcome:
            - Correctly resolves to List type.
        """
        schema = IRSchema(name=None, type="array", items=IRSchema(type="integer"))
        result = TypeHelper.get_python_type_for_schema(
            schema, empty_schemas, context, required=True, resolve_alias_target=False
        )
        assert result == "List[int]"
        assert context.import_collector.has_import("typing", "List")

    def test_get_python_type_for_schema__fallthrough_to_object(
        self, context: RenderContext, empty_schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario:
            - schema is anonymous, not an enum, resolve_alias_target=False.
            - Schema is structurally an object type with additionalProperties:true.
        Expected Outcome:
            - Correctly resolves to dict[str, Any].
        """
        schema = IRSchema(name=None, type="object", additional_properties=True)
        result = TypeHelper.get_python_type_for_schema(
            schema, empty_schemas, context, required=True, resolve_alias_target=False
        )
        assert result == "dict[str, Any]"
        assert context.import_collector.has_import("typing", "Dict")
        assert context.import_collector.has_import("typing", "Any")

    def test_get_python_type_for_schema__fallthrough_to_unknown_any(
        self, context: RenderContext, empty_schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario:
            - schema is anonymous, not an enum, resolve_alias_target=False.
            - Schema type is unknown and not handled by other specific type getters.
        Expected Outcome:
            - Correctly resolves to Any.
        """
        schema = IRSchema(name=None, type="somecompletelyunknownschema")
        result = TypeHelper.get_python_type_for_schema(
            schema, empty_schemas, context, required=True, resolve_alias_target=False
        )
        assert result == "Any"
        assert context.import_collector.has_import("typing", "Any")


class TestTypeHelperModelToModelImports:
    @pytest.fixture
    def model_import_render_context(self, tmp_path: Path) -> RenderContext:
        project_root = tmp_path
        gen_pkg_root = project_root / "out_pkg"
        # Ensure models directory exists under the package root
        models_dir = gen_pkg_root / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Mock FileManager as it's not directly used by TypeHelper logic being tested
        mock_fm = MagicMock(spec=FileManager)

        return RenderContext(
            file_manager=mock_fm,
            package_root_for_generated_code=str(gen_pkg_root),
            overall_project_root=str(project_root),
            core_package_name="out_pkg.core",  # Default or example
        )

    def test_get_python_type_for_schema__model_to_model_import_same_dir(
        self, model_import_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: Generating SchemaA (in out_pkg/models/schema_a.py), which has a field
                  of type SchemaB (defined in out_pkg/models/schema_b.py).
        Expected: TypeHelper should return "SchemaB" as the type string, and
                  RenderContext should have a relative import:
                  from .schema_b import SchemaB
        """
        context = model_import_render_context
        # Ensure package_root_for_generated_code is not None before using it with Path
        assert context.package_root_for_generated_code is not None
        gen_pkg_root = Path(context.package_root_for_generated_code)
        models_dir = gen_pkg_root / "models"  # This was already created by the fixture

        # File being generated
        # Use NameSanitizer for module name consistency if schema names can have special chars
        schema_a_module_name = NameSanitizer.sanitize_module_name("SchemaA")
        current_file_path = models_dir / f"{schema_a_module_name}.py"
        current_file_path.touch()
        context.set_current_file(str(current_file_path))

        # Target file to be imported (must exist for path calculations in RenderContext)
        schema_b_name = "SchemaB"
        schema_b_module_name = NameSanitizer.sanitize_module_name(schema_b_name)
        target_schema_b_file_path = models_dir / f"{schema_b_module_name}.py"
        target_schema_b_file_path.touch()

        # Define SchemaB
        schema_b_def = IRSchema(name=schema_b_name, type="object", properties={"id": IRSchema(type="integer")})
        assert schema_b_def.name is not None  # Ensure name is not None for sanitizer
        schema_b_def.generation_name = NameSanitizer.sanitize_class_name(schema_b_def.name)
        schema_b_def.final_module_stem = NameSanitizer.sanitize_module_name(schema_b_def.name)

        # Manually set generation_name and final_module_stem for the target schema,
        # as TypeHelper expects these to be pre-processed.

        # Define SchemaA's property that references SchemaB
        field_referencing_schema_b = IRSchema(type=schema_b_name)  # 'type' holds the ref name

        all_schemas_dict = {schema_b_name: schema_b_def}
        schema_a_class_name = NameSanitizer.sanitize_class_name("SchemaA")

        # Act
        returned_type_str = TypeHelper.get_python_type_for_schema(
            schema=field_referencing_schema_b,
            all_schemas=all_schemas_dict,
            context=context,
            required=True,
            parent_schema_name=schema_a_class_name,
        )

        # Assert type string
        expected_class_name_b = NameSanitizer.sanitize_class_name(schema_b_name)
        assert returned_type_str == expected_class_name_b

        # Assert import (unified system uses relative imports)
        expected_relative_module = f".{schema_b_module_name}"
        assert context.import_collector.has_import(expected_relative_module, expected_class_name_b), (
            f"Expected import 'from {expected_relative_module} import {expected_class_name_b}' not found. "
            f"Relative imports: {context.import_collector.relative_imports}, "
            f"Absolute imports: {context.import_collector.imports}"
        )

        # Verify rendered import string too
        # Note: ImportCollector.get_formatted_imports() is used by RenderContext.render_imports()
        # We need to ensure the specific import is present in the collector's state that get_formatted_imports would use.
        # The has_import check is good. For rendered output, we'd look at the final string.
        rendered_imports = context.render_imports()
        expected_import_line = f"from {expected_relative_module} import {expected_class_name_b}"
        assert (
            expected_import_line in rendered_imports
        ), f"Expected import line '{expected_import_line}' not in rendered imports:\\n{rendered_imports}"

    def test_get_python_type_for_schema__optional_model_import_same_dir(
        self, model_import_render_context: RenderContext, tmp_path: Path
    ) -> None:
        """
        Scenario: Generating SchemaA (in out_pkg/models/schema_a.py), which has a field
                  of type Optional[SchemaB] (SchemaB defined in out_pkg/models/schema_b.py).
        Expected: TypeHelper should return "Optional[SchemaB]" as the type string, and
                  RenderContext should have a relative import for SchemaB:
                  from .schema_b import SchemaB
                  and an import for Optional from typing.
        """
        context = model_import_render_context
        assert context.package_root_for_generated_code is not None
        gen_pkg_root = Path(context.package_root_for_generated_code)
        models_dir = gen_pkg_root / "models"

        schema_a_module_name = NameSanitizer.sanitize_module_name("SchemaAOpt")
        current_file_path = models_dir / f"{schema_a_module_name}.py"
        current_file_path.touch()
        context.set_current_file(str(current_file_path))

        schema_b_name = "SchemaBOpt"
        schema_b_module_name = NameSanitizer.sanitize_module_name(schema_b_name)
        target_schema_b_file_path = models_dir / f"{schema_b_module_name}.py"
        target_schema_b_file_path.touch()

        schema_b_def = IRSchema(name=schema_b_name, type="object", properties={"id": IRSchema(type="integer")})
        assert schema_b_def.name is not None  # Ensure name is not None for sanitizer
        schema_b_def.generation_name = NameSanitizer.sanitize_class_name(schema_b_def.name)
        schema_b_def.final_module_stem = NameSanitizer.sanitize_module_name(schema_b_def.name)

        # Field in SchemaAOpt is: field_b: Optional[SchemaBOpt]
        # Represented as IRSchema(type="SchemaBOpt", is_nullable=True)
        # The 'required' flag for get_python_type_for_schema also plays a role in Optionality.
        # If a field is schema.is_nullable=True, it's Optional regardless of 'required'.
        # If schema.is_nullable=False but required=False, it's also Optional.
        field_referencing_schema_b = IRSchema(type=schema_b_name, is_nullable=True)

        all_schemas_dict = {schema_b_name: schema_b_def}
        schema_a_class_name = NameSanitizer.sanitize_class_name("SchemaAOpt")

        # Act
        # Pass required=True because the field itself exists; its *type* is Optional.
        returned_type_str = TypeHelper.get_python_type_for_schema(
            schema=field_referencing_schema_b,
            all_schemas=all_schemas_dict,
            context=context,
            required=True,  # Field exists, its type is Optional due to is_nullable=True
            parent_schema_name=schema_a_class_name,
        )

        # Assert type string
        expected_class_name_b = NameSanitizer.sanitize_class_name(schema_b_name)
        assert returned_type_str == f"{expected_class_name_b} | None"

        # Assert import for SchemaB (unified system uses relative imports)
        expected_relative_module_b = f".{schema_b_module_name}"
        assert context.import_collector.has_import(
            expected_relative_module_b, expected_class_name_b
        ), f"Expected SchemaB import 'from {expected_relative_module_b} import {expected_class_name_b}' not found."

        # Assert import for Optional

        # Verify rendered import string too
        rendered_imports = context.render_imports()
        expected_import_line_schema_b = f"from {expected_relative_module_b} import {expected_class_name_b}"

        assert (
            expected_import_line_schema_b in rendered_imports
        ), f"Expected SchemaB import line '{expected_import_line_schema_b}' not in rendered imports:\\n{rendered_imports}"