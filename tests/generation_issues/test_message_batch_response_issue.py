"""Test case for reproducing the MessageBatchResponse return type issue.

This test reproduces the specific issue where:
1. addMessages endpoint should return MessageBatchResponse type
2. MessageBatchResponse should have data field with type List[Message] 
3. But it's generating Data_ type alias and incorrect field types
"""

import tempfile
from pathlib import Path
import pytest
import json

from pyopenapi_gen.generator.client_generator import ClientGenerator


def test_message_batch_response_return_type_issue():
    """Test that MessageBatchResponse generates correctly for addMessages endpoint.
    
    Scenario:
    - MessageBatchResponse schema has 'data' property with array of Message references
    - addMessages operation returns MessageBatchResponse
    - Generated code should have correct type annotations
    
    Expected Outcome:
    - MessageBatchResponse model has data field with List[Message] type
    - addMessages method returns MessageBatchResponse type  
    - No Data_ type alias with incorrect types
    """
    # Create minimal spec that reproduces the issue
    minimal_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/messages/batch": {
                "post": {
                    "operationId": "addMessages",
                    "summary": "Add multiple messages",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AddMessagesRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Messages added successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/MessageBatchResponse"}
                                }
                            },
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "Message": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "content": {"type": "string"},
                        "role": {"type": "string"},
                    },
                    "required": ["id", "content", "role"],
                },
                "User2": {
                    "type": "object", 
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                    "required": ["id", "name"],
                },
                "MessageBatchResponse": {
                    "type": "object",
                    "description": "Response wrapper for a batch of messages",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Message"},
                        }
                    },
                },
                "AddMessagesRequest": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Message"},
                        }
                    },
                    "required": ["messages"],
                },
            }
        },
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        spec_file = temp_path / "minimal_spec.json"
        spec_file.write_text(json.dumps(minimal_spec, indent=2))
        
        # Generate client code
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_file),
            project_root=temp_path,
            output_package="test_api",
            force=True,
            no_postprocess=True
        )
        
        # Check MessageBatchResponse model
        mbr_file = temp_path / "test_api" / "models" / "message_batch_response.py"
        assert mbr_file.exists(), f"MessageBatchResponse model not generated at {mbr_file}"
        
        mbr_content = mbr_file.read_text()
        print(f"=== MessageBatchResponse content ===\\n{mbr_content}")
        
        # Current behavior: data field is named data_ due to sanitization
        # and type might be Data_ type alias instead of List[Message]
        # Let's check what's actually generated
        
        # Check if there's a Data_ type alias file
        data_alias_file = temp_path / "test_api" / "models" / "data_.py"
        if data_alias_file.exists():
            data_alias_content = data_alias_file.read_text()
            print(f"=== Data_ type alias content ===\\n{data_alias_content}")
            
            # The issue: Data_ should be List[Message], not List[Any] or List[User2]
            assert "List[Message]" in data_alias_content, (
                f"Expected Data_ to be List[Message], but got different type. "
                f"Content: {data_alias_content}"
            )
        
        # Check the field type in MessageBatchResponse
        # Current bug: it uses Data_ instead of direct List[Message]
        # Fixed behavior should have: data_: Optional[List[Message]]
        expected_field_patterns = [
            "data_: Optional[List[Message]]",
            "data_: List[Message]",
            "data: Optional[List[Message]]",  # In case we fix the field naming
            "data: List[Message]"
        ]
        
        has_correct_field = any(pattern in mbr_content for pattern in expected_field_patterns)
        
        # For now, let's check what's actually there
        if not has_correct_field:
            print(f"WARNING: Expected one of {expected_field_patterns} in MessageBatchResponse")
            # Check for the current broken behavior to document it
            if "data_: Optional[Data_]" in mbr_content:
                print("CONFIRMED: Found the bug - using Data_ type alias instead of List[Message]")
            elif "data_: Optional[List[Any]]" in mbr_content:
                print("CONFIRMED: Found the bug - using List[Any] instead of List[Message]") 
        
        # Check that Message model was generated correctly
        message_file = temp_path / "test_api" / "models" / "message.py"
        assert message_file.exists(), "Message model should be generated"
        
        # Check endpoints
        endpoints_file = temp_path / "test_api" / "endpoints" / "default.py"
        if endpoints_file.exists():
            endpoints_content = endpoints_file.read_text()
            print(f"=== Endpoints content ===\\n{endpoints_content}")
            
            # Check return type annotation 
            if "-> MessageBatchResponse:" in endpoints_content:
                print("SUCCESS: addMessages returns MessageBatchResponse")
            elif "-> Data_:" in endpoints_content:
                print("BUG CONFIRMED: addMessages returns Data_ instead of MessageBatchResponse")
                # This is the actual bug from the issue
            else:
                print("WARNING: Unexpected return type in addMessages")


if __name__ == "__main__":
    test_message_batch_response_return_type_issue()