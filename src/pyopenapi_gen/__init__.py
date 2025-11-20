"""pyopenapi_gen – Core package

This package provides the internal representation (IR) dataclasses that act as an
intermediate layer between the parsed OpenAPI specification and the code
emitters.  The IR aims to be a *stable*, *fully‑typed* model that the rest of the
code‑generation pipeline can rely on.
"""

from __future__ import annotations

from pathlib import Path

# Removed dataclasses, field, Enum, unique from here, they are in ir.py and http_types.py
from typing import (
    TYPE_CHECKING,
    Any,
    List,
)

# Kept Any, List, Optional, TYPE_CHECKING for __getattr__ and __dir__
# Import HTTPMethod from its canonical location
from .http_types import HTTPMethod

# Import IR classes from their canonical location
from .ir import (
    IROperation,
    IRParameter,
    IRRequestBody,
    IRResponse,
    IRSchema,
    IRSpec,
)

__all__ = [
    # Main API
    "generate_client",
    "ClientGenerator",
    "GenerationError",
    # IR classes
    "HTTPMethod",
    "IRParameter",
    "IRResponse",
    "IROperation",
    "IRSchema",
    "IRSpec",
    "IRRequestBody",
    # Utilities
    "load_ir_from_spec",
    "WarningCollector",
]

# Semantic version of the generator core – automatically managed by semantic-release.
__version__: str = "2.1.0"

# ---------------------------------------------------------------------------
# Lazy-loading and autocompletion support (This part remains)
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    # Imports for static analysis
    from .core.loader.loader import load_ir_from_spec  # noqa: F401
    from .core.warning_collector import WarningCollector  # noqa: F401
    from .generator.client_generator import ClientGenerator, GenerationError  # noqa: F401

# Expose loader and collector at package level
# __all__ is already updated above


def __getattr__(name: str) -> Any:
    # Lazy-import attributes for runtime, supports IDE completion via TYPE_CHECKING
    if name == "load_ir_from_spec":
        from .core.loader.loader import load_ir_from_spec as _func

        return _func
    if name == "WarningCollector":
        from .core.warning_collector import WarningCollector as _warning_cls

        return _warning_cls
    if name == "ClientGenerator":
        from .generator.client_generator import ClientGenerator as _gen_cls

        return _gen_cls
    if name == "GenerationError":
        from .generator.client_generator import GenerationError as _exc

        return _exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    # Ensure dir() and completion shows all exports
    return __all__.copy()


# ---------------------------------------------------------------------------
# Main Programmatic API
# ---------------------------------------------------------------------------


def generate_client(
    spec_path: str,
    project_root: str,
    output_package: str,
    core_package: str | None = None,
    force: bool = False,
    no_postprocess: bool = False,
    verbose: bool = False,
) -> List[Path]:
    """Generate a Python client from an OpenAPI specification.

    This is the main entry point for programmatic usage of pyopenapi_gen.
    It provides a simple function-based API for generating OpenAPI clients
    without needing to instantiate classes or understand internal structure.

    Args:
        spec_path: Path to the OpenAPI specification file (YAML or JSON).
                  Can be a relative or absolute file path.

        project_root: Root directory of your Python project where the generated
                     client will be placed. This is the directory that contains
                     your top-level Python packages.

        output_package: Python package name for the generated client.
                       Uses dot notation (e.g., 'pyapis.my_client').
                       The client will be generated at:
                       {project_root}/{output_package_as_path}/

        core_package: Optional Python package name for shared core runtime.
                     If not specified, defaults to {output_package}.core.
                     Use this when generating multiple clients that share
                     common runtime code (auth, config, http transport, etc.).

        force: If True, overwrites existing output without diff checking.
              If False (default), compares with existing output and only
              updates if changes are detected.

        no_postprocess: If True, skips post-processing (Black formatting and
                       mypy type checking). Useful for faster iteration during
                       development.

        verbose: If True, prints detailed progress information during generation.

    Returns:
        List of Path objects for all generated files.

    Raises:
        GenerationError: If generation fails due to invalid spec, file I/O
                        errors, or other issues during code generation.

    Examples:
        Basic usage with default settings:

        >>> from pyopenapi_gen import generate_client
        >>>
        >>> files = generate_client(
        ...     spec_path="input/openapi.yaml",
        ...     project_root=".",
        ...     output_package="pyapis.my_client"
        ... )
        >>> print(f"Generated {len(files)} files")

        Generate multiple clients sharing a common core package:

        >>> from pyopenapi_gen import generate_client
        >>>
        >>> # Generate first client (creates shared core)
        >>> generate_client(
        ...     spec_path="api_v1.yaml",
        ...     project_root=".",
        ...     output_package="pyapis.client_v1",
        ...     core_package="pyapis.core"
        ... )
        >>>
        >>> # Generate second client (reuses core)
        >>> generate_client(
        ...     spec_path="api_v2.yaml",
        ...     project_root=".",
        ...     output_package="pyapis.client_v2",
        ...     core_package="pyapis.core"
        ... )

        Handle generation errors:

        >>> from pyopenapi_gen import generate_client, GenerationError
        >>>
        >>> try:
        ...     generate_client(
        ...         spec_path="openapi.yaml",
        ...         project_root=".",
        ...         output_package="pyapis.my_client",
        ...         verbose=True
        ...     )
        ... except GenerationError as e:
        ...     print(f"Generation failed: {e}")

        Force regeneration with verbose output:

        >>> generate_client(
        ...     spec_path="openapi.yaml",
        ...     project_root=".",
        ...     output_package="pyapis.my_client",
        ...     force=True,
        ...     verbose=True
        ... )

    Notes:
        - Generated clients are completely self-contained and require no
          runtime dependency on pyopenapi_gen
        - All generated code is automatically formatted with Black and
          type-checked with mypy (unless no_postprocess=True)
        - The generated client uses modern async/await patterns with httpx
        - Type hints are included for all generated code
    """
    from .generator.client_generator import ClientGenerator

    generator = ClientGenerator(verbose=verbose)
    return generator.generate(
        spec_path=spec_path,
        project_root=Path(project_root),
        output_package=output_package,
        core_package=core_package,
        force=force,
        no_postprocess=no_postprocess,
    )
