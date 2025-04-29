import os
from pyopenapi_gen.context.file_manager import FileManager

CONFIG_TEMPLATE = """
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClientConfig:
    base_url: str
    timeout: Optional[float] = 30.0
"""


class ConfigEmitter:
    """Emits config.py with a minimal ClientConfig class."""

    def __init__(self) -> None:
        self.file_manager = FileManager()

    def emit(self, output_dir: str) -> None:
        config_path = os.path.join(output_dir, "config.py")
        # Debug logging
        with open("/tmp/pyopenapi_gen_config_emitter_debug.log", "a") as debug_log:
            debug_log.write(f"ConfigEmitter.emit called. Writing to: {config_path}\n")
            for line in CONFIG_TEMPLATE.splitlines()[:10]:
                debug_log.write(line + "\n")
            debug_log.write("---\n")
        self.file_manager.write_file(config_path, CONFIG_TEMPLATE)
