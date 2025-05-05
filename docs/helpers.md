# Helpers (`helpers/`)

This directory provides a collection of utility classes and functions that support various tasks within the code generation pipeline, promoting code reuse and separation of concerns.

This directory contains utility modules used throughout the generation process.

Known/Likely Modules:
*   `code_writer.py`: Aids in building Python code strings with correct indentation and formatting. See [LineWriter Documentation](./line_writer.md) for details.
*   `name_sanitizer.py`: Converts OpenAPI names (operation IDs, schema names) into valid Python identifiers (class names, function names, variable names).
*   Other utility functions as needed. 