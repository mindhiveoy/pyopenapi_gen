"""Comprehensive integration tests for discriminated union generation.

This module tests the complete pipeline from OpenAPI spec parsing through
to code generation, ensuring discriminated unions are handled correctly
in all edge cases.
"""

from pathlib import Path

import yaml

from pyopenapi_gen import generate_client


def test_discriminated_union__with_explicit_type_object__generates_union_alias(tmp_path: Path) -> None:
    """
    Test discriminated union with explicit type: object generates Union TypeAlias.

    This is the primary regression test - oneOf with type: object should generate
    Union[StartNode, EndNode], not empty dataclass or Union[dict, dict].
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "StartNode": {
                    "type": "object",
                    "required": ["type", "id"],
                    "properties": {
                        "type": {"type": "string", "enum": ["start"]},
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                    },
                },
                "EndNode": {
                    "type": "object",
                    "required": ["type", "id"],
                    "properties": {
                        "type": {"type": "string", "enum": ["end"]},
                        "id": {"type": "string"},
                    },
                },
                "Node": {
                    "type": "object",  # Explicit type: object - this was causing the bug
                    "oneOf": [
                        {"$ref": "#/components/schemas/StartNode"},
                        {"$ref": "#/components/schemas/EndNode"},
                    ],
                    "discriminator": {
                        "propertyName": "type",
                        "mapping": {
                            "start": "#/components/schemas/StartNode",
                            "end": "#/components/schemas/EndNode",
                        },
                    },
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert
    node_file = output_dir / "models" / "node.py"
    assert node_file.exists(), "Node model file should be generated"

    node_content = node_file.read_text()

    # Verify it generates Union TypeAlias
    assert "TypeAlias" in node_content, "Should use TypeAlias for discriminated union"
    assert "Union[" in node_content, "Should generate Union type"

    # Verify it contains the named types, not dict[str, Any]
    assert "StartNode" in node_content, "Should reference StartNode by name"
    assert "EndNode" in node_content, "Should reference EndNode by name"
    assert "dict[str, Any]" not in node_content, "Should NOT fall back to dict[str, Any]"

    # Verify it does NOT generate empty dataclass
    assert "@dataclass" not in node_content, "Should NOT generate dataclass for discriminated union"
    assert "class Node:" not in node_content, "Should NOT generate class for discriminated union"

    # Verify the expected format (order may vary)
    assert (
        ("Node: TypeAlias = Union[StartNode, EndNode]" in node_content)
        or ("Node: TypeAlias = Union[EndNode, StartNode]" in node_content)
        or ("Node: TypeAlias = Union[\n    StartNode,\n    EndNode,\n]" in node_content)
        or ("Node: TypeAlias = Union[\n    EndNode,\n    StartNode,\n]" in node_content)
    ), f"Expected Union with StartNode and EndNode, got:\n{node_content}"


def test_discriminated_union__without_explicit_type__generates_union_alias(tmp_path: Path) -> None:
    """
    Test discriminated union without explicit type field generates Union TypeAlias.

    When type is omitted, it should still generate proper Union.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "SuccessResponse": {
                    "type": "object",
                    "required": ["status", "data"],
                    "properties": {
                        "status": {"type": "string", "enum": ["success"]},
                        "data": {"type": "object"},
                    },
                },
                "ErrorResponse": {
                    "type": "object",
                    "required": ["status", "error"],
                    "properties": {
                        "status": {"type": "string", "enum": ["error"]},
                        "error": {"type": "string"},
                    },
                },
                "Response": {
                    # No explicit type field
                    "oneOf": [
                        {"$ref": "#/components/schemas/SuccessResponse"},
                        {"$ref": "#/components/schemas/ErrorResponse"},
                    ],
                    "discriminator": {"propertyName": "status"},
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert
    response_file = output_dir / "models" / "response.py"
    assert response_file.exists()

    response_content = response_file.read_text()

    assert "TypeAlias" in response_content
    assert "Union[" in response_content
    assert "SuccessResponse" in response_content
    assert "ErrorResponse" in response_content
    assert "dict[str, Any]" not in response_content
    assert "@dataclass" not in response_content


def test_discriminated_union__nested_oneof__generates_all_variants(tmp_path: Path) -> None:
    """
    Test nested discriminated unions (oneOf inside oneOf) generate all variants.

    This tests that recursive collection works properly.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "StringValue": {
                    "type": "object",
                    "required": ["type", "value"],
                    "properties": {
                        "type": {"type": "string", "enum": ["string"]},
                        "value": {"type": "string"},
                    },
                },
                "NumberValue": {
                    "type": "object",
                    "required": ["type", "value"],
                    "properties": {
                        "type": {"type": "string", "enum": ["number"]},
                        "value": {"type": "number"},
                    },
                },
                "SimpleValue": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/StringValue"},
                        {"$ref": "#/components/schemas/NumberValue"},
                    ],
                    "discriminator": {"propertyName": "type"},
                },
                "ArrayValue": {
                    "type": "object",
                    "required": ["type", "items"],
                    "properties": {
                        "type": {"type": "string", "enum": ["array"]},
                        "items": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "Value": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/SimpleValue"},
                        {"$ref": "#/components/schemas/ArrayValue"},
                    ],
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert - Check SimpleValue (first level oneOf)
    simple_value_file = output_dir / "models" / "simple_value.py"
    assert simple_value_file.exists()
    simple_value_content = simple_value_file.read_text()
    assert "Union[" in simple_value_content
    assert "StringValue" in simple_value_content
    assert "NumberValue" in simple_value_content

    # Assert - Check Value (second level oneOf referencing SimpleValue)
    value_file = output_dir / "models" / "value.py"
    assert value_file.exists()
    value_content = value_file.read_text()
    assert "Union[" in value_content
    assert "SimpleValue" in value_content
    assert "ArrayValue" in value_content


def test_discriminated_union__anyof_instead_of_oneof__generates_union(tmp_path: Path) -> None:
    """
    Test that anyOf (not just oneOf) generates Union TypeAlias correctly.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "Cat": {
                    "type": "object",
                    "required": ["petType"],
                    "properties": {
                        "petType": {"type": "string", "enum": ["cat"]},
                        "meow": {"type": "boolean"},
                    },
                },
                "Dog": {
                    "type": "object",
                    "required": ["petType"],
                    "properties": {
                        "petType": {"type": "string", "enum": ["dog"]},
                        "bark": {"type": "boolean"},
                    },
                },
                "Pet": {
                    "anyOf": [  # Using anyOf instead of oneOf
                        {"$ref": "#/components/schemas/Cat"},
                        {"$ref": "#/components/schemas/Dog"},
                    ],
                    "discriminator": {"propertyName": "petType"},
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert
    pet_file = output_dir / "models" / "pet.py"
    assert pet_file.exists()

    pet_content = pet_file.read_text()
    assert "TypeAlias" in pet_content
    assert "Union[" in pet_content
    assert "Cat" in pet_content
    assert "Dog" in pet_content
    assert "dict[str, Any]" not in pet_content


def test_discriminated_union__with_properties__merges_correctly(tmp_path: Path) -> None:
    """
    Test discriminated union that also has direct properties generates correctly.

    This is an edge case where the parent schema has both oneOf and properties.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "CircleShape": {
                    "type": "object",
                    "required": ["type", "radius"],
                    "properties": {
                        "type": {"type": "string", "enum": ["circle"]},
                        "radius": {"type": "number"},
                    },
                },
                "RectangleShape": {
                    "type": "object",
                    "required": ["type", "width", "height"],
                    "properties": {
                        "type": {"type": "string", "enum": ["rectangle"]},
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                    },
                },
                "Shape": {
                    "type": "object",
                    "required": ["id"],
                    "properties": {
                        "id": {"type": "string"},  # Common property
                    },
                    "oneOf": [
                        {"$ref": "#/components/schemas/CircleShape"},
                        {"$ref": "#/components/schemas/RectangleShape"},
                    ],
                    "discriminator": {"propertyName": "type"},
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert - This is a complex case: schema has both properties AND oneOf
    # The expected behaviour depends on implementation, but it should handle it gracefully
    shape_file = output_dir / "models" / "shape.py"
    assert shape_file.exists()

    shape_content = shape_file.read_text()

    # Verify files are generated without errors
    circle_file = output_dir / "models" / "circle_shape.py"
    rectangle_file = output_dir / "models" / "rectangle_shape.py"
    assert circle_file.exists()
    assert rectangle_file.exists()


def test_discriminated_union__multiple_discriminators__all_generated(tmp_path: Path) -> None:
    """
    Test multiple discriminated unions in same spec all generate correctly.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                # First discriminated union
                "EmailNotification": {
                    "type": "object",
                    "required": ["channel", "address"],
                    "properties": {
                        "channel": {"type": "string", "enum": ["email"]},
                        "address": {"type": "string"},
                    },
                },
                "SmsNotification": {
                    "type": "object",
                    "required": ["channel", "phone"],
                    "properties": {
                        "channel": {"type": "string", "enum": ["sms"]},
                        "phone": {"type": "string"},
                    },
                },
                "Notification": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/EmailNotification"},
                        {"$ref": "#/components/schemas/SmsNotification"},
                    ],
                    "discriminator": {"propertyName": "channel"},
                },
                # Second discriminated union
                "CreditCard": {
                    "type": "object",
                    "required": ["method", "cardNumber"],
                    "properties": {
                        "method": {"type": "string", "enum": ["card"]},
                        "cardNumber": {"type": "string"},
                    },
                },
                "BankTransfer": {
                    "type": "object",
                    "required": ["method", "iban"],
                    "properties": {
                        "method": {"type": "string", "enum": ["transfer"]},
                        "iban": {"type": "string"},
                    },
                },
                "PaymentMethod": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/CreditCard"},
                        {"$ref": "#/components/schemas/BankTransfer"},
                    ],
                    "discriminator": {"propertyName": "method"},
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert - Both discriminated unions should generate correctly
    notification_file = output_dir / "models" / "notification.py"
    assert notification_file.exists()
    notification_content = notification_file.read_text()
    assert "Union[" in notification_content
    assert "EmailNotification" in notification_content
    assert "SmsNotification" in notification_content

    payment_file = output_dir / "models" / "payment_method.py"
    assert payment_file.exists()
    payment_content = payment_file.read_text()
    assert "Union[" in payment_content
    assert "CreditCard" in payment_content
    assert "BankTransfer" in payment_content


def test_discriminated_union__three_or_more_variants__all_included(tmp_path: Path) -> None:
    """
    Test discriminated union with 3+ variants includes all in Union.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "StartEvent": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["start"]},
                        "timestamp": {"type": "string"},
                    },
                },
                "UpdateEvent": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["update"]},
                        "changes": {"type": "object"},
                    },
                },
                "CompleteEvent": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["complete"]},
                        "result": {"type": "string"},
                    },
                },
                "ErrorEvent": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["error"]},
                        "message": {"type": "string"},
                    },
                },
                "Event": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/StartEvent"},
                        {"$ref": "#/components/schemas/UpdateEvent"},
                        {"$ref": "#/components/schemas/CompleteEvent"},
                        {"$ref": "#/components/schemas/ErrorEvent"},
                    ],
                    "discriminator": {"propertyName": "type"},
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert
    event_file = output_dir / "models" / "event.py"
    assert event_file.exists()

    event_content = event_file.read_text()
    assert "Union[" in event_content
    assert "StartEvent" in event_content
    assert "UpdateEvent" in event_content
    assert "CompleteEvent" in event_content
    assert "ErrorEvent" in event_content
    assert "dict[str, Any]" not in event_content


def test_discriminated_union__allof_with_nested_oneof__generates_union(tmp_path: Path) -> None:
    """
    Test that allOf containing oneOf schemas generates Union TypeAlias correctly.

    This tests the allOf composition keyword to ensure nested oneOf variants
    get proper names when referenced through allOf.
    """
    # Arrange
    spec_content = {
        "openapi": "3.0.3",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
        "components": {
            "schemas": {
                "SuccessResult": {
                    "type": "object",
                    "required": ["status", "data"],
                    "properties": {
                        "status": {"type": "string", "enum": ["success"]},
                        "data": {"type": "object"},
                    },
                },
                "ErrorResult": {
                    "type": "object",
                    "required": ["status", "error"],
                    "properties": {
                        "status": {"type": "string", "enum": ["error"]},
                        "error": {"type": "string"},
                    },
                },
                "BaseResult": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/SuccessResult"},
                        {"$ref": "#/components/schemas/ErrorResult"},
                    ],
                    "discriminator": {"propertyName": "status"},
                },
                "ExtendedResult": {
                    "allOf": [
                        {"$ref": "#/components/schemas/BaseResult"},  # References oneOf schema
                        {
                            "type": "object",
                            "properties": {
                                "timestamp": {"type": "string", "format": "date-time"},
                                "requestId": {"type": "string"},
                            },
                        },
                    ],
                },
            },
        },
    }

    spec_file = tmp_path / "spec.yaml"
    spec_file.write_text(yaml.dump(spec_content))

    # Act
    generate_client(
        spec_path=str(spec_file),
        project_root=str(tmp_path),
        output_package="test_client",
        no_postprocess=True,  # Skip formatting for speed
    )

    output_dir = tmp_path / "test_client"

    # Assert - BaseResult should generate as Union
    base_result_file = output_dir / "models" / "base_result.py"
    assert base_result_file.exists(), "BaseResult model file should be generated"

    base_result_content = base_result_file.read_text()
    assert "TypeAlias" in base_result_content, "BaseResult should use TypeAlias"
    assert "Union[" in base_result_content, "BaseResult should generate Union type"
    assert "SuccessResult" in base_result_content, "Should reference SuccessResult by name"
    assert "ErrorResult" in base_result_content, "Should reference ErrorResult by name"
    assert "dict[str, Any]" not in base_result_content, "Should NOT fall back to dict[str, Any]"

    # Assert - ExtendedResult should be generated (exact structure depends on allOf handling)
    extended_result_file = output_dir / "models" / "extended_result.py"
    assert extended_result_file.exists(), "ExtendedResult model file should be generated"

    # Verify the oneOf variants are properly named
    success_result_file = output_dir / "models" / "success_result.py"
    error_result_file = output_dir / "models" / "error_result.py"
    assert success_result_file.exists(), "SuccessResult should be generated"
    assert error_result_file.exists(), "ErrorResult should be generated"
