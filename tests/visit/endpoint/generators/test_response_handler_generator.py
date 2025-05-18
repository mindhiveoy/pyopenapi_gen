import unittest
from unittest.mock import MagicMock

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRResponse, IRSchema
from pyopenapi_gen.visit.endpoint.generators.response_handler_generator import EndpointResponseHandlerGenerator


class TestEndpointResponseHandlerGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.render_context_mock = MagicMock(spec=RenderContext)
        self.render_context_mock.import_collector = MagicMock()
        self.render_context_mock.import_collector._current_file_module_dot_path = "some.dummy.path"
        self.code_writer_mock = MagicMock(spec=CodeWriter)
        self.generator = EndpointResponseHandlerGenerator()
        self.mock_op = MagicMock(spec=IROperation)
        self.mock_op.responses = []
        self.render_context_mock.name_sanitizer = MagicMock()

    def test_generate_response_handling_success_json(self) -> None:
        """
        Scenario:
            Test response handling for a successful JSON response where the return type is a known model.
        Expected Outcome:
            The generated code should cast the JSON response to the specified model type.
            The model type and 'cast' should be imported.
        """
        success_response_schema = IRSchema(type="object", properties={"id": IRSchema(type="integer")}, name="Item")
        operation = IROperation(
            operation_id="get_item",
            summary="Get an item",
            description="Retrieve a single item.",
            method=HTTPMethod.GET,
            path="/items/{item_id}",
            tags=["items"],
            parameters=[],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Successful response",
                    content={"application/json": success_response_schema},
                )
            ],
        )
        self.render_context_mock.name_sanitizer.sanitize_class_name.return_value = "Item"
        self.render_context_mock.core_package_name = "test_client.core"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("Item", False),
        ) as mock_get_return_type:
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

            mock_get_return_type.assert_called_once_with(operation, self.render_context_mock, self.generator.schemas)
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("Item")

            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

            self.assertIn("if response.status_code == 200:", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip() == "return cast(Item, response.json())"
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )
            self.render_context_mock.add_import.assert_any_call(
                f"{self.render_context_mock.core_package_name}.exceptions", "HTTPError"
            )
            self.render_context_mock.add_import.assert_any_call("typing", "cast")

    def test_generate_response_handling_for_none_return_type(self) -> None:
        """
        Scenario:
            Test response handling when get_return_type indicates "None" (e.g., for a 204 response).
        Expected Outcome:
            The generated code should simply be "return None".
        """
        operation = IROperation(
            operation_id="delete_item",
            method=HTTPMethod.DELETE,
            path="/items/{item_id}",
            responses=[IRResponse(status_code="204", description="No Content", content={})],
            summary="delete",
            description="delete",
        )
        self.render_context_mock.core_package_name = "test_client.core"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("None", False),
        ) as mock_get_return_type:
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

            mock_get_return_type.assert_called_once()
            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])
            self.assertIn("if response.status_code == 204:", written_code)
            self.assertTrue(
                any(c[0][0].strip() == "return None" for c in self.code_writer_mock.write_line.call_args_list)
            )
            self.render_context_mock.add_import.assert_any_call(
                f"{self.render_context_mock.core_package_name}.exceptions", "HTTPError"
            )

    def test_get_extraction_code_primitive_str(self) -> None:
        """
        Scenario:
            _get_extraction_code is called with return_type="str".
        Expected Outcome:
            Returns "response.text".
        """
        code = self.generator._get_extraction_code(
            return_type="str", context=self.render_context_mock, op=self.mock_op, needs_unwrap=False
        )
        self.assertEqual(code, "response.text")

    def test_get_extraction_code_primitive_bytes(self) -> None:
        """
        Scenario:
            _get_extraction_code is called with return_type="bytes".
        Expected Outcome:
            Returns "response.content".
        """
        code = self.generator._get_extraction_code(
            return_type="bytes", context=self.render_context_mock, op=self.mock_op, needs_unwrap=False
        )
        self.assertEqual(code, "response.content")

    def test_get_extraction_code_any_type(self) -> None:
        """
        Scenario:
            _get_extraction_code is called with return_type="Any".
        Expected Outcome:
            Returns "response.json()  # Type is Any" and registers import for Any.
        """
        code = self.generator._get_extraction_code(
            return_type="Any", context=self.render_context_mock, op=self.mock_op, needs_unwrap=False
        )
        self.assertEqual(code, "response.json()  # Type is Any")
        self.render_context_mock.add_import.assert_called_with("typing", "Any")

    def test_get_extraction_code_model_type(self) -> None:
        """
        Scenario:
            _get_extraction_code is called with a model type string (e.g., "MyModel").
        Expected Outcome:
            Returns "cast(MyModel, response.json())" and registers imports for the model and cast.
        """
        code = self.generator._get_extraction_code(
            return_type="MyModel", context=self.render_context_mock, op=self.mock_op, needs_unwrap=False
        )
        self.assertEqual(code, "cast(MyModel, response.json())")
        self.render_context_mock.add_typing_imports_for_type.assert_called_with("MyModel")
        self.render_context_mock.add_import.assert_any_call("typing", "cast")

    def test_get_extraction_code_model_type_with_unwrap(self) -> None:
        """
        Scenario:
            _get_extraction_code is called for a model type with needs_unwrap=True.
        Expected Outcome:
            Returns multi-line code for unwrapping 'data' key and casting, and registers imports.
        """
        expected_code = (
            "raw_data = response.json().get('data')\n"
            "if raw_data is None:\n"
            "    raise ValueError(\"Expected 'data' key in response but found None\")\n"
            "return cast(MyDataModel, raw_data)"
        )
        code = self.generator._get_extraction_code(
            return_type="MyDataModel", context=self.render_context_mock, op=self.mock_op, needs_unwrap=True
        )
        self.assertEqual(code, expected_code)
        self.render_context_mock.add_typing_imports_for_type.assert_called_with("MyDataModel")
        self.render_context_mock.add_import.assert_any_call("typing", "cast")

    def test_generate_response_handling_error_404(self) -> None:
        """
        Scenario:
            Test response handling for a 404 Not Found error.
        Expected Outcome:
            The generated code should raise Error404(response=response).
            Error404 and HTTPError should be imported.
        """
        operation = IROperation(
            operation_id="get_missing_item",
            method=HTTPMethod.GET,
            path="/items/{item_id}",
            responses=[IRResponse(status_code="404", description="Not Found", content={})],
            summary="get missing",
            description="get missing",
        )
        self.render_context_mock.core_package_name = "test_client.core"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("Any", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

            self.assertIn("if response.status_code == 404:", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip() == "raise Error404(response=response)"
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )

            self.render_context_mock.add_import.assert_any_call(
                f"{self.render_context_mock.core_package_name}", "Error404"
            )
            self.render_context_mock.add_import.assert_any_call(
                f"{self.render_context_mock.core_package_name}.exceptions", "HTTPError"
            )

    def test_generate_response_handling_unhandled_error(self) -> None:
        """
        Scenario:
            Test response handling for an undefined/unhandled error status code.
        Expected Outcome:
            The generated code should fall into the final else block and raise HTTPError(response=response).
            HTTPError should be imported.
        """
        operation = IROperation(
            operation_id="op_no_responses",
            method=HTTPMethod.GET,
            path="/unknown",
            responses=[],
            summary="unknown",
            description="unknown",
        )
        self.render_context_mock.core_package_name = "test_client.core"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("Any", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

            self.assertIn("if True: # Should ideally not happen if responses are defined", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip()
                    == 'raise HTTPError(response=response, message="Unhandled status code", status_code=response.status_code)'
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )

            self.render_context_mock.add_import.assert_any_call(
                f"{self.render_context_mock.core_package_name}.exceptions", "HTTPError"
            )

    def test_generate_response_handling_default_as_success_only_response(self) -> None:
        """
        Scenario:
            Operation has only a 'default' response with a schema, implying success.
        Expected Outcome:
            Code should check 'response.status_code >= 0' and parse the response.
        """
        default_schema = IRSchema(type="object", name="DefaultSuccessData")
        operation = IROperation(
            operation_id="op_default_success_only",
            method=HTTPMethod.GET,
            path="/default_success",
            responses=[
                IRResponse(
                    status_code="default",
                    description="Default success response",
                    content={"application/json": default_schema},
                )
            ],
            summary="default success",
            description="default success",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.return_value = "DefaultSuccessData"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("DefaultSuccessData", False),
        ) as mock_get_return_type:
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

            self.assertIn("if response.status_code >= 0: # Default response catch-all", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip() == "return cast(DefaultSuccessData, response.json())"
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("DefaultSuccessData")
            self.render_context_mock.add_import.assert_any_call("typing", "cast")
            self.assertIn(
                'raise HTTPError(response=response, message="Unhandled status code", status_code=response.status_code)',
                written_code,
            )

    def test_generate_response_handling_default_as_fallback_error(self) -> None:
        """
        Scenario:
            Operation has a 200 OK and a 'default' response (no content), implying 'default' is for errors.
        Expected Outcome:
            Code handles 200, then for other codes, catches with 'default' and raises HTTPError.
        """
        success_schema = IRSchema(type="object", name="SuccessData")
        operation = IROperation(
            operation_id="op_default_fallback_error",
            method=HTTPMethod.GET,
            path="/default_error",
            responses=[
                IRResponse(
                    status_code="200",
                    description="OK",
                    content={"application/json": success_schema},
                ),
                IRResponse(
                    status_code="default",
                    description="A generic error occurred.",
                    content={},
                ),
            ],
            summary="default fallback",
            description="default fallback",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.return_value = "SuccessData"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("SuccessData", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

            self.assertIn("if response.status_code == 200:", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip() == "return cast(SuccessData, response.json())"
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )

            self.assertIn("elif response.status_code >= 0: # Default response catch-all", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip()
                    == 'raise HTTPError(response=response, message="Default error: A generic error occurred.", status_code=response.status_code)'
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )
            self.render_context_mock.add_import.assert_any_call(
                f"{self.render_context_mock.core_package_name}.exceptions", "HTTPError"
            )

    def test_generate_response_handling_default_as_primary_success_heuristic(self) -> None:
        """
        Scenario:
            Operation has no 2xx, only a 'default' response with content.
            _get_primary_response heuristic should pick 'default' as primary success.
        Expected Outcome:
            The 'default' response is handled in the `other_responses` loop.
        """
        default_schema = IRSchema(type="object", name="PrimaryDefault")
        operation = IROperation(
            operation_id="op_primary_default",
            method=HTTPMethod.POST,
            path="/primary_default",
            responses=[
                IRResponse(
                    status_code="default",
                    description="The default outcome",
                    content={"application/json": default_schema},
                )
            ],
            summary="primary default",
            description="primary default",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.return_value = "PrimaryDefault"

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
                return_value=("PrimaryDefault", False),
            ),
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.generators.response_handler_generator._get_primary_response",
                return_value=operation.responses[0],
            ),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)
            written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

            self.assertIn("if response.status_code >= 0: # Default response catch-all", written_code)
            self.assertTrue(
                any(
                    c[0][0].strip() == "return cast(PrimaryDefault, response.json())"
                    for c in self.code_writer_mock.write_line.call_args_list
                )
            )
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("PrimaryDefault")

    def test_generate_response_handling_multiple_2xx_distinct_types(self) -> None:
        """
        Scenario:
            Operation has multiple 2xx responses with different schemas (e.g., 200 -> ModelA, 201 -> ModelB).
        Expected Outcome:
            Generated code should correctly parse and cast to ModelA for 200, and ModelB for 201.
            Imports for ModelA, ModelB, and cast should be registered.
        """
        schema_a = IRSchema(type="object", name="ModelA", properties={"id": IRSchema(type="string")})
        schema_b = IRSchema(type="object", name="ModelB", properties={"value": IRSchema(type="integer")})

        operation = IROperation(
            operation_id="op_multi_2xx",
            method=HTTPMethod.POST,
            path="/multi_success",
            responses=[
                IRResponse(status_code="200", description="Standard success", content={"application/json": schema_a}),
                IRResponse(status_code="201", description="Resource created", content={"application/json": schema_b}),
            ],
            summary="multi 2xx",
            description="multi 2xx",
        )
        self.render_context_mock.core_package_name = "test_client.core"

        def sanitize_side_effect(name: str) -> str:
            if name == "ModelA":
                return "ModelA"
            if name == "ModelB":
                return "ModelB"
            return name

        self.render_context_mock.name_sanitizer.sanitize_class_name.side_effect = sanitize_side_effect

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("ModelA", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

        self.assertIn("if response.status_code == 200:", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "return cast(ModelA, response.json())"
                for c in self.code_writer_mock.write_line.call_args_list
            )
        )
        self.render_context_mock.add_typing_imports_for_type.assert_any_call("ModelA")

        self.assertIn("elif response.status_code == 201:", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "return cast(ModelB, response.json())"
                for c in self.code_writer_mock.write_line.call_args_list
            )
        )
        self.render_context_mock.add_typing_imports_for_type.assert_any_call("ModelB")

        self.render_context_mock.add_import.assert_any_call("typing", "cast")
        self.render_context_mock.add_import.assert_any_call(
            f"{self.render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_generate_response_handling_streaming_bytes(self) -> None:
        """
        Scenario: Operation returns a 200 OK with application/octet-stream, yielding bytes.
        Expected Outcome: Generated code should use 'async for chunk in iter_bytes(response): yield chunk'.
        """
        operation = IROperation(
            operation_id="op_stream_bytes",
            method=HTTPMethod.GET,
            path="/stream/bytes",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Byte stream",
                    content={"application/octet-stream": IRSchema(type="string", format="binary")},
                )
            ],
            summary="stream bytes",
            description="stream bytes",
        )
        self.render_context_mock.core_package_name = "test_client.core"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("AsyncIterator[bytes]", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

        self.assertIn("if response.status_code == 200:", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "async for chunk in iter_bytes(response):"
                for c in self.code_writer_mock.write_line.call_args_list
            )
        )
        self.assertTrue(any(c[0][0].strip() == "yield chunk" for c in self.code_writer_mock.write_line.call_args_list))
        self.assertTrue(
            any(
                c[0][0].strip() == "return  # Explicit return for async generator"
                for c in self.code_writer_mock.write_line.call_args_list
            )
        )

        self.render_context_mock.add_import.assert_any_call(
            f"{self.render_context_mock.core_package_name}.streaming_helpers", "iter_bytes"
        )

    def test_generate_response_handling_streaming_sse(self) -> None:
        """
        Scenario: Operation returns a 200 OK with text/event-stream, yielding parsed JSON objects.
        Expected Outcome: Generated code uses 'async for chunk in iter_sse_events_text(response): yield json.loads(chunk)'.
        """
        event_data_schema = IRSchema(type="object", name="EventData", properties={"id": IRSchema(type="string")})
        operation = IROperation(
            operation_id="op_stream_sse",
            method=HTTPMethod.GET,
            path="/stream/sse",
            responses=[
                IRResponse(
                    status_code="200",
                    description="SSE stream",
                    content={"text/event-stream": event_data_schema},
                )
            ],
            summary="stream sse",
            description="stream sse",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.return_value = "EventData"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("AsyncIterator[EventData]", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

        self.assertIn("if response.status_code == 200:", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "async for chunk in iter_sse_events_text(response):"
                for c in self.code_writer_mock.write_line.call_args_list
            )
        )
        self.assertTrue(
            any(c[0][0].strip() == "yield json.loads(chunk)" for c in self.code_writer_mock.write_line.call_args_list)
        )
        self.assertTrue(
            any(
                c[0][0].strip() == "return  # Explicit return for async generator"
                for c in self.code_writer_mock.write_line.call_args_list
            )
        )

        self.render_context_mock.add_import.assert_any_call(
            f"{self.render_context_mock.core_package_name}.streaming_helpers", "iter_sse_events_text"
        )
        self.render_context_mock.add_plain_import.assert_any_call("json")

    def test_generate_response_handling_union_return_type(self) -> None:
        """
        Scenario: Operation returns a 200 OK, and the type is a Union[ModelA, ModelB].
        Expected Outcome: Generated code should try to parse as ModelA, then ModelB on exception.
        """
        schema_a = IRSchema(type="object", name="ModelA")
        schema_b = IRSchema(type="object", name="ModelB")

        operation = IROperation(
            operation_id="op_union_type",
            method=HTTPMethod.GET,
            path="/union_data",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Data that could be ModelA or ModelB",
                    content={"application/json": schema_a},
                )
            ],
            summary="union type",
            description="union type",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.side_effect = lambda name: name

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("Union[ModelA, ModelB]", False),
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

        self.assertIn("if response.status_code == 200:", written_code)
        self.assertIn("try:", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "return cast(ModelA, response.json())"
                for c in self.code_writer_mock.write_line.call_args_list
                if "try:" in written_code and "except Exception:" not in written_code[: written_code.find(c[0][0])]
            )
        )
        self.assertIn("except Exception:  # Attempt to parse as the second type", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "return cast(ModelB, response.json())"
                for c in self.code_writer_mock.write_line.call_args_list
                if "except Exception:" in written_code[: written_code.find(c[0][0])]
            )
        )

        self.render_context_mock.add_import.assert_any_call("typing", "Union")
        self.render_context_mock.add_import.assert_any_call("typing", "cast")
        self.render_context_mock.add_typing_imports_for_type.assert_any_call("ModelA")
        self.render_context_mock.add_typing_imports_for_type.assert_any_call("ModelB")

    def test_generate_response_handling_union_return_type_with_unwrap_first(self) -> None:
        """
        Scenario: Op returns 200 OK, type is Union[ModelA, ModelB], and needs_unwrap is True.
                  Assume ModelA is parsed successfully first.
        Expected Outcome: Multi-line extraction for ModelA (due to unwrap) is generated in the 'try' block.
        """
        schema_a = IRSchema(type="object", name="ModelA")
        schema_b = IRSchema(type="object", name="ModelB")
        operation = IROperation(
            operation_id="op_union_unwrap",
            method=HTTPMethod.GET,
            path="/union_unwrap",
            responses=[
                IRResponse(status_code="200", description="Union with unwrap", content={"application/json": schema_a})
            ],
            summary="union unwrap",
            description="union unwrap",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.side_effect = lambda name: name

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("Union[ModelA, ModelB]", True),  # needs_unwrap = True
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

        written_code_union = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])
        written_lines_stripped_union = [c[0][0].strip() for c in self.code_writer_mock.write_line.call_args_list]

        self.assertIn("if response.status_code == 200:", written_code_union)
        self.assertIn("try:", written_code_union)
        # Check for ModelA unwrap logic
        self.assertIn("raw_data = response.json().get('data')", written_lines_stripped_union)
        self.assertIn("if raw_data is None:", written_lines_stripped_union)
        self.assertIn(
            "raise ValueError(\"Expected 'data' key in response but found None\")", written_lines_stripped_union
        )
        self.assertIn("return_value = cast(ModelA, raw_data)", written_lines_stripped_union)
        self.assertIn("return return_value", written_lines_stripped_union)
        self.assertIn("except Exception:", written_code_union)

    def test_generate_response_handling_simple_type_with_unwrap(self) -> None:
        """
        Scenario: Op returns 200 OK, type is ModelC, and needs_unwrap is True.
        Expected Outcome: Multi-line extraction for ModelC (due to unwrap) is generated.
        """
        schema_c = IRSchema(type="object", name="ModelC")
        operation = IROperation(
            operation_id="op_simple_unwrap",
            method=HTTPMethod.GET,
            path="/simple_unwrap",
            responses=[
                IRResponse(status_code="200", description="Simple unwrap", content={"application/json": schema_c})
            ],
            summary="simple unwrap",
            description="simple unwrap",
        )
        self.render_context_mock.core_package_name = "test_client.core"
        self.render_context_mock.name_sanitizer.sanitize_class_name.return_value = "ModelC"

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator.get_return_type",
            return_value=("ModelC", True),  # needs_unwrap = True
        ):
            self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])
        written_lines_stripped = [c[0][0].strip() for c in self.code_writer_mock.write_line.call_args_list]

        self.assertIn("if response.status_code == 200:", written_code)
        self.assertIn("raw_data = response.json().get('data')", written_lines_stripped)
        self.assertIn("if raw_data is None:", written_lines_stripped)
        self.assertIn("raise ValueError(\"Expected 'data' key in response but found None\")", written_lines_stripped)
        self.assertIn("return cast(ModelC, raw_data)", written_lines_stripped)

        # Ensure these are directly written, not via a temp 'return_value' as in Union
        self.assertNotIn("return_value = cast(ModelC, raw_data)", written_code)
        self.assertNotIn("return return_value", written_code)


if __name__ == "__main__":
    unittest.main()
