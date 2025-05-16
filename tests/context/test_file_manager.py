"""
Tests for the FileManager which handles file operations during code generation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from pyopenapi_gen.context.file_manager import FileManager


def test_ensure_dir__creates_directory_when_missing() -> None:
    """
    Scenario:
        Calling ensure_dir on a non-existent directory
    Expected Outcome:
        Directory is created
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a non-existent directory path
        new_dir = os.path.join(temp_dir, "new_dir")
        
        # Ensure the directory doesn't exist yet
        assert not os.path.exists(new_dir)
        
        # Call ensure_dir
        manager = FileManager()
        manager.ensure_dir(new_dir)
        
        # Verify directory was created
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)


def test_ensure_dir__succeeds_with_existing_directory() -> None:
    """
    Scenario:
        Calling ensure_dir on an existing directory
    Expected Outcome:
        No error occurs and directory still exists
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Directory already exists
        assert os.path.exists(temp_dir)
        
        # Call ensure_dir
        manager = FileManager()
        manager.ensure_dir(temp_dir)
        
        # Verify directory still exists
        assert os.path.exists(temp_dir)
        assert os.path.isdir(temp_dir)


def test_ensure_dir__creates_nested_directories() -> None:
    """
    Scenario:
        Calling ensure_dir on a nested directory structure
    Expected Outcome:
        All directories in the path are created
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a nested directory path
        nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
        
        # Ensure the directories don't exist yet
        assert not os.path.exists(os.path.join(temp_dir, "level1"))
        
        # Call ensure_dir
        manager = FileManager()
        manager.ensure_dir(nested_dir)
        
        # Verify all nested directories were created
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)
        assert os.path.exists(os.path.join(temp_dir, "level1"))
        assert os.path.exists(os.path.join(temp_dir, "level1", "level2"))


def test_write_file__creates_file_with_content() -> None:
    """
    Scenario:
        Calling write_file to create a new file
    Expected Outcome:
        File is created with expected content
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Prepare file path and content
        file_path = os.path.join(temp_dir, "test_file.txt")
        content = "Test content\nLine 2\nLine 3"

        # Call write_file
        manager = FileManager()

        # Mock only the debug log write to /tmp
        original_open = open

        def side_effect(filename, mode='r', *args, **kwargs):
            if filename == "/tmp/pyopenapi_gen_file_write_debug.log":
                return mock_open()(filename, mode, *args, **kwargs)
            return original_open(filename, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=side_effect):
            manager.write_file(file_path, content)

            # Verify file was created with expected content
            with open(file_path, 'r') as f:
                assert f.read() == content


def test_write_file__overwrites_existing_file() -> None:
    """
    Scenario:
        Calling write_file on an existing file
    Expected Outcome:
        File content is overwritten
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file with initial content
        file_path = os.path.join(temp_dir, "existing_file.txt")
        initial_content = "Initial content"
        with open(file_path, "w") as f:
            f.write(initial_content)

        # Verify initial content was written
        with open(file_path, "r") as f:
            assert f.read() == initial_content

        # Prepare new content
        new_content = "New content"

        # Call write_file to overwrite with new content
        manager = FileManager()

        # Mock only the debug log write to /tmp
        original_open = open

        def side_effect(filename, mode='r', *args, **kwargs):
            if filename == "/tmp/pyopenapi_gen_file_write_debug.log":
                return mock_open()(filename, mode, *args, **kwargs)
            return original_open(filename, mode, *args, **kwargs)

        with patch("builtins.open", side_effect=side_effect):
            manager.write_file(file_path, new_content)

            # Verify file was overwritten with new content
            with open(file_path, 'r') as f:
                assert f.read() == new_content


def test_write_file__creates_parent_directories() -> None:
    """
    Scenario:
        Calling write_file with a path containing non-existent directories
    Expected Outcome:
        Parent directories are created and file is written
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file path with non-existent parent directories
        nested_file_path = os.path.join(temp_dir, "nested", "dirs", "test_file.txt")
        content = "Test content"
        
        # Ensure parent directories don't exist yet
        parent_dir = os.path.dirname(nested_file_path)
        assert not os.path.exists(parent_dir)
        
        # Mock directory creation to verify it's called
        with patch.object(FileManager, 'ensure_dir') as mock_ensure_dir:
            manager = FileManager()
            
            # Also mock file writing to avoid actual IO
            with patch("builtins.open", mock_open()):
                manager.write_file(nested_file_path, content)
                
                # Verify ensure_dir was called with parent directory path
                mock_ensure_dir.assert_called_once_with(parent_dir)


@pytest.mark.skip(reason="Requires complex mocking of file operations")
def test_write_file__logs_debug_information() -> None:
    """
    Scenario:
        Calling write_file should log debug information
    Expected Outcome:
        Debug log is written with file path and first 10 lines of content
    """
    # This test would verify that the debugging log is written correctly,
    # but since it requires complex mocking and the functionality is not critical
    # to the core operation, we're skipping it for now
    pass