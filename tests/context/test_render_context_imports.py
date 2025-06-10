import pytest

from pyopenapi_gen.context.import_collector import ImportCollector


@pytest.mark.parametrize(
    "imports_to_add, expected_output_lines",
    [
        # Basic case
        ([("typing", "List")], ["from typing import List"]),
        # Multiple from same
        ([("typing", "List"), ("typing", "Dict")], ["from typing import Dict, List"]),
        # Multiple different
        ([("typing", "List"), ("os", "path")], ["from os import path", "from typing import List"]),
        # Plain import
        ([("json", "")], ["import json"]),
        # Relative import
        ([(".models", "Foo")], ["from .models import Foo"]),
        # Mix
        (
            [("typing", "List"), (".models", "Foo"), ("json", "")],
            ["import json", "from .models import Foo", "from typing import List"],
        ),
    ],
)
def test_import_collector_logic(imports_to_add: list[tuple[str, str]], expected_output_lines: list[str]) -> None:
    """Tests basic import collection and formatting logic in ImportCollector."""
    collector = ImportCollector()
    for module, name in imports_to_add:
        if name == "":  # Simulate plain import
            collector.add_plain_import(module)
        elif module.startswith("."):
            collector.add_relative_import(module, name)
        else:
            collector.add_import(module, name)

    result_lines = collector.get_import_statements()  # No arguments
    assert sorted(result_lines) == sorted(expected_output_lines)
