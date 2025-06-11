import unittest
from unittest.mock import Mock, MagicMock

import pytest

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRResponse, IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.generators.response_handler_generator import EndpointResponseHandlerGenerator


class TestEndpointResponseHandlerGenerator:
    """Test the response handler generator with the new ResponseStrategy pattern."""
    
    @pytest.fixture
    def render_context_mock(self):
        """Mock render context."""
        context = MagicMock(spec=RenderContext)
        context.import_collector = MagicMock()
        context.import_collector._current_file_module_dot_path = "some.dummy.path"
        context.name_sanitizer = MagicMock()
        context.core_package_name = "test_client.core"
        return context
        
    @pytest.fixture
    def code_writer_mock(self):
        """Mock code writer."""
        return MagicMock(spec=CodeWriter)
        
    @pytest.fixture
    def generator(self):
        """Response handler generator instance."""
        return EndpointResponseHandlerGenerator()
        
    @pytest.fixture
    def mock_op(self):
        """Mock operation."""
        op = MagicMock(spec=IROperation)
        op.responses = []
        return op

    def test_generate_response_handling_success_json(self, generator, code_writer_mock, render_context_mock) -> None:
        """
        Scenario: Test response handling for a successful JSON response with a known model
        Expected Outcome: Generated code uses BaseSchema deserialization and imports model
        """
        # Arrange
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
        
        strategy = ResponseStrategy(
            return_type="Item",
            response_schema=success_response_schema,
            is_streaming=False,
            response_ir=operation.responses[0]
        )
        
        render_context_mock.name_sanitizer.sanitize_class_name.return_value = "Item"

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])
        
        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert any(
            c[0][0].strip() == "return Item.from_dict(response.json())"
            for c in code_writer_mock.write_line.call_args_list
        )
        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_generate_response_handling_for_none_return_type(self, generator, code_writer_mock, render_context_mock) -> None:
        """
        Scenario: Test response handling for None return type (e.g., 204 response)
        Expected Outcome: Generated code simply returns None
        """
        # Arrange
        operation = IROperation(
            operation_id="delete_item",
            method=HTTPMethod.DELETE,
            path="/items/{item_id}",
            responses=[IRResponse(status_code="204", description="No Content", content={})],
            summary="delete",
            description="delete",
        )
        
        strategy = ResponseStrategy(
            return_type="None",
            response_schema=None,
            is_streaming=False,
            response_ir=operation.responses[0]
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])
        assert "match response.status_code:" in written_code
        assert "case 204:" in written_code
        assert any(c[0][0].strip() == "return None" for c in code_writer_mock.write_line.call_args_list)
        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_get_extraction_code_primitive_str(self, generator, render_context_mock, mock_op) -> None:
        """
        Scenario: _get_extraction_code is called with return_type="str"
        Expected Outcome: Returns "response.text"
        """
        # Act
        code = generator._get_extraction_code(
            return_type="str", context=render_context_mock, op=mock_op
        )
        
        # Assert
        assert code == "response.text"

    def test_get_extraction_code_primitive_bytes(self, generator, render_context_mock, mock_op) -> None:
        """
        Scenario: _get_extraction_code is called with return_type="bytes"
        Expected Outcome: Returns "response.content"
        """
        # Act
        code = generator._get_extraction_code(
            return_type="bytes", context=render_context_mock, op=mock_op
        )
        
        # Assert
        assert code == "response.content"

    def test_get_extraction_code_any_type(self, generator, render_context_mock, mock_op) -> None:
        """
        Scenario: _get_extraction_code is called with return_type="Any"
        Expected Outcome: Returns "response.json()  # Type is Any" and registers import for Any
        """
        # Act
        code = generator._get_extraction_code(
            return_type="Any", context=render_context_mock, op=mock_op
        )
        
        # Assert
        assert code == "response.json()  # Type is Any"
        render_context_mock.add_import.assert_called_with("typing", "Any")

    def test_get_extraction_code_model_type(self, generator, render_context_mock, mock_op) -> None:
        """
        Scenario: _get_extraction_code is called with a model type string (e.g., "MyModel")
        Expected Outcome: Returns "MyModel.from_dict(response.json())" for BaseSchema deserialization and registers imports
        """
        # Act
        code = generator._get_extraction_code(
            return_type="MyModel", context=render_context_mock, op=mock_op
        )
        
        # Assert
        assert code == "MyModel.from_dict(response.json())"
        render_context_mock.add_typing_imports_for_type.assert_called_with("MyModel")

    def test_get_extraction_code_model_type_no_unwrapping(self, generator, render_context_mock, mock_op) -> None:
        """
        Scenario: _get_extraction_code is called for a model type 
        Expected Outcome: Returns direct BaseSchema deserialization (no unwrapping)
        """
        # Act
        code = generator._get_extraction_code(
            return_type="MyDataModel", context=render_context_mock, op=mock_op
        )
        
        # Assert
        assert code == "MyDataModel.from_dict(response.json())"
        render_context_mock.add_typing_imports_for_type.assert_called_with("MyDataModel")

    def test_generate_response_handling_error_404(self, generator, code_writer_mock, render_context_mock) -> None:
        """
        Scenario: Test response handling for a 404 Not Found error
        Expected Outcome: Generated code raises Error404(response=response) and imports are added
        """
        # Arrange
        operation = IROperation(
            operation_id="get_missing_item",
            method=HTTPMethod.GET,
            path="/items/{item_id}",
            responses=[IRResponse(status_code="404", description="Not Found", content={})],
            summary="get missing",
            description="get missing",
        )
        
        strategy = ResponseStrategy(
            return_type="Any",
            response_schema=None,
            is_streaming=False,
            response_ir=operation.responses[0]
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])
        
        assert "match response.status_code:" in written_code
        assert "case 404:" in written_code
        assert any(
            c[0][0].strip() == "raise Error404(response=response)"
            for c in code_writer_mock.write_line.call_args_list
        )
        
        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}", "Error404"
        )
        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_generate_response_handling_unhandled_error(self, generator, code_writer_mock, render_context_mock) -> None:
        """
        Scenario: Test response handling for an undefined/unhandled error status code
        Expected Outcome: Generated code falls into final else block and raises HTTPError
        """
        # Arrange
        operation = IROperation(
            operation_id="op_no_responses",
            method=HTTPMethod.GET,
            path="/unknown",
            responses=[],
            summary="unknown",
            description="unknown",
        )
        
        strategy = ResponseStrategy(
            return_type="Any",
            response_schema=None,
            is_streaming=False,
            response_ir=None
        )

        # Act
        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        # Assert
        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])
        
        assert "match response.status_code:" in written_code
        assert "case _:" in written_code
        assert any(
            c[0][0].strip()
            == 'raise HTTPError(response=response, message="Unhandled status code", status_code=response.status_code)'
            for c in code_writer_mock.write_line.call_args_list
        )
        
        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_generate_response_handling_default_as_success_only_response(self, generator, code_writer_mock, render_context_mock) -> None:
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
        render_context_mock.core_package_name = "test_client.core"

        # Create a ResponseStrategy for the default response
        strategy = ResponseStrategy(
            return_type="DefaultSuccessData",
            response_schema=default_schema,
            is_streaming=False,
            response_ir=operation.responses[0]  # default response
        )

        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        # Default case can be handled with case _ if status_code >= 0 or case _
        assert ("case _ if response.status_code >= 0:" in written_code or "case _:" in written_code)
        assert any(
            c[0][0].strip() == "return DefaultSuccessData.from_dict(response.json())"
            for c in code_writer_mock.write_line.call_args_list
        )
        render_context_mock.add_typing_imports_for_type.assert_any_call("DefaultSuccessData")

    def test_generate_response_handling_default_as_fallback_error(self, generator, code_writer_mock, render_context_mock) -> None:
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
        render_context_mock.core_package_name = "test_client.core"

        # Create a ResponseStrategy for the 200 response
        strategy = ResponseStrategy(
            return_type="SuccessData",
            response_schema=success_schema,
            is_streaming=False,
            response_ir=operation.responses[0]  # 200 response
        )

        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert any(
            c[0][0].strip() == "return SuccessData.from_dict(response.json())"
            for c in code_writer_mock.write_line.call_args_list
        )

        # Default case can be handled with case _ if status_code >= 0 or case _
        assert ("case _ if response.status_code >= 0:" in written_code or "case _:" in written_code)
        assert any(
            'raise HTTPError(response=response, message="Default error"' in c[0][0].strip()
            for c in code_writer_mock.write_line.call_args_list
        )
        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_generate_response_handling_default_as_primary_success_heuristic(self, generator, code_writer_mock, render_context_mock) -> None:
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
        render_context_mock.core_package_name = "test_client.core"
        render_context_mock.name_sanitizer.sanitize_class_name.return_value = "PrimaryDefault"

        # Create ResponseStrategy for the test
        strategy = ResponseStrategy(
            return_type="PrimaryDefault",
            response_schema=default_schema,
            is_streaming=False,
            response_ir=operation.responses[0]
        )

        with unittest.mock.patch(
            "pyopenapi_gen.visit.endpoint.generators.response_handler_generator._get_primary_response",
            return_value=operation.responses[0],
        ):
            generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)
            written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

            assert "match response.status_code:" in written_code
            # Default case can be handled with case _ if status_code >= 0 or case _
            assert ("case _ if response.status_code >= 0:" in written_code or "case _:" in written_code)
            assert any(
                c[0][0].strip() == "return PrimaryDefault.from_dict(response.json())"
                for c in code_writer_mock.write_line.call_args_list
            )
            # Verify that proper imports are registered
            render_context_mock.add_import.assert_any_call("typing", "NoReturn")

    def test_generate_response_handling_multiple_2xx_distinct_types(self, generator, code_writer_mock, render_context_mock) -> None:
        """
        Scenario:
            Operation has multiple 2xx responses with different schemas (e.g., 200 -> ModelA, 201 -> ModelB).
        Expected Outcome:
            Generated code should correctly parse and cast to ModelA for 200, and ModelB for 201.
            Imports for ModelA, ModelB, and cast should be registered.
        """
        schema_a = IRSchema(type="object", name="ModelA", properties={"id": IRSchema(type="string")})
        schema_b = IRSchema(type="object", name="ModelB", properties={"value": IRSchema(type="integer")})

        # Set generation_name so they're recognized as named schemas
        schema_a.generation_name = "ModelA"
        schema_b.generation_name = "ModelB"

        # Provide schemas to the generator  
        generator_with_schemas = EndpointResponseHandlerGenerator(schemas={"ModelA": schema_a, "ModelB": schema_b})

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
        render_context_mock.core_package_name = "test_client.core"

        def sanitize_side_effect(name: str) -> str:
            if name == "ModelA":
                return "ModelA"
            if name == "ModelB":
                return "ModelB"
            return name

        render_context_mock.name_sanitizer.sanitize_class_name.side_effect = sanitize_side_effect

        # Create ResponseStrategy for the test (using ModelA as primary response)
        strategy = ResponseStrategy(
            return_type="ModelA",
            response_schema=schema_a,
            is_streaming=False,
            response_ir=operation.responses[0]  # 200 response
        )

        generator_with_schemas.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert any(
            c[0][0].strip() == "return ModelA.from_dict(response.json())"
            for c in code_writer_mock.write_line.call_args_list
        )
        render_context_mock.add_typing_imports_for_type.assert_any_call("ModelA")

        assert "case 201:" in written_code
        assert any(
            c[0][0].strip() == "return ModelB.from_dict(response.json())"
            for c in code_writer_mock.write_line.call_args_list
        )
        render_context_mock.add_typing_imports_for_type.assert_any_call("ModelB")

        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.exceptions", "HTTPError"
        )

    def test_generate_response_handling_streaming_bytes(self, generator, code_writer_mock, render_context_mock) -> None:
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
        render_context_mock.core_package_name = "test_client.core"

        # Create ResponseStrategy for streaming bytes
        strategy = ResponseStrategy(
            return_type="AsyncIterator[bytes]",
            response_schema=operation.responses[0].content["application/octet-stream"],
            is_streaming=True,
            response_ir=operation.responses[0]
        )

        generator.generate_response_handling(code_writer_mock, operation, render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in code_writer_mock.write_line.call_args_list])

        assert "match response.status_code:" in written_code
        assert "case 200:" in written_code
        assert any(
            c[0][0].strip() == "async for chunk in iter_bytes(response):"
            for c in code_writer_mock.write_line.call_args_list
        )
        assert any(c[0][0].strip() == "yield chunk" for c in code_writer_mock.write_line.call_args_list)
        assert any(
            c[0][0].strip() == "return  # Explicit return for async generator"
            for c in code_writer_mock.write_line.call_args_list
        )

        render_context_mock.add_import.assert_any_call(
            f"{render_context_mock.core_package_name}.streaming_helpers", "iter_bytes"
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

        # Create ResponseStrategy for streaming SSE
        strategy = ResponseStrategy(
            return_type="AsyncIterator[EventData]",
            response_schema=event_data_schema,
            is_streaming=True,
            response_ir=operation.responses[0]
        )

        self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

        self.assertIn("match response.status_code:", written_code)
        self.assertIn("case 200:", written_code)
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

        # Create ResponseStrategy for Union return type
        strategy = ResponseStrategy(
            return_type="Union[ModelA, ModelB]",
            response_schema=schema_a,  # Primary schema
            is_streaming=False,
            response_ir=operation.responses[0]
        )

        self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])

        self.assertIn("match response.status_code:", written_code)
        self.assertIn("case 200:", written_code)
        self.assertIn("try:", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "return ModelA.from_dict(response.json())"
                for c in self.code_writer_mock.write_line.call_args_list
                if "try:" in written_code and "except Exception:" not in written_code[: written_code.find(c[0][0])]
            )
        )
        self.assertIn("except Exception:  # Attempt to parse as the second type", written_code)
        self.assertTrue(
            any(
                c[0][0].strip() == "return ModelB.from_dict(response.json())"
                for c in self.code_writer_mock.write_line.call_args_list
                if "except Exception:" in written_code[: written_code.find(c[0][0])]
            )
        )

        self.render_context_mock.add_import.assert_any_call("typing", "Union")
        self.render_context_mock.add_typing_imports_for_type.assert_any_call("ModelA")
        self.render_context_mock.add_typing_imports_for_type.assert_any_call("ModelB")

    def test_generate_response_handling_union_return_type_with_unwrap_first(self) -> None:
        """
        Scenario: Op returns 200 OK, type is Union[ModelA, ModelB], and needs_unwrap is True.
                  Assume ModelA is parsed successfully first.
        Expected Outcome: With unified service, simple cast behavior for Union types (no manual unwrapping).
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

        # Create ResponseStrategy for Union return type with unwrap
        strategy = ResponseStrategy(
            return_type="Union[ModelA, ModelB]",
            response_schema=schema_a,  # Primary schema
            is_streaming=False,
            response_ir=operation.responses[0]
        )

        self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock, strategy)

        written_code_union = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])
        written_lines_stripped_union = [c[0][0].strip() for c in self.code_writer_mock.write_line.call_args_list]

        self.assertIn("match response.status_code:", written_code_union)
        self.assertIn("case 200:", written_code_union)
        self.assertIn("try:", written_code_union)
        # With unified service, no manual unwrapping should be generated for union types
        self.assertIn("return ModelA.from_dict(response.json())", written_lines_stripped_union)
        self.assertIn("except Exception:", written_code_union)
        self.assertIn("return ModelB.from_dict(response.json())", written_lines_stripped_union)

        # Ensure no unwrapping code is generated (unified service handles it)
        self.assertNotIn("raw_data = response.json().get('data')", written_lines_stripped_union)
        self.assertNotIn("return_value = ModelA.from_dict(raw_data)", written_lines_stripped_union)
        self.assertNotIn("return return_value", written_lines_stripped_union)

    def test_generate_response_handling_simple_type_with_unwrap(self) -> None:
        """
        Scenario: Op returns 200 OK, type is ModelC. With unified service, unwrapping is handled internally.
        Expected Outcome: BaseSchema deserialization for ModelC is generated (no manual unwrapping).
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

        # Create ResponseStrategy for simple type with unwrap
        strategy = ResponseStrategy(
            return_type="ModelC",
            response_schema=schema_c,
            is_streaming=False,
            response_ir=operation.responses[0]
        )

        self.generator.generate_response_handling(self.code_writer_mock, operation, self.render_context_mock, strategy)

        written_code = "\n".join([call[0][0] for call in self.code_writer_mock.write_line.call_args_list])
        written_lines_stripped = [c[0][0].strip() for c in self.code_writer_mock.write_line.call_args_list]

        self.assertIn("match response.status_code:", written_code)
        self.assertIn("case 200:", written_code)
        # With unified service, no manual unwrapping should be generated
        self.assertIn("return ModelC.from_dict(response.json())", written_lines_stripped)

        # Ensure no unwrapping code is generated (unified service handles it)
        self.assertNotIn("raw_data = response.json().get('data')", written_lines_stripped)
        self.assertNotIn("ModelC.from_dict(raw_data)", written_code)
        self.assertNotIn("return return_value", written_code)


if __name__ == "__main__":
    unittest.main()
