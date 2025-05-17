import unittest
from unittest.mock import MagicMock

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRRequestBody, IRSchema
from pyopenapi_gen.visit.endpoint.generators.request_generator import EndpointRequestGenerator


class TestEndpointRequestGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.render_context_mock = MagicMock(spec=RenderContext)
        self.code_writer_mock = MagicMock(spec=CodeWriter)
        self.generator = EndpointRequestGenerator()

    def test_generate_request_call_get_no_body(self) -> None:
        """Test generating a GET request call with no body and no specific params/headers."""
        operation = IROperation(
            operation_id="get_items",
            summary="Get items",
            description="Retrieve items.",
            method=HTTPMethod.GET,
            path="/items",
            tags=["items"],
            parameters=[],
            request_body=None,
            responses=[],
        )

        self.generator.generate_request_call(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            has_header_params=False,
            primary_content_type=None,
        )

        all_written_lines = "".join(c[0][0] for c in self.code_writer_mock.write_line.call_args_list)

        self.assertIn('("GET", url', all_written_lines)
        self.assertNotIn('method="GET"', all_written_lines)
        self.assertIn("params=None", all_written_lines)
        self.assertIn("json=None", all_written_lines)
        self.assertIn("data=None", all_written_lines)
        self.assertIn("headers=None", all_written_lines)
        # self.assertIn("timeout=timeout", all_written_lines) # Timeout is not currently added
        self.assertIn(")", all_written_lines)
        self.code_writer_mock.write_line.assert_any_call("")

    def test_generate_request_call_post_json_body(self) -> None:
        """Test generating a POST request call with a JSON body."""
        request_body_schema = IRSchema(type="object", properties={"name": IRSchema(type="string")})
        operation = IROperation(
            operation_id="create_item",
            summary="Create an item",
            description="Create a new item.",
            method=HTTPMethod.POST,
            path="/items",
            tags=["items"],
            parameters=[],
            request_body=IRRequestBody(required=True, content={"application/json": request_body_schema}),
            responses=[],
        )

        self.generator.generate_request_call(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            has_header_params=False,
            primary_content_type="application/json",
        )

        all_written_lines = "".join(c[0][0] for c in self.code_writer_mock.write_line.call_args_list)
        self.assertIn('("POST", url', all_written_lines)
        self.assertNotIn('method="POST"', all_written_lines)
        self.assertIn("json=json_body", all_written_lines)
        self.assertIn("params=None", all_written_lines)
        self.assertIn("headers=None", all_written_lines)
        # self.assertIn("timeout=timeout", all_written_lines) # Timeout is not currently added
        self.code_writer_mock.write_line.assert_any_call("")


if __name__ == "__main__":
    unittest.main()
