# OpenAPI Client Generator Issue: Incorrect Return Type Generation

## Problem Summary

The `pyopenapi-gen` package is generating incorrect return types for API endpoints. Specifically, the `add_messages` method is returning `Data_` (which resolves to `List[User2]`) instead of the correct `MessageBatchResponse` type containing `List[Message]`.

## Environment

- **Generator Package**: `pyopenapi-gen` version 0.7.2
- **Generator Location**: `/Users/villevenalainen/development/pyopenapi_gen/`
- **Client Package**: `pyapis` (uses pyopenapi-gen to generate Python clients)
- **Affected API**: Business API (`business_swagger.json`)
- **Affected Endpoint**: `POST /tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/batch` (operationId: `addMessages`)

## Current Behavior (Incorrect)

The generated Python method:
```python
async def add_messages(
    self,
    tenant_id: str,
    agent_id: str,
    chat_id: str,
    body: AddMessagesRequest,
    x_mainio_internal_token: Optional[str] = None,
) -> Data_:  # ❌ WRONG: Should be MessageBatchResponse
```

Where `Data_` is generated as:
```python
Data_: TypeAlias = List[User2]  # ❌ WRONG: Should be List[Message]
```

## Expected Behavior (Correct)

The method should return:
```python
async def add_messages(...) -> MessageBatchResponse:
```

Where `MessageBatchResponse` should be:
```python
@dataclass
class MessageBatchResponse:
    data: Optional[List[Message]] = None  # ✅ CORRECT
```

## OpenAPI Schema (Correct After Fix)

The OpenAPI schema has been corrected and now properly defines:

### Schema Definition
```json
{
  "MessageBatchResponse": {
    "type": "object",
    "description": "Response wrapper for a batch of messages",
    "properties": {
      "data": {
        "type": "array",
        "items": {
          "$ref": "#/components/schemas/Message"
        }
      }
    }
  }
}
```

### Endpoint Response
```json
{
  "responses": {
    "200": {
      "description": "Batch of messages added successfully",
      "content": {
        "application/json": {
          "schema": {
            "$ref": "#/components/schemas/MessageBatchResponse"
          }
        }
      }
    }
  }
}
```

## Root Cause Analysis

1. **Schema Resolution Issue**: The generator appears to be incorrectly resolving schema references
2. **Type Alias Conflict**: The generator is creating a `Data_` type alias that maps to the wrong type
3. **Circular Reference Handling**: There may be issues with how the generator handles schema relationships

## Files Involved

### Generator Package (`pyopenapi_gen`)
- `src/pyopenapi_gen/helpers/endpoint_utils.py` - Contains `get_return_type()` function
- `src/pyopenapi_gen/helpers/type_helper.py` - Contains type resolution logic
- `src/pyopenapi_gen/core/parsing/schema_parser.py` - Schema parsing logic
- `src/pyopenapi_gen/core/parsing/common/ref_resolution/resolve_schema_ref.py` - Reference resolution

### Generated Client (Evidence of Issue)
- Generated file: `src/pyapis/business/endpoints/messages.py` (method signature)
- Generated file: `src/pyapis/business/models/data_.py` (incorrect type alias)
- Generated file: `src/pyapis/business/models/message_batch_response.py` (should contain correct structure)

## Reproduction Steps

1. **Setup**: Use the corrected OpenAPI schema file `/Users/villevenalainen/development/mainio.app/packages/pyapis/api_specs/business_swagger.json`

2. **Generate Client**:
   ```bash
   cd /Users/villevenalainen/development/mainio.app/packages/pyapis
   poetry run generate-client business
   ```

3. **Verify Issue**: Check the generated files:
   ```bash
   # Should show incorrect return type
   grep -A 5 "def add_messages" src/pyapis/business/endpoints/messages.py
   
   # Should show incorrect type alias
   cat src/pyapis/business/models/data_.py
   
   # Should show incorrect data field type
   cat src/pyapis/business/models/message_batch_response.py
   ```

4. **Run Test**: The failing test demonstrates the issue:
   ```bash
   poetry run pytest tests/test_add_messages_return_type.py -v
   ```

## Test Case

A test file has been created to verify the issue:

```python
# tests/test_add_messages_return_type.py
def test_add_messages_return_type_annotation(self):
    """Test that add_messages has the correct return type annotation."""
    method = getattr(MessagesClient, 'add_messages')
    type_hints = get_type_hints(method)
    return_annotation = type_hints.get('return')
    
    # This should PASS when fixed
    assert return_annotation == MessageBatchResponse, (
        f"Expected add_messages to return MessageBatchResponse, "
        f"but got {return_annotation}"
    )
```

## Expected Fix Areas

The issue likely lies in one or more of these areas in `pyopenapi-gen`:

1. **Schema Reference Resolution**: The `resolve_schema_ref.py` may be incorrectly resolving `#/components/schemas/MessageBatchResponse`

2. **Return Type Determination**: The `get_return_type()` function in `endpoint_utils.py` may have logic issues when handling response schema unwrapping

3. **Type Alias Generation**: The generator may be creating incorrect type aliases when multiple schemas have "data" properties

4. **Response Parsing**: The response parser may not be correctly handling the schema structure

## Debugging Commands

To debug the schema parsing in `pyopenapi-gen`:

```python
# Load and examine the schema structure
import json
with open('/Users/villevenalainen/development/mainio.app/packages/pyapis/api_specs/business_swagger.json') as f:
    spec = json.load(f)

# Check MessageBatchResponse schema
print(json.dumps(spec['components']['schemas']['MessageBatchResponse'], indent=2))

# Check addMessages endpoint
endpoint = spec['paths']['/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/batch']['post']
print(json.dumps(endpoint['responses']['200'], indent=2))
```

## Success Criteria

The fix is successful when:

1. ✅ `add_messages` method returns `MessageBatchResponse` instead of `Data_`
2. ✅ `MessageBatchResponse` has a `data: Optional[List[Message]]` field instead of `data_: Optional[Data_]`
3. ✅ `Data_` type alias (if still generated) does not conflict with message types
4. ✅ All tests in `test_add_messages_return_type.py` pass
5. ✅ The generated client correctly represents the OpenAPI schema structure

## Additional Context

This issue was discovered while working on the `pyapis` package which generates Python API clients from OpenAPI specifications. The OpenAPI schema has been corrected (circular reference removed), but the underlying `pyopenapi-gen` generator is still producing incorrect types, suggesting a bug in the generator's schema resolution or type mapping logic.