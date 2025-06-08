import importlib.resources
import os
from typing import List, Optional

from pyopenapi_gen.context.file_manager import FileManager

# Each tuple: (module, filename, destination)
RUNTIME_FILES = [
    ("pyopenapi_gen.core", "http_transport.py", "core/http_transport.py"),
    ("pyopenapi_gen.core", "exceptions.py", "core/exceptions.py"),
    ("pyopenapi_gen.core", "streaming_helpers.py", "core/streaming_helpers.py"),
    ("pyopenapi_gen.core", "pagination.py", "core/pagination.py"),
    ("pyopenapi_gen.core", "schemas.py", "core/schemas.py"),
    ("pyopenapi_gen.core.auth", "base.py", "core/auth/base.py"),
    ("pyopenapi_gen.core.auth", "plugins.py", "core/auth/plugins.py"),
]

# +++ Add template README location +++
CORE_README_TEMPLATE_MODULE = "pyopenapi_gen.core_package_template"
CORE_README_TEMPLATE_FILENAME = "README.md"

CONFIG_TEMPLATE = """
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClientConfig:
    base_url: str
    timeout: Optional[float] = 30.0
"""


class CoreEmitter:
    """Copies all required runtime files into the generated core module."""

    def __init__(
        self, core_dir: str = "core", core_package: str = "core", exception_alias_names: Optional[List[str]] = None
    ):
        # core_dir is the relative path WITHIN the output package, e.g., "core" or "shared/core"
        # core_package is the Python import name, e.g., "core" or "shared.core"
        self.core_dir_name = os.path.basename(core_dir)  # e.g., "core"
        self.core_dir_relative = core_dir  # e.g., "core" or "shared/core"
        self.core_package = core_package
        self.exception_alias_names = exception_alias_names if exception_alias_names is not None else []
        self.file_manager = FileManager()

    def emit(self, package_output_dir: str) -> list[str]:
        """
        Emits the core files into the specified core directory within the package output directory.
        Args:
            package_output_dir: The root directory where the generated package is being placed.
                                  e.g., /path/to/gen/my_client
        Returns:
            List of generated file paths relative to the workspace root.
        """
        # Determine the absolute path for the core directory, e.g., /path/to/gen/my_client/core
        actual_core_dir = os.path.join(package_output_dir, self.core_dir_relative)

        generated_files = []
        # Ensure the core directory exists (e.g., my_client/core or my_client/shared/core)
        self.file_manager.ensure_dir(actual_core_dir)

        for module, filename, rel_dst in RUNTIME_FILES:
            # rel_dst is like "core/http_transport.py" or "core/auth/base.py"
            # We want the part after "core/", e.g., "http_transport.py" or "auth/base.py"
            # And join it with the actual_core_dir
            destination_relative_to_core = rel_dst.replace("core/", "", 1)
            dst = os.path.join(actual_core_dir, destination_relative_to_core)

            self.file_manager.ensure_dir(os.path.dirname(dst))
            # Use importlib.resources to read the file from the package
            try:
                # Read from pyopenapi_gen.core... or pyopenapi_gen.core.auth...
                with importlib.resources.files(module).joinpath(filename).open("r") as f:
                    content = f.read()
                self.file_manager.write_file(dst, content)
                generated_files.append(dst)
            except FileNotFoundError:
                print(f"Warning: Could not find runtime file {filename} in module {module}. Skipping.")

        # Always create __init__.py files for core and subfolders within the actual core dir
        core_init_path = os.path.join(actual_core_dir, "__init__.py")
        core_init_content = [
            "# Re-export core exceptions and generated aliases",
            "from .exceptions import HTTPError, ClientError, ServerError",
            "from .exception_aliases import *  # noqa: F403",
            "",
            "# Re-export other commonly used core components",
            "from .http_transport import HttpTransport, HttpxTransport",
            "from .config import ClientConfig",
            "from .schemas import BaseSchema",
            "from .auth.base import BaseAuth",
            "from .auth.plugins import ApiKeyAuth, BearerAuth, OAuth2Auth",
            "",
            "__all__ = [",
            "    # Base exceptions",
            '    "HTTPError",',
            '    "ClientError",',
            '    "ServerError",',
            "    # All ErrorXXX from exception_aliases are implicitly in __all__ due to star import",
            "",
            "    # Transport layer",
            '    "HttpTransport",',
            '    "HttpxTransport",',
            "",
            "    # Configuration",
            '    "ClientConfig",',
            "",
            "    # Schemas",
            '    "BaseSchema",',
            "",
            "    # Authentication",
            '    "BaseAuth",',
            '    "ApiKeyAuth",',
            '    "BearerAuth",',
            '    "OAuth2Auth",',
        ]
        # Add discovered exception alias names to __all__
        if self.exception_alias_names:
            core_init_content.append("    # Generated exception aliases")
            for alias_name in sorted(list(set(self.exception_alias_names))):  # Sort and unique
                core_init_content.append(f'    "{alias_name}",')

        core_init_content.append("]")

        self.file_manager.write_file(core_init_path, "\n".join(core_init_content))
        generated_files.append(core_init_path)

        auth_dir = os.path.join(actual_core_dir, "auth")
        if os.path.exists(auth_dir):  # Only create auth/__init__.py if auth files were copied
            auth_init_path = os.path.join(auth_dir, "__init__.py")
            self.file_manager.ensure_dir(os.path.dirname(auth_init_path))
            auth_init_content = [
                "# Core Auth __init__",
                "from .base import BaseAuth",
                "from .plugins import ApiKeyAuth, BearerAuth, OAuth2Auth",
                "",
                "__all__ = [",
                '    "BaseAuth",',
                '    "ApiKeyAuth",',
                '    "BearerAuth",',
                '    "OAuth2Auth",',
                "]",
            ]
            self.file_manager.write_file(auth_init_path, "\n".join(auth_init_content) + "\n")
            generated_files.append(auth_init_path)

        # Ensure py.typed marker for mypy in the actual core directory
        pytyped_path = os.path.join(actual_core_dir, "py.typed")
        if not os.path.exists(pytyped_path):
            self.file_manager.write_file(pytyped_path, "")  # Create empty py.typed
        generated_files.append(pytyped_path)

        # Copy the core README template into the actual core directory
        readme_dst = os.path.join(actual_core_dir, "README.md")
        try:
            with (
                importlib.resources.files(CORE_README_TEMPLATE_MODULE)
                .joinpath(CORE_README_TEMPLATE_FILENAME)
                .open("r") as f
            ):
                readme_content = f.read()
            self.file_manager.write_file(readme_dst, readme_content)
            generated_files.append(readme_dst)
        except FileNotFoundError:
            print(
                f"Warning: Could not find core README template {CORE_README_TEMPLATE_FILENAME} "
                f"in {CORE_README_TEMPLATE_MODULE}. Skipping."
            )

        # Generate config.py from template inside the actual core directory
        config_path = os.path.join(actual_core_dir, "config.py")
        self.file_manager.write_file(config_path, CONFIG_TEMPLATE)
        generated_files.append(config_path)

        return generated_files
