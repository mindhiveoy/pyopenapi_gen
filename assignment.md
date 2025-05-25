# Assignment: Fix Self-Referencing Type Annotations in PyAPIs Code Generator

## Background

The PyAPIs code generator is creating Python dataclass models from OpenAPI/Swagger specifications. When a schema contains self-referencing fields (recursive structures), the generated Python code fails with a `NameError` because Python cannot reference a class that is still being defined.

## Problem Description

When generating Python dataclasses from OpenAPI schemas that contain self-references, the generator produces invalid Python code that cannot be imported.

### Example of Current (Broken) Output

**Input Schema (OpenAPI/Swagger):**
```yaml
components:
  schemas:
    Message:
      type: object
      properties:
        id:
          type: string
          description: Unique event identifier
        chat_id:
          type: string
        message:
          $ref: '#/components/schemas/Message'  # Self-reference
          description: "[Self-referencing schema: Message]"
        role:
          $ref: '#/components/schemas/Role'
        tokens:
          $ref: '#/components/schemas/MessageTokens'
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
```

**Current Generated Code (BROKEN):**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .message_tokens import MessageTokens
from .role import Role

__all__ = ["Message4"]


@dataclass
class Message4:
    """
    Message4 dataclass.

    Args:
        chat_id (str)            :
        created_at (datetime)    : Timestamp when this revision was created
        id_ (str)                : Unique event identifier
        message (Message4)       : [Self-referencing schema: Message]
        role (Role)              : User's role
        tokens (MessageTokens)   :
        updated_at (datetime)    :
        user_id (Optional[str])  : The ID of the user whose password is being changed
    """

    chat_id: str
    created_at: datetime  # Timestamp when this revision was created
    id_: str  # Unique event identifier
    message: Message4  # [Self-referencing schema: Message]  ❌ ERROR: NameError: name 'Message4' is not defined
    role: Role  # User's role
    tokens: MessageTokens
    updated_at: datetime
    user_id: Optional[str]  # The ID of the user whose password is being changed
```

## Expected Outcome

The generator should detect self-referencing types and use Python forward references (string annotations) for those fields.

**Expected Generated Code (FIXED):**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .message_tokens import MessageTokens
from .role import Role

__all__ = ["Message4"]


@dataclass
class Message4:
    """
    Message4 dataclass.

    Args:
        chat_id (str)            :
        created_at (datetime)    : Timestamp when this revision was created
        id_ (str)                : Unique event identifier
        message (Message4)       : [Self-referencing schema: Message]
        role (Role)              : User's role
        tokens (MessageTokens)   :
        updated_at (datetime)    :
        user_id (Optional[str])  : The ID of the user whose password is being changed
    """

    chat_id: str
    created_at: datetime  # Timestamp when this revision was created
    id_: str  # Unique event identifier
    message: "Message4"  # [Self-referencing schema: Message]  ✅ FIXED: Using forward reference
    role: Role  # User's role
    tokens: MessageTokens
    updated_at: datetime
    user_id: Optional[str]  # The ID of the user whose password is being changed
```

## Technical Requirements

1. **Detection Logic**: The generator must detect when a field's type references the class being defined
2. **Forward Reference**: When a self-reference is detected, wrap the type name in quotes
3. **Preserve Other Types**: Non-self-referencing types should remain unchanged
4. **Handle Complex Types**: Should also work with Optional, List, Dict, etc. containing self-references

### Additional Test Cases

**Case 1: Optional Self-Reference**
```python
# Input
parent: Optional[TreeNode]  # Should detect TreeNode inside Optional

# Expected Output
parent: Optional["TreeNode"]
```

**Case 2: List of Self-References**
```python
# Input
children: List[TreeNode]  # Should detect TreeNode inside List

# Expected Output
children: List["TreeNode"]
```

**Case 3: Nested Generic Types**
```python
# Input
related: Dict[str, List[TreeNode]]  # Should detect TreeNode inside nested generics

# Expected Output
related: Dict[str, List["TreeNode"]]
```

## Success Criteria

1. All generated Python files with self-referencing types can be imported without `NameError`
2. Type checking tools (mypy, pyright) correctly understand the types
3. No changes to non-self-referencing type annotations
4. Generated code maintains the same runtime behavior

## Implementation Hints

- Look for where the generator creates type annotations for dataclass fields
- Check if the field type name matches the class name being generated
- Consider using regex or AST manipulation to handle complex generic types
- The fix should be applied during code generation, not as a post-processing step

## Testing

Create unit tests that:
1. Generate code from schemas with self-references
2. Attempt to import the generated modules
3. Verify the imports succeed without errors
4. Check that the type annotations are correctly formatted with quotes
