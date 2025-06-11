# Changelog

All notable changes to PyOpenAPI Generator are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.4] - 2024-11-06

### Added
- Professional-grade documentation overhaul with comprehensive README.md
- Detailed contributing guidelines in CONTRIBUTING.md
- Formal changelog protocol following Keep a Changelog format
- Documentation index in docs/README.md with navigation
- Universal Why→What→How documentation structure standards

### Changed
- Enhanced README.md with modern badges, better structure, and comprehensive examples
- Improved project metadata and documentation standards in pyproject.toml
- Updated architecture documentation to follow established standards

### Removed
- Unused Jinja2 dependency (project uses visitor pattern, not templates)
- Feature status promises to avoid implementation commitments

## [0.8.3] - 2024-11-06

### Changed
- Minor improvements and maintenance updates

## [0.8.1] - 2024-11-06

### Added
- Enhanced schema handling capabilities
- Minor improvements to code generation

### Changed  
- Improved schema processing logic

## [0.8.0] - 2024-11-06

### Added
- ⭐ **NEW**: Unified type resolution system (`types/` package)
  - Clean architecture with contracts, resolvers, and services
  - Dependency injection with protocol-based design
  - Comprehensive test coverage for type resolution
- Enterprise-grade developer experience improvements
- Unified architecture across all components

### Changed
- Major refactoring to use unified type resolution throughout codebase
- Enhanced code generation reliability and consistency
- Improved error handling and type safety

### Fixed
- All failing tests resolved with new architecture
- mypy import errors resolved with proper httpx dependency

### Technical Details
- Implemented unified type resolution system for consistent type handling
- Applied black formatting to all source files
- Enhanced testing coverage and reliability

## [0.7.x] - Previous Versions

### Added
- Core OpenAPI client generation functionality
- Async-first Python client architecture
- Advanced cycle detection for complex schemas
- Pluggable authentication system
- Smart pagination support
- Response unwrapping capabilities
- Tag-based operation organization
- Comprehensive error handling
- Self-contained client generation (zero runtime dependencies)

### Features Established
- Three-stage pipeline: Load → Visit → Emit
- Intermediate Representation (IR) for stable code generation
- Support for Python 3.10-3.12
- Integration with modern Python tooling (Black, Ruff, mypy)
- Comprehensive test suite with high coverage requirements

---

## Release Notes Format

Each release includes:

- **Added**: New features and capabilities
- **Changed**: Modifications to existing functionality  
- **Deprecated**: Features marked for future removal
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes and issue resolutions
- **Security**: Security vulnerability fixes

## Version History Links

- [Unreleased]: Compare against latest release
- [0.8.3]: https://github.com/your-org/pyopenapi-gen/releases/tag/v0.8.3
- [0.8.1]: https://github.com/your-org/pyopenapi-gen/releases/tag/v0.8.1  
- [0.8.0]: https://github.com/your-org/pyopenapi-gen/releases/tag/v0.8.0

## Contributing to the Changelog

When contributing changes:

1. Add entries to the `[Unreleased]` section
2. Use the appropriate category (Added, Changed, Fixed, etc.)
3. Write clear, descriptive entries
4. Include issue/PR references when relevant
5. Follow the established format and tone

Example entry:
```markdown
### Added
- OAuth2 authentication support with refresh token handling (#123)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines.