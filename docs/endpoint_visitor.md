# Endpoint Visitor (`visit/endpoint_visitor.py`)

This visitor translates the `IROperation` nodes from the Intermediate Representation into Python methods within the generated client classes. Each method corresponds to a specific API endpoint and HTTP method.

Traverses `IROperation` nodes from the Intermediate Representation.

Responsibilities:
*   Generates Python methods within endpoint client classes for each API operation.
*   Parses `IROperation` details (path, method, parameters, request body, responses) to construct the method signature and body.
*   Determines correct Python type hints for parameters and return values based on `IRSchema` nodes within `IRParameter`, `IRRequestBody`, and `IRResponse`.
*   Handles response unwrapping logic (e.g., returning `Tenant` from a response defined with `TenantResponse` schema) by generating code to access the relevant part of the response payload (like `.data`).
*   Uses `CodeWriter` helper to construct the Python code. 