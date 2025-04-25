from pyopenapi_gen.utils import ImportCollector


def test_import_collector_basic():
    """Test the basic functionality of the ImportCollector.

    Scenario:
        - Add single imports from different modules
        - Generate import statements

    Expected outcome:
        - Each import should be properly formatted as 'from module import name'
        - All added imports should be present in the generated statements
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_import("sys", "exit")

    statements = collector.get_import_statements()

    assert "from os import path" in statements
    assert "from sys import exit" in statements


def test_import_collector_multiple_from_same_module():
    """Test collecting multiple imports from the same module.

    Scenario:
        - Add multiple imports from a single module
        - Generate import statements

    Expected outcome:
        - All imports from the same module should be consolidated into a single statement
        - The imports should be alphabetically sorted
        - The format should be 'from module import name1, name2, name3'
    """
    collector = ImportCollector()
    collector.add_imports("os", ["path", "environ", "makedirs"])

    statements = collector.get_import_statements()
    assert len(statements) == 1
    assert "from os import environ, makedirs, path" in statements


def test_import_collector_typing_imports():
    """Test the specialized helper for typing imports.

    Scenario:
        - Use the add_typing_import helper to add multiple typing imports
        - Generate import statements

    Expected outcome:
        - All typing imports should be consolidated into a single statement
        - The imports should be alphabetically sorted
        - The format should be 'from typing import Type1, Type2, Type3'
    """
    collector = ImportCollector()
    collector.add_typing_import("List")
    collector.add_typing_import("Dict")
    collector.add_typing_import("Optional")

    statements = collector.get_import_statements()
    assert len(statements) == 1
    assert "from typing import Dict, List, Optional" in statements


def test_import_collector_direct_imports():
    """Test the direct import collection functionality.

    Scenario:
        - Add direct imports from different modules using add_direct_import
        - Generate import statements

    Expected outcome:
        - Direct imports should be included in the generated statements
        - Each direct import should be properly formatted as 'from module import name'
        - Direct imports should be grouped separately from standard imports
    """
    collector = ImportCollector()
    collector.add_direct_import("datetime", "datetime")
    collector.add_direct_import("dataclasses", "dataclass")

    statements = collector.get_import_statements()
    assert len(statements) >= 2
    assert "from datetime import datetime" in statements
    assert "from dataclasses import dataclass" in statements


def test_import_collector_relative_imports():
    """Test the relative import collection functionality.

    Scenario:
        - Add relative imports (imports prefixed with '.') using add_relative_import
        - Generate import statements

    Expected outcome:
        - Relative imports should be included in the generated statements
        - Multiple imports from the same relative module should be consolidated
        - The format should be 'from .module import Name1, Name2'
    """
    collector = ImportCollector()
    collector.add_relative_import(".models", "Pet")
    collector.add_relative_import(".models", "User")

    statements = collector.get_import_statements()
    assert "from .models import Pet, User" in statements


def test_import_collector_ordering():
    """Test the ordering of different import types.

    Scenario:
        - Add a mix of standard, direct, and relative imports
        - Generate import statements and analyze their order

    Expected outcome:
        - Standard imports should appear first
        - Direct imports should appear after standard imports
        - Relative imports should appear last
        - This ordering follows PEP 8 conventions for import ordering
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_direct_import("dataclasses", "dataclass")
    collector.add_relative_import(".models", "Pet")

    statements = collector.get_import_statements()

    # Check that standard imports come first
    first_import_index = statements.index("from os import path")

    # Find direct imports
    direct_import_index = -1
    for i, stmt in enumerate(statements):
        if "from dataclasses import dataclass" in stmt:
            direct_import_index = i
            break

    # Find relative imports
    relative_import_index = -1
    for i, stmt in enumerate(statements):
        if "from .models import Pet" in stmt:
            relative_import_index = i
            break

    assert (
        direct_import_index > first_import_index
    ), "Direct imports should come after standard imports"
    assert (
        relative_import_index > direct_import_index
    ), "Relative imports should come after direct imports"


def test_import_collector_formatted_output():
    """Test the formatted string output method.

    Scenario:
        - Add various imports
        - Generate a formatted string of import statements

    Expected outcome:
        - The output should be a string containing all import statements
        - Each import statement should be on its own line
        - The format should follow our import ordering conventions
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_typing_import("List")

    formatted = collector.get_formatted_imports()

    assert "from os import path" in formatted
    assert "from typing import List" in formatted
    assert isinstance(formatted, str)


def test_import_collector_deduplication():
    """Test that duplicate imports are automatically deduplicated.

    Scenario:
        - Add the same import multiple times
        - Generate import statements

    Expected outcome:
        - Each import should appear only once in the output
        - There should be no duplicate import statements
    """
    collector = ImportCollector()
    # Add the same import multiple times
    collector.add_typing_import("List")
    collector.add_typing_import("List")
    collector.add_typing_import("Dict")

    # Add duplicate direct imports
    collector.add_direct_import("datetime", "date")
    collector.add_direct_import("datetime", "date")

    statements = collector.get_import_statements()

    # Check typing imports
    typing_statements = [s for s in statements if "typing" in s]
    assert len(typing_statements) == 1
    assert "from typing import Dict, List" in typing_statements

    # Check direct imports
    datetime_statements = [s for s in statements if "datetime" in s]
    assert len(datetime_statements) == 1
    assert "from datetime import date" in datetime_statements


def test_import_collector_empty():
    """Test the behavior when no imports have been added.

    Scenario:
        - Create an ImportCollector but don't add any imports
        - Generate import statements

    Expected outcome:
        - The list of import statements should be empty
        - The formatted output should be an empty string
    """
    collector = ImportCollector()

    statements = collector.get_import_statements()
    formatted = collector.get_formatted_imports()

    assert len(statements) == 0
    assert formatted == ""


def test_import_collector_has_import():
    """Test the has_import method for checking if imports exist.

    Scenario:
        - Add some imports
        - Check for existence of added and non-added imports

    Expected outcome:
        - has_import should return True for imports that have been added
        - has_import should return False for imports that haven't been added
    """
    collector = ImportCollector()
    collector.add_import("os", "path")
    collector.add_typing_import("List")

    assert collector.has_import("os", "path") is True
    assert collector.has_import("typing", "List") is True
    assert collector.has_import("os", "environ") is False
    assert collector.has_import("sys", "exit") is False
