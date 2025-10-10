"""Unit test for detecting circular imports."""

import unittest
from typing import Set

from pyopenapi_gen import IRSchema


class TestDetectCircularImports(unittest.TestCase):
    """Tests for the detection of circular imports and their handling."""

    def test_detect_circular_imports(self) -> None:
        """
        Scenario:
            When generating code for models that reference each other circularly,
            we need to detect and handle this case to avoid import errors.

        Expected Outcome:
            A set of schema names that form circular references is identified.
        """
        # Create schemas with circular dependencies
        schema_a = IRSchema(
            name="MessageA",
            type="object",
            properties={
                "b_ref": IRSchema(
                    name="b_ref",
                    type="MessageB",  # Reference to another schema
                )
            },
        )

        schema_b = IRSchema(
            name="MessageB",
            type="object",
            properties={
                "a_ref": IRSchema(
                    name="a_ref",
                    type="MessageA",  # Reference back to the first schema
                )
            },
        )

        # Map of all schemas by name
        schemas: dict[str, IRSchema] = {"MessageA": schema_a, "MessageB": schema_b}

        # Find circular references
        circular_refs = self._find_circular_references(schemas)

        # These two schemas should form a circular reference
        self.assertIn("MessageA", circular_refs)
        self.assertIn("MessageB", circular_refs)

    def _find_circular_references(self, schemas: dict[str, IRSchema]) -> Set[str]:
        """
        Find circular references in a set of schemas.

        This is a simplified version of what TypeHelper would do.
        """
        circular_refs: Set[str] = set()
        visited: dict[str, Set[str]] = {}

        def visit(schema_name: str, path: Set[str]) -> None:
            """Visit a schema and check for circular references."""
            if schema_name in path:
                # Found a circular reference
                circular_refs.add(schema_name)
                circular_refs.update(path)
                return

            if schema_name in visited:
                # Already visited this schema
                return

            # Mark as visited
            visited[schema_name] = set(path)

            # Get the schema
            schema = schemas.get(schema_name)
            if not schema:
                return

            # Check all property references
            for prop_name, prop in schema.properties.items():
                if prop.type and prop.type in schemas:
                    # This property references another schema
                    new_path = set(path)
                    new_path.add(schema_name)
                    visit(prop.type, new_path)

        # Visit each schema
        for schema_name in schemas:
            visit(schema_name, set())

        return circular_refs


if __name__ == "__main__":
    unittest.main()
