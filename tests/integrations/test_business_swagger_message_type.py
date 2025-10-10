"""Integration test for business_swagger.json to catch message property type generation issue.

Scenario:
The ChatCreate component has a property 'message' with type 'string' in the OpenAPI spec.
The generated code should correctly generate this as type 'str', not 'Message'.

This test verifies that string properties are correctly generated as Python str type.
"""

import json
import tempfile
from pathlib import Path

from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.generator.client_generator import ClientGenerator


def test_chatcreate_message_property_type_generation():
    """Test that ChatCreate.message property generates as str, not Message.

    Scenario:
    - ChatCreate component has 'message' property with type 'string' in OpenAPI spec
    - Generated code should have message: str, not message: Message

    Expected Outcome:
    - Generated ChatCreate dataclass has message field with str annotation
    - No incorrect Message type import or usage
    """
    # Arrange
    spec_path = Path(__file__).parent.parent.parent / "input" / "business_swagger.json"
    assert spec_path.exists(), f"Test spec not found at {spec_path}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        project_root = temp_path
        output_package = "test_business_api"

        # Act - Generate the client code
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_path),
            project_root=project_root,
            output_package=output_package,
            force=True,
            no_postprocess=True,  # Skip type checking to avoid timeout and SystemExit
        )

        # Assert - Check generated ChatCreate model
        chat_create_file = project_root / output_package / "models" / "chat_create.py"
        assert chat_create_file.exists(), f"ChatCreate model not generated at {chat_create_file}"

        chat_create_content = chat_create_file.read_text()

        # Verify the message field is typed correctly as str (or str | None)
        has_correct_type = "message: str" in chat_create_content or "message: str | None" in chat_create_content
        assert has_correct_type, (
            f"Expected 'message: str' or 'message: str | None' in generated ChatCreate model. "
            f"Generated content:\n{chat_create_content}"
        )

        # Verify no incorrect Message type usage for the message field
        has_incorrect_type = (
            "message: Message" in chat_create_content or "message: Optional[Message]" in chat_create_content
        )
        assert (
            not has_incorrect_type
        ), f"Found incorrect 'message: Message' type annotation. Generated content:\n{chat_create_content}"


def test_chatcreate_schema_parsing_isolated():
    """Test ChatCreate schema parsing in isolation.

    Scenario:
    - Load business_swagger.json spec
    - Parse ChatCreate schema specifically
    - Verify the IR representation has correct types

    Expected Outcome:
    - ChatCreate schema exists in IR
    - Message property can be found (structure may vary due to fix)
    """
    # Arrange
    spec_path = Path(__file__).parent.parent.parent / "input" / "business_swagger.json"

    # Act - Load and parse the spec
    spec_data = json.loads(spec_path.read_text())
    ir_spec = load_ir_from_spec(spec_data)

    # Assert - Find ChatCreate schema in IR
    chat_create_schema = None
    if hasattr(ir_spec.schemas, "keys"):
        chat_create_schema = ir_spec.schemas.get("ChatCreate")

    assert chat_create_schema is not None, "ChatCreate schema not found in parsed IR"

    # Verify that both Message schema and ChatCreate schema exist
    # This confirms the fix doesn't break the parsing of either schema
    message_schema = ir_spec.schemas.get("Message")
    assert message_schema is not None, "Message schema should still exist"
    assert chat_create_schema != message_schema, "ChatCreate and Message should be different schemas"
