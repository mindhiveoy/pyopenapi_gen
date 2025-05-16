# Operation ID Handling in PyOpenAPI Generator

## Current Implementation

1. **Initial Processing:**
   - Operation IDs are initially processed in `src/pyopenapi_gen/core/loader.py` in the `_parse_operations` function
   - If an explicit `operationId` is provided in the OpenAPI spec, it's used as-is (line 230-231)
   - If no `operationId` is provided, one is generated using `NameSanitizer.sanitize_method_name(f"{mu}_{path}".strip("/"))` (line 233)

2. **Method Name Generation:**
   - When generating endpoint methods in `src/pyopenapi_gen/visit/endpoint_method_generator.py`, the operation ID is converted to a valid Python method name using `NameSanitizer.sanitize_method_name(op.operation_id)` (line 183)
   - This sanitization ensures valid Python identifiers but doesn't address duplicate names

3. **Method Organization:**
   - Methods are grouped by tags in `src/pyopenapi_gen/emitters/endpoints_emitter.py`
   - The `emit` method in `EndpointsEmitter` organizes operations by tags, creating one module per tag
   - Each tag's operations are processed by the `EndpointVisitor` to generate methods

## Current Limitations

1. **No Explicit Duplicate Handling:**
   - There is no explicit mechanism to detect or handle duplicate operation IDs
   - If two operations have the same operation ID (after sanitization), they would generate methods with the same name within a tag client
   - This would result in Python syntax errors in the generated code

2. **Potential Conflicts:**
   - Operations with different explicit operation IDs might collide after sanitization
   - Operations with auto-generated operation IDs might collide with explicit ones
   - Operations in different tags might have the same operation ID, which is not a problem as they'd be in different classes

## Potential Solutions

1. **Detection and De-duplication:**
   - Add a mechanism in `EndpointsEmitter.emit()` to detect duplicate method names within each tag
   - When a duplicate is found, modify the operation ID by adding a suffix (e.g., `_2`, `_v2`)

2. **Implementation Location:**
   - The best place to add this logic would be in `src/pyopenapi_gen/emitters/endpoints_emitter.py`
   - Before passing operations to `EndpointVisitor`, ensure unique operation IDs within each tag group

3. **Implementation Approach:**
   - Track sanitized method names per tag
   - If a collision is detected, rename by adding a suffix
   - Update the operation's operation_id field before passing to the visitor
   - Log a warning about duplicate operation IDs

## Recommended Code Modifications

The primary modification point would be in `EndpointsEmitter.emit()` before the `methods = [self.visitor.visit(op, context) for op in ops]` line.