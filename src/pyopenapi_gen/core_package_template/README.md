# Core Runtime Components

This directory contains the core runtime components required by the generated API client.

## Client Independence

**The generated API client is fully independent and does NOT require the `pyopenapi_gen` package to be installed at runtime.**

All necessary base classes, protocols, transport implementations, and utility functions are included directly within this `core` package. You can safely use the generated client in any Python environment without installing the generator itself.

## Shared Core (Optional)

In scenarios where multiple API clients are generated (perhaps for different services within the same ecosystem), you might want to share a single instance of this `core` package to avoid duplication.

To achieve this:
1.  Generate the first client normally. This will create the `core` package.
2.  Move or copy this `core` package to a location accessible by all your client packages (e.g., a shared `libs` directory).
3.  Ensure this shared location is included in your Python environment's `PYTHONPATH`.
4.  When generating subsequent clients, use the `--core-import-path <path_to_shared_core>` option with `pyopenapi-gen`. This tells the generator *not* to create a new `core` directory but instead to generate imports relative to the specified shared path (e.g., `from shared_libs.core.http_transport import HttpTransport`).

This allows multiple clients to reuse the same base implementation, reducing code size and ensuring consistency. 