# PyOpenAPI Generator Test Map

This document provides a comprehensive map of tests in the pyopenapi_gen project to help developers navigate the test landscape, avoid duplication, and understand test coverage.

## Test Structure Overview

Tests are organized by component/functionality, following a similar structure to the main codebase:

```
tests/
├── auth/               # Authentication-related tests 
├── cli/                # Command-line interface tests
├── context/            # Context and state management tests
├── core/               # Core functionality tests
│   ├── parsing/        # Schema and specification parsing tests
│   │   ├── common/     # Common parsing utilities
│   │   │   └── ref_resolution/  # Reference resolution tests
│   │   │       └── helpers/  # Test helpers for ref resolution
│   │   └── keywords/  # OpenAPI keyword-specific parsing
│   └── writers/       # Code and documentation writer tests
├── emitters/           # Code emitter tests
├── generation/         # End-to-end generation tests
├── helpers/            # Utility and helper function tests
├── integrations/       # Integration and end-to-end tests
└── visit/              # Visitor pattern implementation tests
    ├── endpoint/       # Endpoint visitor tests
    │   ├── generators/ # Endpoint code generation tests
    │   └── processors/ # Endpoint processing tests
    └── model/          # Model visitor tests
```

## Test Categories

### Authentication Tests
- **auth/test_auth_base.py**: Tests for the base authentication protocol
- **auth/test_auth_plugins.py**: Tests for authentication plugin implementations (Bearer, API keys, etc.)

### CLI Tests
- **cli/test_cli_backup_diff.py**: Tests for backup and diffing functionality in CLI
- **cli/test_cli_edge_cases.py**: Edge case handling in CLI
- **cli/test_cli_internal_utils.py**: Internal CLI utility functions
- **cli/test_http_pagination_cli.py**: CLI pagination functionality

### Context Tests
- **context/test_file_manager.py**: Tests for file management functionality (17 tests)
- **context/test_import_collector.py**: Tests for import collection and management (17 tests)
- **context/test_render_context_imports.py**: Tests for rendering context import handling
- **context/test_render_context_relative_paths.py**: Tests for relative path resolution in rendering

### Core Tests
Core functionality tests are the most numerous, covering parsing, loading, and processing of OpenAPI specifications.

#### Core IR Tests
- **core/test_ir.py**: Tests for the Intermediate Representation (IR) models
- **core/test_ir_schema.py**: Tests for IR schema functionality

#### Core Loader Tests
- **core/test_loader.py**: Basic loader functionality
- **core/test_loader_extensive.py**: Comprehensive loader tests
- **core/test_loader_invalid_refs.py**: Tests for handling invalid references
- **core/test_loader_malformed.py**: Tests for handling malformed specifications
- **core/test_loader_media_types.py**: Tests for handling different media types

#### Core Parsing Tests
- **core/parsing/test_schema_parser.py**: Tests for schema parsing (20 tests)
- **core/parsing/test_context.py**: Tests for parsing context
- **core/parsing/test_cycle_detection.py**: Tests for cycle detection in schemas
- **core/parsing/test_cycle_helpers.py**: Tests for cycle helper utilities
- **core/parsing/test_improved_schema_naming.py**: Tests for schema naming improvements
- **core/parsing/test_inline_enum_extractor.py**: Tests for enum extraction from schemas (14 tests)
- **core/parsing/test_inline_object_promoter.py**: Tests for inline object promotion
- **core/parsing/test_logging.py**: Tests for logging during parsing
- **core/parsing/test_ref_resolver.py**: Tests for reference resolution
- **core/parsing/test_schema_finalizer.py**: Tests for schema finalization
- **core/parsing/test_type_parser.py**: Tests for type parsing

#### Core Writers Tests
- **core/writers/test_code_writer.py**: Tests for Python code generation
- **core/writers/test_documentation_writer.py**: Tests for documentation generation (14 tests)
- **core/writers/test_line_writer.py**: Tests for line-by-line code writing (22 tests)

#### Other Core Tests
- **core/test_detect_circular_imports.py**: Tests for circular import detection
- **core/test_exceptions_module.py**: Tests for exception handling
- **core/test_forward_references.py**: Tests for handling forward references
- **core/test_http_transport.py**: Tests for HTTP transport layer
- **core/test_import_resolution.py**: Tests for import resolution
- **core/test_pagination.py**: Tests for pagination functionality
- **core/test_parsing_context.py**: Tests for parsing context
- **core/test_protocol_defaults.py**: Tests for protocol default implementations
- **core/test_streaming_helpers.py**: Tests for streaming helpers
- **core/test_telemetry.py**: Tests for telemetry functionality
- **core/test_telemetry_client.py**: Tests for telemetry client
- **core/test_utils.py**: Tests for core utilities (16 tests)
- **core/test_warning_collector.py**: Tests for warning collection

### Emitters Tests
- **emitters/test_client_emitter.py**: Tests for client code generation
- **emitters/test_docs_emitter.py**: Tests for documentation generation
- **emitters/test_duplicate_operations.py**: Tests for handling duplicate operations
- **emitters/test_endpoints_emitter.py**: Tests for endpoint code generation
- **emitters/test_exceptions_emitter.py**: Tests for exception class generation
- **emitters/test_models_emitter.py**: Tests for model class generation (19 tests)

### Generation Tests
- **generation/test_external_core_package.py**: Tests for generating with external core package
- **generation/test_response_unwrapping.py**: Tests for response unwrapping functionality

### Helpers Tests
- **helpers/test_endpoint_utils.py**: Tests for endpoint utility functions (15 tests)
- **helpers/test_get_endpoint_return_types.py**: Tests for GET endpoint return type handling
- **helpers/test_named_type_resolver.py**: Tests for named type resolution
- **helpers/test_put_endpoint_return_types.py**: Tests for PUT endpoint return type handling
- **helpers/test_type_cleaner.py**: Tests for type cleaning utilities
- **helpers/test_type_helper.py**: Tests for type helper functions (20 tests)
- **helpers/test_url_utils.py**: Tests for URL utility functions
- **helpers/test_utils_helpers.py**: Tests for general utility helpers

### Integration Tests
- **integrations/test_end_to_end_business_swagger.py**: End-to-end tests with business swagger
- **integrations/test_end_to_end_petstore.py**: End-to-end tests with petstore swagger

### Visitor Tests
Tests for the visitor pattern implementation, used for traversing the IR and generating code.

#### Model Visitor Tests
- **visit/model/test_alias_generator.py**: Tests for type alias generation
- **visit/model/test_dataclass_generator.py**: Tests for dataclass generation
- **visit/model/test_enum_generator.py**: Tests for enum generation
- **visit/test_model_visitor.py**: Tests for the model visitor

#### Endpoint Visitor Tests
- **visit/endpoint/test_endpoint_visitor.py**: Tests for the endpoint visitor
- **visit/endpoint/generators/test_docstring_generator.py**: Tests for docstring generation
- **visit/endpoint/generators/test_endpoint_method_generator.py**: Tests for endpoint method generation
- **visit/endpoint/generators/test_request_generator.py**: Tests for request code generation
- **visit/endpoint/generators/test_response_handler_generator.py**: Tests for response handler generation (18 tests)
- **visit/endpoint/generators/test_signature_generator.py**: Tests for method signature generation
- **visit/endpoint/generators/test_url_args_generator.py**: Tests for URL argument handling
- **visit/endpoint/processors/test_import_analyzer.py**: Tests for import analysis
- **visit/endpoint/processors/test_parameter_processor.py**: Tests for parameter processing

#### Other Visitor Tests
- **visit/test_client_visitor.py**: Tests for the client visitor

## Test Overlap Analysis

### Potential Duplications
1. **Schema Parser Tests**: Both `tests/core/parsing/test_schema_parser.py` and `tests/core/test_schema_parser.py` exist
2. **Type Helper Tests**: Overlap between `tests/helpers/test_type_helper.py` and other type-related tests

### Test Coverage by Component

| Component | # of Test Files | Approx. # of Tests | Coverage Focus |
|-----------|----------------|---------------------|----------------|
| Core      | 46             | ~400                | Parsing, IR, Loading |
| Visit     | 14             | ~120                | Code Generation |
| Helpers   | 8              | ~70                 | Utilities |
| Context   | 4              | ~40                 | State Management |
| Emitters  | 6              | ~60                 | File Generation |
| Auth      | 2              | ~20                 | Authentication |
| CLI       | 4              | ~40                 | Command Line |
| Generation| 2              | ~20                 | End-to-End |
| Integration | 2            | ~20                 | End-to-End |

## Recommended Testing Approach

When adding new features or fixing bugs:

1. **Identify the Component**: Determine which component your change affects
2. **Check Existing Tests**: Review tests in the corresponding category to avoid duplication
3. **Unit Test First**: Write unit tests for the specific functionality
4. **Integration Test If Needed**: For cross-component changes, add integration tests
5. **Consider Edge Cases**: Add tests for error handling and boundary conditions

## Known Test Gaps

- **Circular Dependencies**: More comprehensive tests needed for complex circular references
- **Performance Testing**: Limited tests for performance optimization
- **Error Recovery**: More tests needed for graceful error recovery scenarios

## Running Tests

### Quick Commands
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run tests, stop on first failure (fast debugging)
make test-fast

# Run specific test file
pytest tests/core/test_loader.py

# Run specific test function
pytest tests/core/test_loader.py::test_load_ir_from_spec__minimal_openapi_spec__creates_ir_with_basic_components
```

### Quality Assurance
```bash
# Before committing - auto-fix and check everything
make quality-fix && make quality

# Individual quality checks
make format-check         # Code formatting
make lint                 # Linting
make typecheck            # Type checking
make security             # Security scanning
```

## Test Configuration

The project uses pytest with the following main configuration options:
- Test discovery in the `tests/` directory
- Test files must match `test_*.py`
- Test functions must be prefixed with `test_`
- Coverage target: ≥90% branch coverage
- Strict type checking with mypy

See `pyproject.toml` and `Makefile` for complete configuration details. 