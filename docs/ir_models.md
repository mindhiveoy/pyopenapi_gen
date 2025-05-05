# Intermediate Representation (IR) (`__init__.py`)

The Intermediate Representation (IR) is a set of Python dataclasses that provide a structured, validated, and Python-native view of the OpenAPI specification. It serves as the single source of truth for all subsequent code generation steps (Visitors and Emitters), decoupling them from the complexities and variations of the raw OpenAPI spec format.

Defines the core dataclasses (`IRSpec`, `IROperation`, `IRParameter`, `IRRequestBody`, `IRResponse`, `IRSchema`) that represent the normalized and validated OpenAPI specification.

```mermaid
classDiagram
    IRSpec "1" *-- "*" IROperation
    IRSpec "1" *-- "*" IRSchema : Global Schemas
    IROperation "1" *-- "*" IRParameter
    IROperation "1" *-- "1" IRRequestBody
    IROperation "1" *-- "*" IRResponse
    IRRequestBody "1" *-- "*" IRSchema : Request Content Schemas
    IRResponse "1" *-- "*" IRSchema : Response Content Schemas
    IRParameter "1" *-- "1" IRSchema : Parameter Schema
    IRSchema "1" *-- "*" IRSchema : Properties
    IRSchema "1" *-- "1" IRSchema : Items (for arrays)

    class IRSpec{
        +str title
        +str version
        +Optional[str] description
        +Dict[str, IRSchema] schemas
        +List[IROperation] operations
        +List[str] servers
    }
    class IROperation{
        +str operation_id
        +HTTPMethod method
        +str path
        +Optional[str] summary
        +Optional[str] description
        +List[IRParameter] parameters
        +Optional[IRRequestBody] request_body
        +List[IRResponse] responses
        +List[str] tags
    }
    class IRParameter{
        +str name
        +str in_
        +bool required
        +IRSchema schema
        +Optional[str] description
    }
    class IRResponse{
        +str status_code
        +Optional[str] description
        +Dict[str, IRSchema] content
        +bool stream
        +Optional[str] stream_format
    }
    class IRRequestBody{
        +bool required
        +Dict[str, IRSchema] content
        +Optional[str] description
    }
    class IRSchema{
        +Optional[str] name
        +Optional[str] type
        +Optional[str] format
        +List[str] required
        +Dict[str, IRSchema] properties
        +Optional[IRSchema] items
        +Optional[List[Any]] enum
        +Optional[str] description
    }
```
*Diagram: Relationship between core IR dataclasses.* 

Key aspects related to schema references:
*   `IRSchema` holds the parsed details of a schema, including type, format, properties, items (for arrays), enums, etc.
*   Relationships between schemas (e.g., nested objects, arrays of objects) are represented through nested `IRSchema` instances within `properties` or `items`.
*   The loader populates these structures after resolving `$ref`s. 