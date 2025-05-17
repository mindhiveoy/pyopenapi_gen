# PyOpenAPI-Gen Project Structure

This document outlines the folder and file structure of the `pyopenapi-gen` Python OpenAPI client generator. Its purpose is to provide a clear map of the codebase for developers and to help maintain a clean and organized structure.

## Root Level (`pyopenapi_gen/`)

*   `cli.py`: Command-line interface for the generator. Handles argument parsing and orchestrates the generation process.
*   `generator/`: Contains the main `Generator` class responsible for the end-to-end client generation workflow.
    *   `generator.py`: (Assumed) Defines the main `Generator` class.
*   `ir.py`: Defines the Intermediate Representation (IR) dataclasses (`IRSpec`, `IROperation`, `IRParameter`, `IRSchema`, etc.) that model the normalized OpenAPI specification. All code generation is based on this IR.
*   `http_types.py`: Defines core HTTP-related types or enums used across the generator and potentially in the generated client's core.
*   `py.typed`: Marker file for PEP 561 compliance, indicating that the package provides type information.
*   `__init__.py`: Main package initializer. May expose key classes or functions for programmatic use.
*   `core_package_template/`: (Assumed based on name) Template files for the `core` module that gets generated into the client package. This would include base transport, auth protocols, exceptions, etc.

## `src/pyopenapi_gen/core/`

This directory seems to contain fundamental components used by the generator itself and also parts that might be templated into the generated client's `core` module.

*   `loader.py`: Responsible for loading and parsing the OpenAPI specification file into a raw dictionary format, potentially performing initial validation.
*   `utils.py`: General utility functions used across the generator codebase. (e.g., `NameSanitizer`, `Formatter` were mentioned in architecture).
*   `writers/`: Utilities for code construction and writing.
    *   `code_writer.py`: Helper for building Python code strings with correct indentation and formatting.
    *   `python_construct_renderer.py`: Renders specific Python constructs like dataclasses, enums, and functions using `CodeWriter`.
    *   `documentation_writer.py`: Helper for generating Markdown documentation.
    *   `line_writer.py`: (Purpose to be clarified, potentially a more granular writer than `CodeWriter`).
*   `auth/`: (Assumed based on architecture) Contains `BaseAuth` protocol and implementations for various authentication schemes (Bearer, API key, etc.). These are likely part of the `core_package_template`.
*   `parsing/`: Modules related to parsing parts of the OpenAPI spec and transforming them into the IR or intermediate structures.
    *   `context.py`: Manages shared state during schema parsing, including visited references, schema dictionaries, and cycle detection.
    *   `schema_parser.py`: Main orchestrator for parsing OpenAPI schema objects into `IRSchema` instances.
    *   `schema_finalizer.py`: Handles final processing and validation of parsed schemas.
    *   `common/`: Shared utilities and base functionality for schema parsing.
        *   `type_parser.py`: Parses basic type information and nullability from schema definitions.
        *   `ref_resolution/`: Components for handling schema references.
            *   `resolve_schema_ref.py`: Core logic for resolving `$ref` JSON pointers.
            *   `helpers/`: Supporting utilities for reference resolution.
    *   `keywords/`: Specialized parsers for OpenAPI schema keywords.
        *   `all_of_parser.py`: Handles merging of schemas under `allOf` directives.
        *   `any_of_parser.py`: Processes `anyOf` composition keywords.
        *   `one_of_parser.py`: Processes `oneOf` composition keywords.
        *   `array_items_parser.py`: Parses array type definitions and their items.
        *   `properties_parser.py`: Handles object property iteration and parsing.
    *   `transformers/`: Components that transform or enhance parsed schemas.
        *   `inline_enum_extractor.py`: Extracts inline enums and prepares them for IR representation.
        *   `inline_object_promoter.py`: Promotes inline object schemas to named schemas.
*   `streaming_helpers.py`: Utility functions for handling streaming responses in the generated client. Likely part of `core_package_template`.
*   `http_transport.py`: Defines the `HttpTransport` protocol and a default implementation (e.g., `HttpxTransport`). Part of `core_package_template`.
*   `schemas.py`: (Purpose to be clarified, distinct from `ir.py`. May contain Pydantic models for spec validation or specific internal schema representations before IR).
*   `telemetry.py`: (Purpose to be clarified, potentially for collecting usage data or generator metrics - should not be in generated client).
*   `warning_collector.py`: Collects and manages warnings encountered during the generation process.
*   `pagination.py`: Helpers for handling paginated API endpoints in the generated client. Likely part of `core_package_template`.
*   `postprocess_manager.py`: Manages post-processing steps after initial code generation (e.g., formatting, linting).
*   `exceptions.py`: Defines base exception classes for the generated client (e.g., `ApiError`). Part of `core_package_template`.

## `src/pyopenapi_gen/helpers/`

Utility modules that assist various stages of the generation process, often operating on the IR.

*   `type_helper.py`: Determines Python type hints for `IRSchema` definitions, managing necessary imports via `RenderContext`.
*   `type_cleaner.py`: Cleans and normalizes complex type hint strings (e.g., `Optional[List[Union[None, str]]]` -> `Optional[List[str]]`).
*   `endpoint_utils.py`: Helper functions specifically for processing `IROperation` and `IRParameter` to prepare for endpoint code generation.
*   `url_utils.py`: Utilities for constructing and manipulating URLs for API requests.

## `src/pyopenapi_gen/emitters/`

Orchestrate the code generation process for major output categories. They use corresponding Visitors to generate code and then write files to disk.

*   `client_emitter.py`: Generates the main `APIClient` class.
*   `core_emitter.py`: Responsible for emitting the shared `core` package/module into the generated client.
*   `docs_emitter.py`: Generates Markdown documentation.
*   `endpoints_emitter.py`: Generates Python files for API endpoint groups/tags.
*   `exceptions_emitter.py`: Generates the exceptions module for the client.
*   `models_emitter.py`: Generates Python files for data models (dataclasses, enums).

## `src/pyopenapi_gen/visit/`

Implements the Visitor pattern to traverse IR nodes and generate code.

*   `visitor.py`: Base `Visitor` class.
*   `client_visitor.py`: Renders the main `APIClient` class.
*   `docs_visitor.py`: Renders Markdown documentation from the IR.
*   `endpoint_method_generator.py`: (More specific than a simple visitor) Generates the body of individual endpoint methods, including request/response handling, parameter processing, and calls to the HTTP transport.
*   `endpoint_visitor.py`: Renders Python classes for endpoint groups (tags) and their methods, utilizing `EndpointMethodGenerator`.
*   `exception_visitor.py`: Renders exception alias classes for HTTP error codes.
*   `model_visitor.py`: Renders Python dataclasses or enums from `IRSchema` nodes.

## `src/pyopenapi_gen/context/`

Manages shared state and context during the code generation process.

*   `render_context.py`: Central context object tracking imports, current file paths, package structure, and providing helper methods for path resolution and import management (`ImportCollector`, `FileManager`).
*   `import_collector.py`: Collects, organizes, and formats Python import statements for a given file.
*   `file_manager.py`: Handles file system operations like writing generated files.

---

This structure will be used as a reference to ensure new components are placed logically and that existing components' responsibilities remain clear. 