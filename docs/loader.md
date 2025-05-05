# Loader (`core/loader.py`)

This component acts as the entry point for processing the raw OpenAPI specification after it has been loaded from a file (e.g., YAML or JSON) into a Python dictionary. Its primary goal is to transform this unstructured data into the structured, typed Intermediate Representation (IR).

Responsible for parsing the raw OpenAPI specification dictionary and converting it into the Intermediate Representation (IR) objects (like `IRSpec`, `IROperation`, `IRSchema`).

This module handles:
*   Reading the spec structure.
*   Resolving `$ref` JSON Pointers within the specification.
*   Instantiating the IR dataclasses.
*   Basic validation and normalization of the spec data. 