"""Comprehensive integration tests for field name mapping.

Tests that the generator correctly handles field name mapping for:
- snake_case API fields (preserve original names)
- camelCase API fields (roundtrip works correctly)
- Field collisions (unique names generated)
- Mixed casing in same schema
"""

import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import generate_client


def _create_test_spec_snake_case() -> dict:
    """Create an OpenAPI spec with snake_case field names."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Snake Case API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "UserProfile": {
                    "type": "object",
                    "required": ["user_id", "created_at"],
                    "properties": {
                        "user_id": {"type": "string", "description": "The user identifier"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "display_name": {"type": "string"},
                        "email_address": {"type": "string"},
                    },
                }
            }
        },
    }


def _create_test_spec_field_collision() -> dict:
    """Create an OpenAPI spec with field name collisions."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Collision API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "CollisionModel": {
                    "type": "object",
                    "required": ["userId", "user_id", "address"],
                    "properties": {
                        "userId": {"type": "string", "description": "User ID in camelCase"},
                        "user_id": {"type": "string", "description": "User ID in snake_case"},
                        "address": {"type": "string"},
                    },
                }
            }
        },
    }


def _create_test_spec_mixed_casing() -> dict:
    """Create an OpenAPI spec with mixed field casing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Mixed Casing API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "MixedModel": {
                    "type": "object",
                    "required": ["firstName", "last_name", "emailAddress"],
                    "properties": {
                        "firstName": {"type": "string"},
                        "last_name": {"type": "string"},
                        "emailAddress": {"type": "string"},
                    },
                }
            }
        },
    }


def test_field_mapping__snake_case_api__roundtrip_preserves_original_names() -> None:
    """Test that snake_case API fields are preserved through roundtrip.

    Scenario:
        - OpenAPI spec uses snake_case field names (user_id, created_at)
        - Generate client and deserialise API response
        - Serialise back and verify original snake_case names are used

    Expected Outcome:
        - Python dataclass uses snake_case attributes (same as API)
        - Serialisation produces snake_case keys (original API format)
    """
    import json

    spec = _create_test_spec_snake_case()

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_path = project_root / "spec.json"
        spec_path.write_text(json.dumps(spec))

        generate_client(
            spec_path=str(spec_path),
            project_root=str(project_root),
            output_package="snakeapi",
            force=True,
            no_postprocess=True,
        )

        import sys

        sys.path.insert(0, str(project_root))

        from snakeapi.core.cattrs_converter import structure_from_dict
        from snakeapi.core.utils import DataclassSerializer
        from snakeapi.models.user_profile import UserProfile

        # Deserialise from API response (snake_case keys)
        api_response = {
            "user_id": "user-123",
            "created_at": "2024-01-15T10:30:00Z",
            "display_name": "John Doe",
            "email_address": "john@example.com",
        }

        user = structure_from_dict(api_response, UserProfile)

        # Verify Python attributes
        assert user.user_id == "user-123"
        # created_at is converted to datetime by cattrs
        from datetime import datetime, timezone

        assert user.created_at == datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        assert user.display_name == "John Doe"
        assert user.email_address == "john@example.com"

        # Serialise back
        result = DataclassSerializer.serialize(user)

        # Verify original snake_case keys are used (NOT camelCase!)
        assert "user_id" in result, "Should use snake_case 'user_id' (original API name)"
        assert "created_at" in result, "Should use snake_case 'created_at' (original API name)"
        assert "display_name" in result, "Should use snake_case 'display_name' (original API name)"
        assert "email_address" in result, "Should use snake_case 'email_address' (original API name)"

        # Verify NO camelCase keys
        assert "userId" not in result, "Should NOT convert to camelCase"
        assert "createdAt" not in result, "Should NOT convert to camelCase"
        assert "displayName" not in result, "Should NOT convert to camelCase"
        assert "emailAddress" not in result, "Should NOT convert to camelCase"

        # Verify values
        assert result["user_id"] == "user-123"
        # datetime is serialised to ISO string
        assert result["created_at"] == "2024-01-15T10:30:00+00:00"

        sys.path.remove(str(project_root))


def test_field_mapping__field_collision__generates_unique_fields() -> None:
    """Test that field collisions are handled with unique field names.

    Scenario:
        - OpenAPI spec has 'userId' (camelCase) and 'user_id' (snake_case)
        - Both sanitise to 'user_id' in Python
        - Generator should create unique field names

    Expected Outcome:
        - First field: 'user_id' (maps from 'userId')
        - Second field: 'user_id_2' (maps from 'user_id')
        - Both fields serialise back to their original API names
    """
    import json

    spec = _create_test_spec_field_collision()

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_path = project_root / "spec.json"
        spec_path.write_text(json.dumps(spec))

        generate_client(
            spec_path=str(spec_path),
            project_root=str(project_root),
            output_package="collisionapi",
            force=True,
            no_postprocess=True,
        )

        import sys

        sys.path.insert(0, str(project_root))

        # Read generated model to verify field names
        model_path = project_root / "collisionapi" / "models" / "collision_model.py"
        model_code = model_path.read_text()

        # Verify unique field names were generated
        assert "user_id:" in model_code, "First collision field 'user_id' should exist"
        assert "user_id_2:" in model_code, "Second collision field 'user_id_2' should exist"
        assert "address:" in model_code, "Non-colliding field 'address' should exist"

        # Verify Meta class has correct mappings
        assert "key_transform_with_load" in model_code
        assert "key_transform_with_dump" in model_code

        from collisionapi.core.cattrs_converter import structure_from_dict
        from collisionapi.core.utils import DataclassSerializer
        from collisionapi.models.collision_model import CollisionModel

        # Deserialise from API response
        api_response = {
            "userId": "camel-user-id",
            "user_id": "snake-user-id",
            "address": "123 Main St",
        }

        model = structure_from_dict(api_response, CollisionModel)

        # Verify both values are accessible
        assert model.user_id == "camel-user-id", "user_id should have value from 'userId'"
        assert model.user_id_2 == "snake-user-id", "user_id_2 should have value from 'user_id'"
        assert model.address == "123 Main St"

        # Serialise back
        result = DataclassSerializer.serialize(model)

        # Verify both original API names are used
        assert "userId" in result, "Should serialise to original 'userId'"
        assert "user_id" in result, "Should serialise to original 'user_id'"
        assert result["userId"] == "camel-user-id"
        assert result["user_id"] == "snake-user-id"

        sys.path.remove(str(project_root))


def test_field_mapping__mixed_casing__all_fields_mapped_correctly() -> None:
    """Test that mixed casing fields all map correctly.

    Scenario:
        - OpenAPI spec has: 'firstName' (camelCase), 'last_name' (snake_case), 'emailAddress' (camelCase)
        - All should be mapped correctly

    Expected Outcome:
        - All fields deserialise correctly
        - All fields serialise back to their original format
    """
    import json

    spec = _create_test_spec_mixed_casing()

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        spec_path = project_root / "spec.json"
        spec_path.write_text(json.dumps(spec))

        generate_client(
            spec_path=str(spec_path),
            project_root=str(project_root),
            output_package="mixedapi",
            force=True,
            no_postprocess=True,
        )

        import sys

        sys.path.insert(0, str(project_root))

        from mixedapi.core.cattrs_converter import structure_from_dict
        from mixedapi.core.utils import DataclassSerializer
        from mixedapi.models.mixed_model import MixedModel

        # Deserialise from API response (mixed casing)
        api_response = {
            "firstName": "John",
            "last_name": "Doe",
            "emailAddress": "john@example.com",
        }

        model = structure_from_dict(api_response, MixedModel)

        # Verify Python attributes (all snake_case)
        assert model.first_name == "John"
        assert model.last_name == "Doe"
        assert model.email_address == "john@example.com"

        # Serialise back
        result = DataclassSerializer.serialize(model)

        # Verify original casing is preserved
        assert "firstName" in result, "Should use original camelCase 'firstName'"
        assert "last_name" in result, "Should use original snake_case 'last_name'"
        assert "emailAddress" in result, "Should use original camelCase 'emailAddress'"

        # Verify values
        assert result["firstName"] == "John"
        assert result["last_name"] == "Doe"
        assert result["emailAddress"] == "john@example.com"

        sys.path.remove(str(project_root))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
