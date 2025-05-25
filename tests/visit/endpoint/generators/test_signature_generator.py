"""
Tests for the EndpointMethodSignatureGenerator class.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRParameter, IRSchema
from pyopenapi_gen.visit.endpoint.generators.signature_generator import EndpointMethodSignatureGenerator


@pytest.fixture
def op_for_sig_basic() -> IROperation:
    return IROperation(
        path="/basic",
        method=HTTPMethod.GET,
        operation_id="get_basic",
        summary="Basic op sum",
        description="Basic op desc",
        parameters=[],
        responses=[],
    )


@pytest.fixture
def op_for_sig_with_params() -> IROperation:
    return IROperation(
        path="/params/{id}",
        method=HTTPMethod.POST,
        operation_id="create_item",
        summary="Param op sum",
        description="Param op desc",
        parameters=[
            IRParameter(name="id", param_in="path", required=True, schema=IRSchema(type="integer")),
            IRParameter(name="limit", param_in="query", required=False, schema=IRSchema(type="integer")),
            IRParameter(name="token", param_in="header", required=True, schema=IRSchema(type="string")),
        ],
        responses=[],  # Assume simple response for signature testing
    )


@pytest.fixture
def render_context_mock_for_sig() -> MagicMock:
    mock = MagicMock(spec=RenderContext)
    mock.core_package_name = "test_core"
    mock.add_typing_imports_for_type = MagicMock()
    mock.add_plain_import = MagicMock()
    return mock


@pytest.fixture
def schemas_for_sig() -> Dict[str, IRSchema]:
    return {}


class TestEndpointMethodSignatureGenerator:
    def test_generate_signature_no_params(
        self,
        op_for_sig_basic: IROperation,
        render_context_mock_for_sig: MagicMock,
        schemas_for_sig: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation with no parameters.
        Expected: async def get_basic(self) -> None:
        """
        generator = EndpointMethodSignatureGenerator(schemas=schemas_for_sig)
        writer = CodeWriter()
        ordered_params_from_processor: List[Dict[str, Any]] = []

        with patch(
            "pyopenapi_gen.visit.endpoint.generators.signature_generator.get_return_type", return_value=("None", False)
        ):
            generator.generate_signature(
                writer, op_for_sig_basic, render_context_mock_for_sig, ordered_params_from_processor
            )

        generated_code = writer.get_code().strip()
        expected_signature_parts = ["async def get_basic(", "    self,", ") -> None:"]
        actual_lines = [line.strip() for line in generated_code.splitlines() if line.strip()]
        expected_lines = [line.strip() for line in expected_signature_parts if line.strip()]
        assert actual_lines[: len(expected_lines)] == expected_lines
        render_context_mock_for_sig.add_typing_imports_for_type.assert_any_call("None")

    def test_generate_signature_with_params(
        self,
        op_for_sig_with_params: IROperation,
        render_context_mock_for_sig: MagicMock,
        schemas_for_sig: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation with path, query (optional), and header parameters.
        Expected: async def create_item(self, id: int, token: str, limit: Optional[int] = None) -> SomeReturnType:
        """
        generator = EndpointMethodSignatureGenerator(schemas=schemas_for_sig)
        writer = CodeWriter()

        ordered_params_from_processor: List[Dict[str, Any]] = [
            {"name": "id", "type": "int", "required": True, "param_in": "path", "original_name": "id"},
            {"name": "token", "type": "str", "required": True, "param_in": "header", "original_name": "token"},
            {
                "name": "limit",
                "type": "Optional[int]",
                "required": False,
                "default": None,
                "param_in": "query",
                "original_name": "limit",
            },
        ]

        with (
            patch(
                "pyopenapi_gen.visit.endpoint.generators.signature_generator.get_return_type",
                return_value=("SomeReturnType", False),
            ) as mock_get_return,
            patch("pyopenapi_gen.visit.endpoint.generators.signature_generator.get_param_type") as mock_get_param_type,
        ):
            mock_get_param_type.side_effect = lambda param_spec, ctx, schemas_dict: {
                "id": "int",
                "limit": "Optional[int]",
                "token": "str",
            }.get(param_spec.name, "Any")

            generator.generate_signature(
                writer, op_for_sig_with_params, render_context_mock_for_sig, ordered_params_from_processor
            )

        generated_code = writer.get_code().strip()
        expected_signature_parts = [
            "async def create_item(",
            "    self,",
            "    id_: int,",  # 'id' is sanitized to 'id_'
            "    token: str,",
            "    limit: Optional[int] = None,",
            ") -> SomeReturnType:",
        ]
        actual_lines = [line.strip() for line in generated_code.splitlines() if line.strip()]
        expected_lines = [line.strip() for line in expected_signature_parts if line.strip()]
        assert actual_lines[: len(expected_lines)] == expected_lines

        render_context_mock_for_sig.add_typing_imports_for_type.assert_any_call("int")
        render_context_mock_for_sig.add_typing_imports_for_type.assert_any_call("str")
        render_context_mock_for_sig.add_typing_imports_for_type.assert_any_call("Optional[int]")
        render_context_mock_for_sig.add_typing_imports_for_type.assert_any_call("SomeReturnType")
