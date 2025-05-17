"""
Tests for TypeHelper methods that support type conversion and cleaning.
"""

import re
from typing import Any, Dict, List, Optional

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
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
            ("simple_dict", "Dict[str, Any]", "Dict[str, Any]"),
            ("simple_list", "List[str]", "List[str]"),
            ("simple_optional", "Optional[str]", "Optional[str]"),
            # Common error cases from OpenAPI 3.1 nullable handling
            ("dict_with_none", "Dict[str, Any, None]", "Dict[str, Any]"),
            ("list_with_none", "List[JsonValue, None]", "List[JsonValue]"),
            ("optional_with_none", "Optional[Any, None]", "Optional[Any]"),
            # More complex nested types
            ("nested_dict", "Dict[str, Dict[str, Any, None]]", "Dict[str, Dict[str, Any]]"),
            ("nested_list", "List[List[str, None]]", "List[List[str]]"),
            (
                "complex_union",
                "Union[Dict[str, Any, None], List[str, None], Optional[int, None]]",
                "Union[Dict[str, Any], List[str], Optional[int]]",
            ),
            # OpenAPI 3.1 complex nullable cases
            ("openapi_31_list_none", "List[Union[Dict[str, Any], None]]", "List[Union[Dict[str, Any], None]]"),
            ("list_with_multi_params", "List[str, int, bool, None]", "List[str]"),
            ("dict_with_multi_params", "Dict[str, int, bool, None]", "Dict[str, int]"),
            # Deeply nested structures
            (
                "deep_nested_union",
                "Union[Dict[str, List[Dict[str, Any, None], None]], List[Dict[str, Any, None], None]]",
                "Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]",
            ),
            # Real-world complex cases from the errors we've encountered
            (
                "embedding_flat_case",
                "Union[Dict[str, Any], List[Union[Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None], None], Optional[Any], bool, float, str]",
                "Union[Dict[str, Any], List[Union[Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None]], Optional[Any], bool, float, str]",
            ),
            # Edge cases
            ("empty_string", "", ""),
            ("no_brackets", "AnyType", "AnyType"),
            ("incomplete_syntax", "Dict[str,", "Dict[str,"),
            ("empty_union", "Union[]", "Any"),
            ("optional_none", "Optional[None]", "Optional[Any]"),
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
        complex_type = "Union[Dict[str, List[Dict[str, Any, None], None]], List[Union[Dict[str, Any, None], str, None]], Optional[Dict[str, Union[str, int, None], None]]]"

        expected = "Union[Dict[str, List[Dict[str, Any]]], List[Union[Dict[str, Any], str, None]], Optional[Dict[str, Union[str, int, None]]]]"

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
            "Dict[str, Any], "
            "List["
            "Union["
            "Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None"
            "], "
            "None"
            "], "
            "Optional[Any], "
            "bool, "
            "float, "
            "str"
            "]"
        )

        expected = (
            "Union["
            "Dict[str, Any], "
            "List["
            "Union["
            "Dict[str, Any], List[JsonValue], Optional[Any], bool, float, str, None"
            "]"
            "], "
            "Optional[Any], "
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
        "py_type", ["str", "List[int]", "Union[str, bool]", "Any", "Optional[str]", "Union[str, None]"]
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
        assert not fresh_finalizer.context.import_collector.has_import("typing", "Optional"), (
            f"Optional was incorrectly added for {py_type} with non_nullable_schema, required=True"
        )

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
        assert not another_fresh_finalizer.context.import_collector.has_import("typing", "Optional"), (
            f"Optional was incorrectly added for {py_type} with none_nullable_schema, required=True"
        )

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
        assert ff1.finalize("str", non_nullable_schema, False) == "Optional[str]"
        assert ff1.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.ii ("Any")
        ff2 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff2.finalize("Any", non_nullable_schema, False) == "Optional[Any]"
        assert ff2.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.iii (already "Optional[...]")
        ff3 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff3.finalize("Optional[int]", non_nullable_schema, False) == "Optional[int]"
        assert not ff3.context.import_collector.has_import("typing", "Optional"), (
            "Optional added when py_type was already Optional[]"
        )

        # Postcondition 1.b.iv (already "Union[..., None]")
        ff4 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff4.finalize("Union[int, float, None]", non_nullable_schema, False) == "Union[int, float, None]"
        assert not ff4.context.import_collector.has_import("typing", "Optional"), (
            "Optional added when py_type was Union[..., None]"
        )

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
        assert ff7.finalize("Union[int, float]", non_nullable_schema, False) == "Optional[Union[int, float]]"
        assert ff7.context.import_collector.has_import("typing", "Optional")

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
        assert ff1.finalize("str", nullable_schema, True) == "Optional[str]"
        assert ff1.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.ii ("Any")
        ff2 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff2.finalize("Any", nullable_schema, True) == "Optional[Any]"
        assert ff2.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.iii (already "Optional[...]")
        ff3 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff3.finalize("Optional[int]", nullable_schema, True) == "Optional[int]"
        assert not ff3.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.iv (already "Union[..., None]")
        ff4 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff4.finalize("Union[int, float, None]", nullable_schema, True) == "Union[int, float, None]"
        assert not ff4.context.import_collector.has_import("typing", "Optional")

        # Postcondition 1.b.v (Union without None)
        ff5 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        assert ff5.finalize("Union[int, float]", nullable_schema, True) == "Optional[Union[int, float]]"
        assert ff5.context.import_collector.has_import("typing", "Optional")

    # Sub-Category 2.3: Optional because `required=False` AND `schema.is_nullable=True` (double reason)
    def test_finalize_optional_due_to_not_required_and_schema_nullable(
        self, nullable_schema: IRSchema, fresh_finalizer: TypeFinalizer
    ) -> None:
        """Contract: Optional due to both required=False and schema.is_nullable=True."""
        assert fresh_finalizer.finalize("str", nullable_schema, False) == "Optional[str]"
        assert fresh_finalizer.context.import_collector.has_import("typing", "Optional")

    # Test original problematic cases explicitly, mapping them to the contract
    def test_finalize_original_cases_mapped_to_contract(
        self, nullable_schema: IRSchema, non_nullable_schema: IRSchema
    ) -> None:
        """Original test cases mapped to new contract understanding."""

        # Case 1: Simple type with nullable schema (required=True)
        # Contract: Optional due to schema.is_nullable=True (Sub-Category 2.2)
        # Expect: "Optional[str]", import Optional
        ff_c1 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c1.finalize("str", nullable_schema, True)
        assert result == "Optional[str]"
        assert ff_c1.context.import_collector.has_import("typing", "Optional")

        # Case 2: Simple type with non-nullable schema but not required (required=False)
        # Contract: Optional due to required=False (Sub-Category 2.1)
        # Expect: "Optional[str]", import Optional
        ff_c2 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c2.finalize("str", non_nullable_schema, False)
        assert result == "Optional[str]"
        assert ff_c2.context.import_collector.has_import("typing", "Optional")

        # Case 3: Already Optional type doesn't get double-wrapped (schema nullable, required=True)
        # Contract: Optional by usage, but py_type already "Optional[...]" (Postcondition 1.b.iii)
        # Expect: "Optional[str]", DO NOT import Optional again for this specific call path
        ff_c3 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c3.finalize("Optional[str]", nullable_schema, True)
        assert result == "Optional[str]"
        assert not ff_c3.context.import_collector.has_import("typing", "Optional"), (
            "Optional import was added when py_type was already Optional[]"
        )

        # Case 4: Union type, non-nullable schema, not required (required=False)
        # Contract: Optional due to required=False. py_type is "Union[str, int]" (Postcondition 1.b.v)
        # Expect: "Optional[Union[str, int]]", import Optional
        ff_c4 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c4.finalize("Union[str, int]", non_nullable_schema, False)
        assert result == "Optional[Union[str, int]]"
        assert ff_c4.context.import_collector.has_import("typing", "Optional")

        # Case 5: Any type, nullable schema (required=True)
        # Contract: Optional due to schema.is_nullable=True. py_type is "Any" (Postcondition 1.b.ii)
        # Expect: "Optional[Any]", import Optional
        ff_c5 = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_c5.finalize("Any", nullable_schema, True)
        assert result == "Optional[Any]"
        assert ff_c5.context.import_collector.has_import("typing", "Optional")

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
        assert result == "Optional[Union[str, int]]"
        assert ff_c7.context.import_collector.has_import("typing", "Optional")

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
        assert result == "Optional[str]"

        # Test when required=False
        # Need another fresh finalizer for isolated import check if we were to check imports here
        another_fresh_finalizer = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = another_fresh_finalizer.finalize("str", string_or_null_schema, False)
        assert result == "Optional[str]"

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
        assert result == "Optional[str]"

        # Test complex list type that should be wrapped with Optional
        nullable_schema_list = IRSchema(
            name="NullableList", type="array", items=IRSchema(type="object"), is_nullable=True
        )
        ff_list = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_list.finalize("List[Dict[str, Any]]", nullable_schema_list, True)
        assert result == "Optional[List[Dict[str, Any]]]", "Failed to properly handle nullable array"

        # Test multiple-type Union that should be wrapped with Optional
        nullable_union_schema = IRSchema(
            name="NullableUnion", any_of=[], is_nullable=True
        )  # any_of details not important here
        ff_union = TypeFinalizer(
            RenderContext(
                overall_project_root="/tmp", package_root_for_generated_code="/tmp/pkg", core_package_name="core"
            )
        )
        result = ff_union.finalize("Union[Dict[str, Any], List[str], int]", nullable_union_schema, True)
        assert result == "Optional[Union[Dict[str, Any], List[str], int]]", "Failed to handle nullable union"

    def test_get_python_type_for_schema__schema_is_none__returns_any(self, context: RenderContext) -> None:
        """
        Scenario:
            - Call TypeHelper.get_python_type_for_schema with schema=None.
        Expected Outcome:
            - Returns "Any".
            - Adds "typing.Any" to imports.
        """
        # Arrange
        schemas: Dict[str, IRSchema] = {}
        # Act
        result = TypeHelper.get_python_type_for_schema(None, schemas, context)  # type: ignore
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
        schema_format: Optional[str],
        expected_py_type: Optional[str],
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
            assert primitive_resolver.context.import_collector.has_import(module, name), (
                f"Expected import {module}.{name} not found for {schema_type}/{schema_format}"
            )
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
    def schemas_fixture(self) -> Dict[str, IRSchema]:  # Renamed to avoid conflict with schemas param
        return {
            "MyModel": IRSchema(name="MyModel", type="object", properties={"id": IRSchema(type="integer")}),
            "MyEnum": IRSchema(name="MyEnum", type="string", enum=["A", "B"]),
        }

    @pytest.fixture
    def array_resolver(self, context: RenderContext, schemas_fixture: Dict[str, IRSchema]) -> ArrayTypeResolver:
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
                "List[TestArrayItem]",
                ["List"],
            ),
            ({"type": "object"}, "List[Dict[str, Any]]", ["List", "Dict", "Any"]),
            ({"type": "array", "items": {"type": "string"}}, "List[List[str]]", ["List"]),
            ({}, "List[Any]", ["List", "Any"]),
            ({"items": None}, "List[Any]", ["List", "Any"]),
        ],
    )
    def test_resolve_array_type(  # Renamed method for clarity
        self,
        items_schema_dict: Dict[str, Any],
        expected_py_type: str,
        expected_typing_imports: List[str],
        # context: RenderContext, # No longer directly used here, resolver has its own
        schemas_fixture: Dict[str, IRSchema],  # Use renamed fixture
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
            ) or array_resolver.context.import_collector.has_import("datetime", name), (
                f"Expected typing/datetime import '{name}' not found for items: {items_schema_dict}"
            )


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
    def schemas(self) -> Dict[str, IRSchema]:
        return {
            "SchemaA": IRSchema(name="SchemaA", type="object", properties={"a": IRSchema(type="string")}),
            "SchemaB": IRSchema(name="SchemaB", type="object", properties={"b": IRSchema(type="integer")}),
            "SchemaC": IRSchema(name="SchemaC", type="string", format="date"),
            "DataWrapper": IRSchema(
                name="DataWrapper",
                type="object",
                properties={"data": IRSchema(name="SchemaA_ref", type="SchemaA")},
                is_data_wrapper=True,
            ),
            "SimpleObject": IRSchema(name="SimpleObject", type="object"),
        }

    @pytest.fixture
    def composition_resolver(self, context: RenderContext, schemas: Dict[str, IRSchema]) -> CompositionTypeResolver:
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
                "Optional[str]",
                ["Union"],
            ),  # Handled by final Optional wrapping, Union[str, None] is intermediate
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
            #    TypeFinalizer._get_composition_type might not do unwrapping itself, but get_python_type_for_schema might.
            #    For now, let's assume _get_composition_type returns the type of the single element for allOf=[Schema].
            ("all_of", [{"$ref": "#/components/schemas/DataWrapper"}], "DataWrapper", []),
            # 3. allOf with multiple distinct object types - this is complex. TypeFinalizer might return the first, or Any, or a specific name if one is dominant.
            #    The current TypeFinalizer._get_composition_type for allOf returns the type of the *first* schema in the list.
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
                "Dict[str, Any]",
                ["Dict", "Any"],
            ),  # First is anonymous object
            ("all_of", [], "Any", ["Any"]),  # Empty allOf
        ],
    )
    def test_get_composition_type(
        self,
        composition_type: str,
        sub_schemas_dicts: List[Dict[str, Any]],
        expected_py_type: str,
        expected_typing_imports: List[str],
        context: RenderContext,
        schemas: Dict[str, IRSchema],
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
            parent_schema_dict["type"] = None  # Type should be None if a composition keyword is present

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
            ) or composition_resolver.context.import_collector.has_import("datetime", name), (
                f"Expected typing/datetime import '{name}' not found for {composition_type} with items: {sub_schemas_dicts}"
            )


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
    def base_schemas(self) -> Dict[str, IRSchema]:
        return {
            "ComplexModel": IRSchema(name="ComplexModel", type="object", properties={"id": IRSchema(type="integer")}),
            "SimpleEnum": IRSchema(name="SimpleEnum", type="string", enum=["A", "B"]),
            "MyStringAlias": IRSchema(name="MyStringAlias", type="string"),
            "MyIntAlias": IRSchema(name="MyIntAlias", type="integer"),
            "MyNumberAlias": IRSchema(name="MyNumberAlias", type="number"),
            "MyBooleanAlias": IRSchema(name="MyBooleanAlias", type="boolean"),
            "MyArrayAlias": IRSchema(name="MyArrayAlias", type="array", items=IRSchema(type="string")),
            "MyObjectAlias": IRSchema(name="MyObjectAlias", type="object"),
            "MyUnknownAlias": IRSchema(name="MyUnknownAlias", type="some_custom_unknown_type"),
        }

    @pytest.fixture
    def named_resolver(self, context: RenderContext, base_schemas: Dict[str, IRSchema]) -> NamedTypeResolver:
        return NamedTypeResolver(context, base_schemas)

    @pytest.mark.parametrize(
        "test_id, input_schema_dict, expected_return_type, expected_model_imports",
        [
            # 1. Named Complex Model (not an alias-like structure)
            (
                "named_complex_model",
                {"name": "ComplexModel", "type": "object"},  # input schema is a reference by name
                "ComplexModel",
                [("models.complex_model", "ComplexModel")],
            ),
            # 2. Named Simple Enum (not an alias-like structure)
            (
                "named_simple_enum",
                {"name": "SimpleEnum", "type": "string"},  # input schema is a reference by name
                "SimpleEnum",
                [("models.simple_enum", "SimpleEnum")],
            ),
            # 3. Structurally Alias-like to known primitive (string)
            (
                "alias_to_primitive_string",
                {"name": "MyStringAlias", "type": "string"},  # input schema is a reference by name
                None,  # Should defer to structural resolution
                [],
            ),
            # 4. Structurally Alias-like to known primitive (integer)
            ("alias_to_primitive_integer", {"name": "MyIntAlias", "type": "integer"}, None, []),
            # 5. Structurally Alias-like to known primitive (number)
            ("alias_to_primitive_number", {"name": "MyNumberAlias", "type": "number"}, None, []),
            # 6. Structurally Alias-like to known primitive (boolean)
            ("alias_to_primitive_boolean", {"name": "MyBooleanAlias", "type": "boolean"}, None, []),
            # 7. Structurally Alias-like to array
            (
                "alias_to_array",
                {"name": "MyArrayAlias", "type": "array"},
                None,  # Should defer
                [],
            ),
            # 8. Structurally Alias-like to object (no props) - treated as class reference
            (
                "alias_to_object_no_props",
                {"name": "MyObjectAlias", "type": "object"},
                "MyObjectAlias",
                [("models.my_object_alias", "MyObjectAlias")],
            ),
            # 9. Structurally Alias-like to UNKNOWN base type
            (
                "alias_to_unknown_type",
                {"name": "MyUnknownAlias", "type": "some_custom_unknown_type"},
                None,  # Should defer, leading to Any
                [],
            ),
            # 10. Named Inline Enum (schema has name and enum, but not in global `schemas` dict)
            # This scenario implies the input `schema` to _get_named_or_enum_type IS the definition.
            (
                "named_inline_enum_string",
                {"name": "StatusEnum", "type": "string", "enum": ["active", "inactive"]},
                "StatusEnum",
                [("models.status_enum", "StatusEnum")],
            ),
            (
                "named_inline_enum_integer",
                {"name": "NumericStatusEnum", "type": "integer", "enum": [1, 2, 3]},
                "NumericStatusEnum",
                [("models.numeric_status_enum", "NumericStatusEnum")],
            ),
            # 11. Unnamed Enum (string, type not specified -> defaults to string)
            ("unnamed_enum_default_string", {"enum": ["X", "Y"]}, "str", []),
            # 12. Unnamed Enum (string, type explicitly string)
            ("unnamed_enum_explicit_string", {"type": "string", "enum": ["X", "Y"]}, "str", []),
            # 13. Unnamed Enum (integer)
            ("unnamed_enum_integer", {"type": "integer", "enum": [10, 20]}, "int", []),
            # 14. Schema name not in global schemas, not an inline enum (e.g. an unresolved ref or direct use of a new named type)
            (
                "named_schema_not_in_globals_not_enum",
                {"name": "NotInGlobals", "type": "object"},
                None,  # Expects to return None as it cannot resolve it from `schemas` and it's not an enum
                [],
            ),
            # 15. Input schema itself has no name (anonymous)
            (
                "anonymous_schema_no_enum",
                {"type": "object", "properties": {"field": {"type": "string"}}},
                None,  # No name, no enum -> returns None
                [],
            ),
        ],
    )
    def test_get_named_or_enum_type(
        self,
        test_id: str,
        input_schema_dict: Dict[str, Any],
        expected_return_type: Optional[str],
        expected_model_imports: List[tuple[str, str]],
        context: RenderContext,
        base_schemas: Dict[str, IRSchema],
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
            - Returns the correct Python type string (e.g., a class name for a model/enum, None for aliases to be resolved structurally, base types for unnamed enums).
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
                assert fresh_context_for_test.import_collector.has_import(module, name), (
                    f"[{test_id}] Expected model import {module}.{name} not found."
                )
        else:
            allow_model_imports = False
            if expected_return_type:
                if any(char.isupper() for char in re.sub(r"[^a-zA-Z_0-9]", "", expected_return_type)):
                    allow_model_imports = True

            if not allow_model_imports:
                if hasattr(fresh_context_for_test.import_collector, "imports"):
                    for imp_module in fresh_context_for_test.import_collector.imports.keys():
                        assert not imp_module.startswith("models."), (
                            f"[{test_id}] Unexpected model import found: {imp_module} when none expected (expected_return_type: {expected_return_type})."
                        )


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
    def schemas(self) -> Dict[str, IRSchema]:
        return {
            "ReferencedModel": IRSchema(
                name="ReferencedModel", type="object", properties={"id": IRSchema(type="integer")}
            ),
            "StringType": IRSchema(name="StringType", type="string"),
        }

    @pytest.fixture
    def object_resolver(self, context: RenderContext, schemas: Dict[str, IRSchema]) -> ObjectTypeResolver:
        main_resolver = SchemaTypeResolver(context, schemas)
        return ObjectTypeResolver(context, schemas, main_resolver)

    @pytest.mark.parametrize(
        "test_id, input_schema_dict, expected_return_type, expected_typing_imports",
        [
            # 1. additionalProperties: true
            (
                "additional_props_true",
                {"type": "object", "additional_properties": True},
                "Dict[str, Any]",
                ["Dict", "Any"],
            ),
            # 2. additionalProperties: {schema} (referencing a primitive type)
            (
                "additional_props_schema_primitive",
                {"type": "object", "additional_properties": {"type": "string"}},
                "Dict[str, str]",
                [
                    "Dict"  # str is built-in, Any might be imported by sub-call if sub-schema was complex
                ],
            ),
            # 3. additionalProperties: {schema} (referencing a named model)
            (
                "additional_props_schema_ref_model",
                {"type": "object", "additional_properties": {"$ref": "#/components/schemas/ReferencedModel"}},
                "Dict[str, ReferencedModel]",
                [
                    "Dict"  # ReferencedModel import handled by recursive call
                ],
            ),
            # 4. Anonymous object, no properties, no explicit additionalProperties (should default to Dict[str, Any])
            ("anon_obj_no_props_no_add_props", {"type": "object"}, "Dict[str, Any]", ["Dict", "Any"]),
            # 5. Anonymous object WITH properties (should warn and become Dict[str, Any]) - COVERAGE (lines 254-260)
            (
                "anon_obj_with_props",
                {"type": "object", "properties": {"key": {"type": "string"}}},
                "Dict[str, Any]",
                ["Dict", "Any"],
            ),
            # 6. Named object, no properties, additionalProperties: false (should return its own name) - COVERAGE (line 267-272)
            (
                "named_obj_no_props_add_props_false",
                {"name": "MyNamedObject", "type": "object", "additional_properties": False},
                "MyNamedObject",  # Sanitized name
                [],  # Import handled by ModelVisitor if it becomes a top-level model
            ),
            # 7. Named object, no properties, additionalProperties: {} (empty schema, restrictive) - COVERAGE (line 267-272)
            (
                "named_obj_no_props_add_props_empty_schema",
                {
                    "name": "MyNamedEmptyPropsObject",
                    "type": "object",
                    "additional_properties": {},
                },  # Empty schema means no extra props
                "MyNamedEmptyPropsObject",
                [],
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
        input_schema_dict: Dict[str, Any],
        expected_return_type: Optional[str],
        expected_typing_imports: List[str],
        context: RenderContext,
        schemas: Dict[str, IRSchema],
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
            - Returns the correct Python type string (e.g., Dict[str, Any], model name, Any, or None).
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

        for imp_name in expected_typing_imports:
            assert object_resolver.context.import_collector.has_import("typing", imp_name), (
                f"[{test_id}] Expected typing import '{imp_name}' not found."
            )

        allow_model_imports = False
        if expected_return_type:
            if any(char.isupper() for char in re.sub(r"[^a-zA-Z_0-9]", "", expected_return_type)):
                allow_model_imports = True

        if not allow_model_imports:
            if hasattr(object_resolver.context.import_collector, "imports"):
                for imp_module in object_resolver.context.import_collector.imports.keys():
                    assert not imp_module.startswith("models."), (
                        f"[{test_id}] Unexpected model import found: {imp_module} when none expected (expected_return_type: {expected_return_type})."
                    )


class TestTypeHelperGetPythonTypeForSchemaFallthroughs:
    @pytest.fixture
    def context(self) -> RenderContext:
        return RenderContext(
            overall_project_root="/tmp",
            package_root_for_generated_code="/tmp/pkg",
            core_package_name="core",
        )

    @pytest.fixture
    def empty_schemas(self) -> Dict[str, IRSchema]:
        return {}

    def test_get_python_type_for_schema__fallthrough_to_primitive(
        self, context: RenderContext, empty_schemas: Dict[str, IRSchema]
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
        self, context: RenderContext, empty_schemas: Dict[str, IRSchema]
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
        self, context: RenderContext, empty_schemas: Dict[str, IRSchema]
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
        self, context: RenderContext, empty_schemas: Dict[str, IRSchema]
    ) -> None:
        """
        Scenario:
            - schema is anonymous, not an enum, resolve_alias_target=False.
            - Schema is structurally an object type with additionalProperties:true.
        Expected Outcome:
            - Correctly resolves to Dict[str, Any].
        """
        schema = IRSchema(name=None, type="object", additional_properties=True)
        result = TypeHelper.get_python_type_for_schema(
            schema, empty_schemas, context, required=True, resolve_alias_target=False
        )
        assert result == "Dict[str, Any]"
        assert context.import_collector.has_import("typing", "Dict")
        assert context.import_collector.has_import("typing", "Any")

    def test_get_python_type_for_schema__fallthrough_to_unknown_any(
        self, context: RenderContext, empty_schemas: Dict[str, IRSchema]
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
