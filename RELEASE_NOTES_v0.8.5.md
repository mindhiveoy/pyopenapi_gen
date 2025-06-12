# Release Notes - PyOpenAPI Generator v0.8.5

## 🚀 Major Features

### JSON-to-Dataclass Automatic Conversion 
- **Automatic field mapping**: Generated dataclasses now include `from_dict()` methods for seamless JSON deserialization
- **BaseSchema integration**: All models inherit from BaseSchema with built-in serialization/deserialization
- **DataclassWizard integration**: Leverages dataclass-wizard for robust JSON handling
- **Field name sanitization**: Automatic handling of Python reserved keywords and builtins

### Unified Response Strategy Architecture
- **ResponseStrategy pattern**: Replaced scattered response handling with unified, testable strategy pattern
- **Enhanced type resolution**: Improved response type inference and error handling
- **Streamlined testing**: All response handling now uses consistent, mockable patterns
- **Better maintainability**: Centralized response logic reduces technical debt

## 🔧 Technical Improvements

### Code Quality & Architecture
- **Complete removal of legacy code**: Eliminated deprecated `get_return_type_unified` function
- **Test modernization**: Migrated from unittest to pytest patterns across 29+ test files
- **Enhanced type safety**: Improved MyPy compliance and type annotations
- **CLI compatibility**: Fixed Typer/Click version compatibility issues

### Development Experience
- **Python 3.12 support**: Updated target version to Python 3.12+ only
- **Improved CI/CD**: Enhanced GitHub Actions workflows with better error handling
- **Quality assurance**: Comprehensive test coverage (85%+ required)
- **Developer tools**: Updated dependencies and dev tooling

## 🐛 Bug Fixes

### Critical Fixes
- **Circular import resolution**: Enhanced cycle detection for complex schemas
- **Response unwrapping**: Fixed edge cases in response data extraction
- **Type annotation errors**: Resolved MyPy false positives
- **CLI argument parsing**: Fixed edge cases in command-line interface

### Stability Improvements
- **Memory optimization**: Reduced memory usage in large schema processing
- **Error handling**: More graceful degradation on malformed specifications
- **Test reliability**: Eliminated flaky tests and improved CI stability

## 📦 Dependencies

### New Dependencies
- `dataclass-wizard>=0.22.0`: For automatic JSON-to-dataclass conversion
- `click>=8.0.0,<8.2.0`: Pinned for CLI stability

### Updated Dependencies
- `typer>=0.12.0,<0.14.0`: Version compatibility fix
- `bandit>=1.7.0`: Security scanning improvements
- `pytest-timeout>=2.1.0`: Test timeout handling

## 🔄 Migration Guide

### For Existing Users
Generated clients now include enhanced serialization capabilities. No breaking changes to existing APIs.

### For Contributors
- **Python 3.12+ required**: Update development environment
- **New test patterns**: Use pytest fixtures instead of unittest.TestCase
- **Enhanced quality checks**: All PRs now require 85% test coverage

## 🎯 Compatibility

- **Python**: 3.12+ (3.10, 3.11 support removed)
- **Platforms**: Linux, macOS, Windows
- **OpenAPI**: 3.0, 3.1 specifications
- **Generated clients**: Fully independent, no runtime dependency on generator

## 🔗 Links

- [GitHub Repository](https://github.com/mindhiveoy/pyopenapi_gen)
- [Documentation](https://github.com/mindhiveoy/pyopenapi_gen#readme)
- [PyPI Package](https://pypi.org/project/pyopenapi-gen/)

---

**Full Changelog**: [v0.8.4...v0.8.5](https://github.com/mindhiveoy/pyopenapi_gen/compare/v0.8.4...v0.8.5)
EOF < /dev/null