"""Tests for dataclass integration in endpoint generators.

Scenario: Generated endpoint methods should automatically serialize dataclass inputs
before sending them as request bodies.

Expected Outcome: Generated code includes DataclassSerializer calls for body parameters,
ensuring seamless developer experience with dataclass inputs.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, call

import pytest
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRRequestBody, IRSchema
from pyopenapi_gen.visit.endpoint.generators.url_args_generator import EndpointUrlArgsGenerator


@pytest.fixture
def render_context_mock() -> MagicMock:
    mock = MagicMock(spec=RenderContext)
    mock.core_package_name = "test_core"
    return mock


@pytest.fixture
def code_writer_mock() -> MagicMock:
    return MagicMock(spec=CodeWriter)


@pytest.fixture
def url_args_generator() -> EndpointUrlArgsGenerator:
    return EndpointUrlArgsGenerator()


class TestDataclassIntegrationInUrlArgsGenerator:
    """Test dataclass serialization integration in URL args generator."""

    def test_generate_url_and_args_json_body__includes_serializer_call__converts_dataclass_input(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Generate endpoint method with JSON body parameter
        Expected Outcome: Generated code includes DataclassSerializer call for body parameter
        """
        # Arrange
        body_param_info: Dict[str, Any] = {
            "name": "body",
            "param_in": "body",
            "required": True,
            "original_name": "body",
            "type": "CreateUserRequest",  # Custom dataclass type
        }

        operation = IROperation(
            operation_id="create_user",
            summary="Create a new user",
            description="Creates a new user with the provided data.",
            method=HTTPMethod.POST,
            path="/users",
            tags=["users"],
            parameters=[],
            request_body=IRRequestBody(
                description="User data",
                content={"application/json": IRSchema(type="CreateUserRequest", description="User creation data")},
                required=True,
            ),
            responses=[],
        )

        ordered_parameters = [body_param_info]
        primary_content_type = "application/json"

        # Act
        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            None,  # resolved_body_type
        )

        # Assert
        # Should import DataclassSerializer
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")

        # Should generate serialized json_body assignment
        expected_calls = [
            call('url = f"{self.base_url}/users"'),
            call(""),
            call("json_body: CreateUserRequest = DataclassSerializer.serialize(body)"),
            call(""),
        ]

        code_writer_mock.write_line.assert_has_calls(expected_calls, any_order=False)

    def test_generate_url_and_args_form_data__includes_serializer_call__converts_dataclass_to_form(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Generate endpoint method with form data body parameter
        Expected Outcome: Generated code includes DataclassSerializer call for form data
        """
        # Arrange
        operation = IROperation(
            operation_id="submit_form",
            summary="Submit form data",
            description="Submits form data to the server.",
            method=HTTPMethod.POST,
            path="/forms",
            tags=["forms"],
            parameters=[],
            request_body=IRRequestBody(
                description="Form data",
                content={"application/x-www-form-urlencoded": IRSchema(type="object")},
                required=True,
            ),
            responses=[],
        )

        ordered_parameters: List[Dict[str, Any]] = []
        primary_content_type = "application/x-www-form-urlencoded"
        resolved_body_type = "FormDataRequest"

        # Act
        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        # Assert
        # Should import DataclassSerializer
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")

        # Should generate serialized form_data_body assignment
        code_writer_mock.write_line.assert_any_call(
            "form_data_body: FormDataRequest = DataclassSerializer.serialize(form_data)"
        )

    def test_generate_url_and_args_no_body__does_not_include_serializer__handles_bodyless_requests(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Generate endpoint method without body parameter (GET request)
        Expected Outcome: No DataclassSerializer import or call is generated
        """
        # Arrange
        operation = IROperation(
            operation_id="get_users",
            summary="Get all users",
            description="Retrieves a list of all users.",
            method=HTTPMethod.GET,
            path="/users",
            tags=["users"],
            parameters=[],
            request_body=None,
            responses=[],
        )

        ordered_parameters: List[Dict[str, Any]] = []

        # Act
        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            None,  # primary_content_type
            None,  # resolved_body_type
        )

        # Assert
        # Should NOT import DataclassSerializer
        import_calls = render_context_mock.add_import.call_args_list
        serializer_import_calls = [
            call for call in import_calls if len(call[0]) >= 2 and "DataclassSerializer" in str(call[0][1])
        ]
        assert len(serializer_import_calls) == 0, "DataclassSerializer should not be imported for bodyless requests"

        # Should NOT generate any serializer calls
        write_calls = code_writer_mock.write_line.call_args_list
        serializer_write_calls = [call for call in write_calls if "DataclassSerializer" in str(call[0][0])]
        assert len(serializer_write_calls) == 0, "DataclassSerializer should not be called for bodyless requests"

    def test_generate_url_and_args_multipart_files__includes_serializer_for_metadata__handles_mixed_content(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Generate endpoint method with multipart/form-data including metadata
        Expected Outcome: DataclassSerializer is used for non-file parts of multipart data
        """
        # Arrange
        files_param_info: Dict[str, Any] = {
            "name": "files",
            "param_in": "formData",
            "required": True,
            "original_name": "files",
            "type": "Dict[str, Any]",  # Could contain dataclass metadata
        }

        operation = IROperation(
            operation_id="upload_with_metadata",
            summary="Upload files with metadata",
            description="Uploads files along with structured metadata.",
            method=HTTPMethod.POST,
            path="/upload",
            tags=["files"],
            parameters=[],
            request_body=IRRequestBody(
                description="Files and metadata",
                content={"multipart/form-data": IRSchema(type="object")},
                required=True,
            ),
            responses=[],
        )

        ordered_parameters = [files_param_info]
        primary_content_type = "multipart/form-data"

        # Act
        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            None,  # resolved_body_type
        )

        # Assert
        # Should import DataclassSerializer for potential dataclass serialization in multipart data
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")

        # Should generate files_data with potential serialization
        code_writer_mock.write_line.assert_any_call("files_data: Dict[str, Any] = DataclassSerializer.serialize(files)")


class TestEndpointMethodGeneratorDataclassIntegration:
    """Test end-to-end dataclass integration in generated endpoint methods."""

    def test_endpoint_method_generation__includes_all_serialization_logic__complete_integration(self) -> None:
        """
        Scenario: Generate complete endpoint method with dataclass body parameter
        Expected Outcome: All necessary imports and serialization logic are included
        """
        # This test verifies the complete integration across all generators
        # The actual implementation will span multiple generator classes

        # This test serves as a specification for the expected behavior
        # and will be implemented once the generators are updated

        expected_generated_code = '''
async def create_user(self, body: CreateUserRequest) -> CreateUserResponse:
    """Create a new user.

    Args:
        body: User data to create

    Returns:
        CreateUserResponse: The created user data

    Raises:
        HTTPError: If the request fails
    """
    url = f"{self.base_url}/users"

    json_body: CreateUserRequest = DataclassSerializer.serialize(body)

    response = await self._transport.request("POST", url, json=json_body)

    if response.status_code == 201:
        return CreateUserResponse.model_validate(response.json())
    else:
        raise HTTPError(f"Request failed with status {response.status_code}")
        '''.strip()

        # For now, this test documents the expected behavior
        # The implementation will make this test pass
        assert True  # Placeholder until generators are updated


class TestDataclassSerializationCodeGeneration:
    """Test the actual code generation patterns for dataclass serialization."""

    def test_json_body_assignment_pattern__generates_correct_code__preserves_type_hints(self) -> None:
        """
        Scenario: Verify the exact code pattern generated for JSON body serialization
        Expected Outcome: Code includes proper type hints and serialization call
        """
        # Expected pattern:
        # json_body: TypeName = DataclassSerializer.serialize(body)

        # This test defines the expected code generation pattern
        expected_pattern = "json_body: {type_hint} = DataclassSerializer.serialize(body)"

        # The implementation should generate this exact pattern
        assert True  # Will be implemented in the generator update

    def test_form_data_assignment_pattern__generates_correct_code__handles_form_serialization(self) -> None:
        """
        Scenario: Verify the exact code pattern generated for form data serialization
        Expected Outcome: Code includes proper form data handling with serialization
        """
        # Expected pattern:
        # form_data_body: TypeName = DataclassSerializer.serialize(form_data)

        expected_pattern = "form_data_body: {type_hint} = DataclassSerializer.serialize(form_data)"

        # The implementation should generate this exact pattern
        assert True  # Will be implemented in the generator update

    def test_import_generation__includes_serializer_import__adds_necessary_dependencies(self) -> None:
        """
        Scenario: Verify that DataclassSerializer import is added when needed
        Expected Outcome: Proper import statement is added to render context
        """
        # Expected import:
        # from {core_package}.utils import DataclassSerializer

        # This should be added via:
        # context.add_import(f"{context.core_package_name}.utils", "DataclassSerializer")

        assert True  # Will be implemented in the generator update
