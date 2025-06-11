"""Unit tests for IRSchema class."""

import pytest
from pyopenapi_gen import IRSchema


def test_irschema_init_arguments() -> None:
    """Test that IRSchema doesn't accept raw_schema_node as argument."""
    # Valid parameters should work
    schema = IRSchema(name="Test", type="object", description="Test schema", properties={}, required=[])
    assert schema.name == "Test"

    # This should raise TypeError because raw_schema_node is not a valid parameter
    with pytest.raises(TypeError) as exc_info:
        IRSchema(
            name="Test",
            type="object",
            raw_schema_node={"type": "object"},  # Invalid parameter
        )

    assert "got an unexpected keyword argument 'raw_schema_node'" in str(exc_info.value)
