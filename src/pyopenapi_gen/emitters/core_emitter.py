import importlib.resources
import os

from pyopenapi_gen.context.file_manager import FileManager

# Each tuple: (module, filename, destination)
RUNTIME_FILES = [
    ("pyopenapi_gen.core", "http_transport.py", "core/http_transport.py"),
    ("pyopenapi_gen.core", "exceptions.py", "core/exceptions.py"),
    ("pyopenapi_gen.core", "streaming_helpers.py", "core/streaming_helpers.py"),
    ("pyopenapi_gen.core", "pagination.py", "core/pagination.py"),
    ("pyopenapi_gen.core.auth", "base.py", "core/auth/base.py"),
    ("pyopenapi_gen.core.auth", "plugins.py", "core/auth/plugins.py"),
]

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

    def __init__(self, core_dir: str = "core", core_package: str = "core"):
        self.core_dir = core_dir
        self.core_package = core_package
        self.file_manager = FileManager()

    def emit(self, output_dir: str) -> list[str]:
        generated_files = []
        for module, filename, rel_dst in RUNTIME_FILES:
            if self.core_dir:
                dst = os.path.join(output_dir, rel_dst.replace("core", self.core_dir, 1))
            else:
                # Remove 'core/' prefix from rel_dst
                dst = os.path.join(output_dir, rel_dst[len("core/") :] if rel_dst.startswith("core/") else rel_dst)
            self.file_manager.ensure_dir(os.path.dirname(dst))
            # Use importlib.resources to read the file from the package
            with importlib.resources.files(module).joinpath(filename).open("r") as f:
                content = f.read()
            self.file_manager.write_file(dst, content)
            generated_files.append(dst)
        # Always create __init__.py files for core and subfolders if core_dir is set
        if self.core_dir:
            core_init = os.path.join(output_dir, self.core_dir, "__init__.py")
            self.file_manager.write_file(core_init, "")
            generated_files.append(core_init)
            auth_init = os.path.join(output_dir, self.core_dir, "auth", "__init__.py")
            self.file_manager.write_file(auth_init, "")
            generated_files.append(auth_init)
        return generated_files
