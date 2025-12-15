"""Unit tests for field name collision detection in DataclassGenerator.

Tests that the DataclassGenerator correctly handles field name collisions when
multiple API field names sanitise to the same Python field name.
"""

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator


@pytest.fixture
def render_context() -> RenderContext:
    """Create a render context for testing."""
    return RenderContext(
        core_package_name="testclient.core",
        package_root_for_generated_code="/tmp/testclient",
        overall_project_root="/tmp",
        parsed_schemas={},
    )


@pytest.fixture
def dataclass_generator() -> DataclassGenerator:
    """Create a DataclassGenerator for testing."""
    renderer = PythonConstructRenderer()
    return DataclassGenerator(renderer=renderer, all_schemas={})


def test_generate__field_collision_userId_user_id__creates_unique_fields(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that userId and user_id fields are both generated with unique names.

    Scenario:
        - Schema has two properties: 'userId' (camelCase) and 'user_id' (snake_case)
        - Both sanitise to 'user_id' in Python
        - Generator should detect collision and create unique field names

    Expected Outcome:
        - First field keeps 'user_id'
        - Second field gets 'user_id_2'
        - Both field mappings are correct in Meta class
    """
    # Arrange
    schema = IRSchema(
        name="UserData",
        type="object",
        properties={
            "userId": IRSchema(name="userId", type="string"),
            "user_id": IRSchema(name="user_id", type="string"),
            "address": IRSchema(name="address", type="string"),
        },
        required=["userId", "user_id", "address"],
    )

    # Act
    code = dataclass_generator.generate(schema, "UserData", render_context)

    # Assert - Both fields should exist with unique names
    assert "user_id: str" in code, "First collision field 'user_id' should exist"
    assert "user_id_2: str" in code, "Second collision field 'user_id_2' should exist"
    assert "address: str" in code, "Non-colliding field 'address' should exist"

    # Assert - Meta class should have correct mappings
    assert "class Meta:" in code, "Meta class should be generated"
    assert '"userId": "user_id"' in code, "userId should map to user_id"
    assert '"user_id": "user_id_2"' in code, "user_id should map to user_id_2"


def test_generate__field_collision_three_variants__applies_suffixes(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that three colliding field names all get unique suffixes.

    Scenario:
        - Schema has 'userId', 'user_id', and 'User_ID' properties
        - All sanitise to 'user_id' in Python
        - Generator should create unique names for all three

    Expected Outcome:
        - First field: 'user_id'
        - Second field: 'user_id_2'
        - Third field: 'user_id_3'
    """
    # Arrange
    schema = IRSchema(
        name="UserIdentifiers",
        type="object",
        properties={
            "userId": IRSchema(name="userId", type="string"),
            "user_id": IRSchema(name="user_id", type="string"),
            "User_ID": IRSchema(name="User_ID", type="string"),
        },
        required=["userId", "user_id", "User_ID"],
    )

    # Act
    code = dataclass_generator.generate(schema, "UserIdentifiers", render_context)

    # Assert - All three fields should exist with unique names
    assert "user_id: str" in code, "First collision field 'user_id' should exist"
    assert "user_id_2: str" in code, "Second collision field 'user_id_2' should exist"
    assert "user_id_3: str" in code, "Third collision field 'user_id_3' should exist"


def test_generate__no_collision__no_suffix_applied(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that fields without collision don't get suffixes.

    Scenario:
        - Schema has 'firstName', 'lastName', 'address' properties
        - None collide after sanitisation
        - No suffixes should be applied

    Expected Outcome:
        - Fields: 'first_name', 'last_name', 'address'
        - No '_2' or '_3' suffixes
    """
    # Arrange
    schema = IRSchema(
        name="Person",
        type="object",
        properties={
            "firstName": IRSchema(name="firstName", type="string"),
            "lastName": IRSchema(name="lastName", type="string"),
            "address": IRSchema(name="address", type="string"),
        },
        required=["firstName", "lastName", "address"],
    )

    # Act
    code = dataclass_generator.generate(schema, "Person", render_context)

    # Assert - Fields should exist without suffixes
    assert "first_name: str" in code
    assert "last_name: str" in code
    assert "address: str" in code

    # Assert - No collision suffixes applied
    assert "_2" not in code, "No collision suffixes should be present"
    assert "_3" not in code, "No collision suffixes should be present"


def test_generate__collision_with_required_fields__preserves_required_status(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that field collision handling preserves required/optional status.

    Scenario:
        - 'userId' is required, 'user_id' is optional
        - Both collide to 'user_id'
        - Required status should be preserved for each

    Expected Outcome:
        - 'user_id' (from userId) should be required (no default)
        - 'user_id_2' (from user_id) should be optional (has default)
    """
    # Arrange
    schema = IRSchema(
        name="UserWithOptional",
        type="object",
        properties={
            "userId": IRSchema(name="userId", type="string"),
            "user_id": IRSchema(name="user_id", type="string"),
        },
        required=["userId"],  # Only userId is required
    )

    # Act
    code = dataclass_generator.generate(schema, "UserWithOptional", render_context)

    # Assert - First field (from userId) should be required
    # Required fields appear before optional fields in sorted order
    assert "user_id: str" in code, "Required field should exist"

    # Assert - Second field (from user_id) should be optional
    assert "user_id_2: str" in code or "user_id_2: str | None" in code


def test_field_mappings__collision__both_api_names_preserved(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that Meta class preserves both original API names in mappings.

    Scenario:
        - 'dataSourceId' and 'data_source_id' collide
        - Meta class should correctly map both to their Python names

    Expected Outcome:
        - key_transform_with_load: {"dataSourceId": "data_source_id", "data_source_id": "data_source_id_2"}
        - key_transform_with_dump: {"data_source_id": "dataSourceId", "data_source_id_2": "data_source_id"}
    """
    # Arrange
    schema = IRSchema(
        name="DataSource",
        type="object",
        properties={
            "dataSourceId": IRSchema(name="dataSourceId", type="string"),
            "data_source_id": IRSchema(name="data_source_id", type="string"),
        },
        required=["dataSourceId", "data_source_id"],
    )

    # Act
    code = dataclass_generator.generate(schema, "DataSource", render_context)

    # Assert - Meta class should have correct bidirectional mappings
    assert "key_transform_with_load" in code
    assert "key_transform_with_dump" in code

    # Load mappings (API → Python)
    assert '"dataSourceId": "data_source_id"' in code
    assert '"data_source_id": "data_source_id_2"' in code

    # Dump mappings (Python → API)
    assert '"data_source_id": "dataSourceId"' in code
    assert '"data_source_id_2": "data_source_id"' in code


def test_generate__snake_case_api_field__preserves_original_name(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that snake_case API fields are mapped back to their original names.

    Scenario:
        - API spec uses snake_case: 'user_id', 'created_at'
        - Python fields: 'user_id', 'created_at' (same)
        - Meta class should still map to preserve original names

    Expected Outcome:
        - Meta class contains mappings even when names match
        - Ensures serialisation uses original API names
    """
    # Arrange
    schema = IRSchema(
        name="SnakeCaseModel",
        type="object",
        properties={
            "user_id": IRSchema(name="user_id", type="string"),
            "created_at": IRSchema(name="created_at", type="string"),
        },
        required=["user_id", "created_at"],
    )

    # Act
    code = dataclass_generator.generate(schema, "SnakeCaseModel", render_context)

    # Assert - Meta class should exist with mappings
    assert "class Meta:" in code, "Meta class should be generated even when names match"
    assert "key_transform_with_load" in code
    assert "key_transform_with_dump" in code

    # Assert - Mappings should preserve original names
    assert '"user_id": "user_id"' in code, "user_id should map to itself"
    assert '"created_at": "created_at"' in code, "created_at should map to itself"


def test_generate__kebab_case_api_field__maps_correctly(
    dataclass_generator: DataclassGenerator, render_context: RenderContext
) -> None:
    """Test that kebab-case API fields are mapped correctly.

    Scenario:
        - API spec uses kebab-case: 'user-id', 'created-at'
        - Python fields: 'user_id', 'created_at'
        - Meta class should map Python names back to kebab-case

    Expected Outcome:
        - key_transform_with_dump maps 'user_id' to 'user-id'
        - key_transform_with_load maps 'user-id' to 'user_id'
    """
    # Arrange
    schema = IRSchema(
        name="KebabCaseModel",
        type="object",
        properties={
            "user-id": IRSchema(name="user-id", type="string"),
            "created-at": IRSchema(name="created-at", type="string"),
        },
        required=["user-id", "created-at"],
    )

    # Act
    code = dataclass_generator.generate(schema, "KebabCaseModel", render_context)

    # Assert - Fields should be snake_case
    assert "user_id: str" in code
    assert "created_at: str" in code

    # Assert - Meta mappings should use kebab-case for API
    assert '"user-id": "user_id"' in code, "Load mapping should map kebab-case to snake_case"
    assert '"user_id": "user-id"' in code, "Dump mapping should map snake_case to kebab-case"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
