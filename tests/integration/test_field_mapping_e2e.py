"""Integration test for field name mapping in generated clients.

Tests that the DataclassSerializer correctly maps Python snake_case field names
to API camelCase field names when serializing request bodies.
"""

import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import generate_client


def test_field_mapping__business_swagger_updateDocument__serializes_to_camelCase() -> None:
    """End-to-end test for field mapping with business_swagger.json.

    Scenario:
        - Generate client from business_swagger.json
        - Import DocumentUpdate model from generated client
        - Create instance with snake_case attributes
        - Serialize using DataclassSerializer
        - Verify output uses camelCase API field names

    Expected Outcome:
        - Generated code should include field mappings in Meta class
        - DataclassSerializer should use camelCase keys (not snake_case)
        - Validates the fix for the field mapping bug
    """
    # Arrange - Generate client in temporary directory
    spec_path = "input/business_swagger.json"
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Act - Generate client
        generate_client(
            spec_path=spec_path,
            project_root=str(project_root),
            output_package="businessapi",
            force=True,
            no_postprocess=True,  # Skip formatting for speed
        )

        # Import generated model dynamically
        import sys

        sys.path.insert(0, str(project_root))
        from businessapi.core.utils import DataclassSerializer
        from businessapi.models.document_update import DocumentUpdate

        # Create instance with snake_case attributes
        doc_update = DocumentUpdate(
            url="https://example.com/doc",
            data_source_id="source-123",
            mime_type="text/html",
            last_modified="2024-10-23T12:00:00Z",
        )

        # Act - Serialize using DataclassSerializer
        result = DataclassSerializer.serialize(doc_update)

        # Assert - Should use camelCase API field names
        assert isinstance(result, dict)

        # Check that camelCase keys are present
        assert "dataSourceId" in result, "Should use camelCase 'dataSourceId' (API field name)"
        assert "mimeType" in result, "Should use camelCase 'mimeType' (API field name)"
        assert "lastModified" in result, "Should use camelCase 'lastModified' (API field name)"

        # Check that snake_case keys are NOT present
        assert "data_source_id" not in result, "Should NOT use snake_case 'data_source_id' (Python field name)"
        assert "mime_type" not in result, "Should NOT use snake_case 'mime_type' (Python field name)"
        assert "last_modified" not in result, "Should NOT use snake_case 'last_modified' (Python field name)"

        # Verify values are correct
        assert result["dataSourceId"] == "source-123"
        assert result["mimeType"] == "text/html"
        assert result["lastModified"] == "2024-10-23T12:00:00Z"

        # Cleanup
        sys.path.remove(str(project_root))


def test_field_mapping__roundtrip__preserves_data() -> None:
    """Test that field mapping works correctly in both directions.

    Scenario:
        - Generate client from business_swagger.json
        - Create DocumentUpdate from dict with camelCase keys (API response)
        - Serialize back to dict
        - Verify field names are preserved

    Expected Outcome:
        - from_dict should accept camelCase and map to snake_case attributes
        - DataclassSerializer should map snake_case attributes back to camelCase
        - Data should be preserved through the roundtrip
    """
    # Arrange - Generate client in temporary directory
    spec_path = "input/business_swagger.json"
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Generate client
        generate_client(
            spec_path=spec_path,
            project_root=str(project_root),
            output_package="businessapi",
            force=True,
            no_postprocess=True,  # Skip formatting for speed
        )

        # Import generated model dynamically
        import sys

        sys.path.insert(0, str(project_root))
        from businessapi.core.utils import DataclassSerializer
        from businessapi.models.document_update import DocumentUpdate

        # Act - Create from API response (camelCase)
        api_response = {
            "url": "https://example.com/doc",
            "dataSourceId": "source-456",
            "mimeType": "application/json",
            "lastModified": "2024-10-23T15:30:00Z",
        }
        doc_update = DocumentUpdate.from_dict(api_response)

        # Verify attributes are accessible via snake_case
        assert doc_update.data_source_id == "source-456"
        assert doc_update.mime_type == "application/json"
        assert doc_update.last_modified == "2024-10-23T15:30:00Z"

        # Act - Serialize back (should produce camelCase)
        result = DataclassSerializer.serialize(doc_update)

        # Assert - Should match original API response format
        assert result["dataSourceId"] == "source-456"
        assert result["mimeType"] == "application/json"
        assert result["lastModified"] == "2024-10-23T15:30:00Z"

        # Cleanup
        sys.path.remove(str(project_root))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
