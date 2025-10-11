"""
Regression test for missing imports bug when schema names are substrings of each other.

Bug: When generating imports for schemas, the self-import check used .endswith() which
incorrectly matched when one filename was a suffix of another.

Example: "vector_index_with_embedding_response_data.py".endswith("embedding_response_data.py") == True

This caused EmbeddingResponseData to be treated as a self-import when being resolved
from VectorIndexWithEmbeddingResponseData, resulting in a forward reference without an import.
"""

from unittest.mock import Mock

from pyopenapi_gen import IRSchema
from pyopenapi_gen.types.resolvers.reference_resolver import OpenAPIReferenceResolver
from pyopenapi_gen.types.resolvers.schema_resolver import OpenAPISchemaResolver
from pyopenapi_gen.types.services.type_service import RenderContextAdapter


def test_schema_resolver__similar_module_names__generates_import_correctly():
    """
    Scenario: Two schemas where one module name is a suffix of the other
    - VectorIndexWithEmbeddingResponseData in vector_index_with_embedding_response_data.py
    - EmbeddingResponseData in embedding_response_data.py

    Expected Outcome: When resolving EmbeddingResponseData from VectorIndexWithEmbeddingResponseData,
    it should NOT be treated as a self-import and SHOULD generate an import statement.
    """
    # Arrange
    embedding_schema = IRSchema(
        name="EmbeddingResponseData",
        type="object",
        generation_name="EmbeddingResponseData",
        final_module_stem="embedding_response_data",
        properties={"id": IRSchema(type="string")},
    )

    vector_schema = IRSchema(
        name="VectorIndexWithEmbeddingResponseData",
        type="object",
        generation_name="VectorIndexWithEmbeddingResponseData",
        final_module_stem="vector_index_with_embedding_response_data",
        properties={
            "id": IRSchema(type="string"),
            "embedding": embedding_schema,  # Reference to EmbeddingResponseData
        },
    )

    schemas = {
        "EmbeddingResponseData": embedding_schema,
        "VectorIndexWithEmbeddingResponseData": vector_schema,
    }

    ref_resolver = OpenAPIReferenceResolver(schemas)
    schema_resolver = OpenAPISchemaResolver(ref_resolver)

    # Create mock context that simulates being in vector_index_with_embedding_response_data.py
    mock_render_context = Mock()
    mock_render_context.current_file = "/path/to/models/vector_index_with_embedding_response_data.py"

    # Track import calls
    import_calls = []

    def track_import(module, name):
        import_calls.append((module, name))

    mock_render_context.add_import = track_import
    mock_render_context.calculate_relative_path_for_internal_module = Mock(return_value=".embedding_response_data")

    context = RenderContextAdapter(mock_render_context)

    # Act
    result = schema_resolver.resolve_schema(embedding_schema, context, required=False)

    # Assert
    assert result.python_type == "EmbeddingResponseData"
    assert result.is_forward_ref is False, "Should NOT be a forward reference"
    assert result.needs_import is True, "Should need an import"
    assert result.import_module is not None, "Should have import module"
    assert result.import_name == "EmbeddingResponseData"

    # Verify import was added
    assert len(import_calls) == 1, f"Expected 1 import call, got {len(import_calls)}"
    import_module, import_name = import_calls[0]
    assert (
        "embedding_response_data" in import_module
    ), f"Import module '{import_module}' should contain the correct module stem"
    assert import_name == "EmbeddingResponseData", f"Import name should be EmbeddingResponseData, got {import_name}"


def test_schema_resolver__actual_self_import__marks_as_forward_reference():
    """
    Scenario: Schema referencing itself (actual self-import)

    Expected Outcome: Should be marked as forward reference WITHOUT import.
    """
    # Arrange
    self_ref_schema = IRSchema(
        name="RecursiveSchema",
        type="object",
        generation_name="RecursiveSchema",
        final_module_stem="recursive_schema",
        properties={
            "name": IRSchema(type="string"),
            "child": None,  # Will be set to self
        },
    )
    # Create circular reference
    self_ref_schema.properties["child"] = self_ref_schema

    schemas = {"RecursiveSchema": self_ref_schema}

    ref_resolver = OpenAPIReferenceResolver(schemas)
    schema_resolver = OpenAPISchemaResolver(ref_resolver)

    # Create mock context simulating being in recursive_schema.py
    mock_render_context = Mock()
    mock_render_context.current_file = "/path/to/models/recursive_schema.py"

    # Track import calls
    import_calls_self = []

    def track_import_self(module, name):
        import_calls_self.append((module, name))

    mock_render_context.add_import = track_import_self

    context = RenderContextAdapter(mock_render_context)

    # Act
    result = schema_resolver.resolve_schema(self_ref_schema, context, required=False)

    # Assert
    assert result.python_type == "RecursiveSchema"
    assert result.is_forward_ref is True, "SHOULD be a forward reference for self-import"
    assert result.needs_import is False, "Should NOT need import for self-reference"
    assert result.import_module is None, "Should NOT have import module for self-reference"

    # Verify NO import was added
    assert len(import_calls_self) == 0, f"Expected 0 import calls, got {len(import_calls_self)}"


def test_schema_resolver__exact_filename_match__only_self_import():
    """
    Scenario: Verify that only EXACT filename matches are treated as self-imports

    Expected Outcome:
    - "user.py" resolving User -> self-import (forward ref, no import)
    - "super_user.py" resolving User -> NOT self-import (no forward ref, WITH import)
    """
    # Arrange
    user_schema = IRSchema(
        name="User",
        type="object",
        generation_name="User",
        final_module_stem="user",
        properties={"name": IRSchema(type="string")},
    )

    schemas = {"User": user_schema}
    ref_resolver = OpenAPIReferenceResolver(schemas)
    schema_resolver = OpenAPISchemaResolver(ref_resolver)

    # Test 1: From user.py (EXACT match - should be self-import)
    mock_context_self = Mock()
    mock_context_self.current_file = "/path/to/models/user.py"

    import_calls_exact = []

    def track_import_exact(module, name):
        import_calls_exact.append((module, name))

    mock_context_self.add_import = track_import_exact

    context_self = RenderContextAdapter(mock_context_self)

    result_self = schema_resolver.resolve_schema(user_schema, context_self, required=True)

    assert result_self.is_forward_ref is True, "user.py resolving User should be forward ref"
    assert result_self.needs_import is False, "user.py resolving User should NOT need import"
    assert len(import_calls_exact) == 0, f"Expected 0 import calls for self-import, got {len(import_calls_exact)}"

    # Test 2: From super_user.py (suffix match but NOT exact - should NOT be self-import)
    mock_context_other = Mock()
    mock_context_other.current_file = "/path/to/models/super_user.py"
    mock_context_other.calculate_relative_path_for_internal_module = Mock(return_value=".user")

    import_calls_other = []

    def track_import_other(module, name):
        import_calls_other.append((module, name))

    mock_context_other.add_import = track_import_other

    context_other = RenderContextAdapter(mock_context_other)

    result_other = schema_resolver.resolve_schema(user_schema, context_other, required=True)

    assert result_other.is_forward_ref is False, "super_user.py resolving User should NOT be forward ref"
    assert result_other.needs_import is True, "super_user.py resolving User SHOULD need import"
    assert len(import_calls_other) == 1, f"Expected 1 import call, got {len(import_calls_other)}"
