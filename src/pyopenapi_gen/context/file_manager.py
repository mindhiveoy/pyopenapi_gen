"""
FileManager: Manages file operations for code generation.

This module provides utilities for creating directories and writing
generated Python code to files, with appropriate logging for debugging.
"""

import os


class FileManager:
    """
    Manages file operations for the code generation process.
    
    This class provides methods to write content to files and ensure directories
    exist, with built-in logging for debugging purposes.
    """
    
    def write_file(self, path: str, content: str) -> None:
        """
        Write content to a file, ensuring the parent directory exists.
        
        This method also logs the file path and first 10 lines of content
        to a debug log for troubleshooting purposes.
        
        Args:
            path: The absolute path to the file to write
            content: The string content to write to the file
        """
        self.ensure_dir(os.path.dirname(path))
        
        # Log the file path and first 10 lines of content for debugging
        with open("/tmp/pyopenapi_gen_file_write_debug.log", "a") as debug_log:
            debug_log.write(f"WRITE FILE: {path}\n")
            for line in content.splitlines()[:10]:
                debug_log.write(line + "\n")
            debug_log.write("---\n")
            
        # Write the content to the file
        with open(path, "w") as f:
            f.write(content)

    def ensure_dir(self, path: str) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: The directory path to ensure exists
        """
        os.makedirs(path, exist_ok=True)
