import os


class FileManager:
    def write_file(self, path: str, content: str) -> None:
        self.ensure_dir(os.path.dirname(path))
        # Log the file path and first 10 lines of content
        with open("/tmp/pyopenapi_gen_file_write_debug.log", "a") as debug_log:
            debug_log.write(f"WRITE FILE: {path}\n")
            for line in content.splitlines()[:10]:
                debug_log.write(line + "\n")
            debug_log.write("---\n")
        with open(path, "w") as f:
            f.write(content)

    def ensure_dir(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    # ... other helpers as needed
