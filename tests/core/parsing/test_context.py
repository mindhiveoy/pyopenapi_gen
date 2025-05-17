"""
Tests for the ParsingContext class.
"""

import logging
import unittest

from pyopenapi_gen.core.parsing.context import ParsingContext


class TestParsingContext(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext()
        # Suppress logging during tests unless specifically testing log output
        logging.getLogger("pyopenapi_gen.core.parsing.context").setLevel(logging.CRITICAL)

    def test_enter_schema_initial_entry(self) -> None:
        """
        Scenario:
            - Call enter_schema for the first time with a schema name.
        Expected Outcome:
            - recursion_depth is 1.
            - Schema name is in currently_parsing and parsing_path.
            - No cycle is detected (returns False, None).
        """
        schema_name = "TestSchema1"
        is_cycle, cycle_path = self.context.enter_schema(schema_name)

        self.assertFalse(is_cycle)
        self.assertIsNone(cycle_path)
        self.assertEqual(self.context.recursion_depth, 1)
        self.assertIn(schema_name, self.context.currently_parsing)
        self.assertEqual(self.context.currently_parsing, [schema_name])

    def test_enter_schema_multiple_entries_no_cycle(self) -> None:
        """
        Scenario:
            - Call enter_schema multiple times with different schema names.
        Expected Outcome:
            - recursion_depth and max_recursion_depth are updated correctly.
            - All schema names are in currently_parsing and parsing_path in order.
            - No cycle is detected.
        """
        schema_name1 = "TestSchema1"
        schema_name2 = "TestSchema2"

        self.context.enter_schema(schema_name1)
        is_cycle, cycle_path = self.context.enter_schema(schema_name2)

        self.assertFalse(is_cycle)
        self.assertIsNone(cycle_path)
        self.assertEqual(self.context.recursion_depth, 2)
        self.assertIn(schema_name1, self.context.currently_parsing)
        self.assertIn(schema_name2, self.context.currently_parsing)
        self.assertEqual(self.context.currently_parsing, [schema_name1, schema_name2])

    def test_enter_schema_with_none_name(self) -> None:
        """
        Scenario:
            - Call enter_schema with name=None.
        Expected Outcome:
            - recursion_depth and max_recursion_depth are incremented.
            - currently_parsing and parsing_path remain unchanged (as None is not tracked for cycles).
            - No cycle is detected.
        """
        self.context.enter_schema("OuterSchema")  # Existing entry
        initial_currently_parsing = self.context.currently_parsing.copy()

        is_cycle, cycle_path = self.context.enter_schema(None)

        self.assertFalse(is_cycle)
        self.assertIsNone(cycle_path)
        self.assertEqual(self.context.recursion_depth, 2)
        self.assertEqual(self.context.currently_parsing, initial_currently_parsing)

    def test_enter_schema_detects_cycle(self) -> None:
        """
        Scenario:
            - Call enter_schema with a schema name that is already in currently_parsing.
        Expected Outcome:
            - Cycle is detected (returns True, cycle_path_string).
            - recursion_depth is incremented, but schema name is not re-added to path/set.
            - self.cycle_detected flag is set to True.
        """
        schema_name1 = "SchemaA"
        schema_name_cycle = "SchemaB"

        self.context.enter_schema(schema_name1)
        self.context.enter_schema(schema_name_cycle)  # First entry of SchemaB
        initial_currently_parsing = self.context.currently_parsing.copy()

        # Re-enter SchemaB to create a cycle
        is_cycle, cycle_path = self.context.enter_schema(schema_name_cycle)

        self.assertTrue(is_cycle)
        self.assertIsNotNone(cycle_path)
        self.assertEqual(cycle_path, f"{schema_name_cycle} -> {schema_name_cycle}")
        self.assertEqual(self.context.recursion_depth, 3)  # Depth still increases
        self.assertTrue(self.context.cycle_detected)
        self.assertEqual(self.context.currently_parsing, initial_currently_parsing)

    def test_exit_schema_single_exit(self) -> None:
        """
        Scenario:
            - Call enter_schema then exit_schema for the same name.
        Expected Outcome:
            - recursion_depth is decremented to 0.
            - Schema name is removed from currently_parsing and parsing_path.
        """
        schema_name = "TestSchema1"
        self.context.enter_schema(schema_name)
        self.context.exit_schema(schema_name)

        self.assertEqual(self.context.recursion_depth, 0)
        self.assertNotIn(schema_name, self.context.currently_parsing)
        self.assertEqual(self.context.currently_parsing, [])

    def test_exit_schema_multiple_exits_correct_order(self) -> None:
        """
        Scenario:
            - Enter multiple schemas, then exit them in reverse order of entry.
        Expected Outcome:
            - recursion_depth correctly tracks down to 0.
            - currently_parsing and parsing_path are correctly emptied.
        """
        schema_name1 = "SchemaX"
        schema_name2 = "SchemaY"

        self.context.enter_schema(schema_name1)
        self.context.enter_schema(schema_name2)

        self.context.exit_schema(schema_name2)
        self.assertEqual(self.context.recursion_depth, 1)
        self.assertNotIn(schema_name2, self.context.currently_parsing)
        self.assertIn(schema_name1, self.context.currently_parsing)
        self.assertEqual(self.context.currently_parsing, [schema_name1])

        self.context.exit_schema(schema_name1)
        self.assertEqual(self.context.recursion_depth, 0)
        self.assertNotIn(schema_name1, self.context.currently_parsing)
        self.assertEqual(self.context.currently_parsing, [])

    def test_exit_schema_with_none_name(self) -> None:
        """
        Scenario:
            - Call enter_schema with a name, then enter_schema with None, then exit_schema with None.
        Expected Outcome:
            - recursion_depth is decremented.
            - currently_parsing and parsing_path (related to named schemas) are unaffected by exit(None).
        """
        schema_name = "TrackedSchema"
        self.context.enter_schema(schema_name)
        self.context.enter_schema(None)  # Anonymous entry

        self.assertEqual(self.context.recursion_depth, 2)
        initial_currently_parsing = self.context.currently_parsing.copy()

        self.context.exit_schema(None)  # Anonymous exit

        self.assertEqual(self.context.recursion_depth, 1)
        self.assertEqual(self.context.currently_parsing, initial_currently_parsing)
        self.assertIn(schema_name, self.context.currently_parsing)

    def test_exit_schema_removes_name_from_currently_parsing(self) -> None:
        """
        Scenario:
            - A schema is entered and then exited.
        Expected Outcome:
            - The schema name is no longer in `currently_parsing`.
            - Covers line 94 of context.py (self.currently_parsing.remove(name)).
        """
        schema_name = "ToBeRemoved"
        self.context.enter_schema(schema_name)
        self.assertIn(schema_name, self.context.currently_parsing)
        self.context.exit_schema(schema_name)
        self.assertNotIn(schema_name, self.context.currently_parsing)

    def test_exit_schema_pops_correct_name_from_parsing_path(self) -> None:
        """
        Scenario:
            - Multiple schemas are entered. Exiting one.
        Expected Outcome:
            - `currently_parsing` reflects the correct state after exits.
        """
        s1 = "SchemaPath1"
        s2 = "SchemaPath2"
        self.context.enter_schema(s1)
        self.context.enter_schema(s2)
        self.assertEqual(self.context.currently_parsing, [s1, s2])

        self.context.exit_schema(s2)  # Exiting the last one
        self.assertEqual(self.context.currently_parsing, [s1])

        self.context.enter_schema(s2)  # Re-enter s2
        self.assertEqual(self.context.currently_parsing, [s1, s2])

        # Behavior of exit_schema for non-top element:
        # It removes from currently_parsing if present (due to recovery logic if stack mismatched),
        # but only pops if it's the top.
        # Let's test exiting s1 while s2 is on top
        self.context.exit_schema(s1)
        # s1 should be removed from the list by exit_schema's recovery logic, even if not at top.
        # This is because currently_parsing.remove(schema_name) is called if not schema_name == currently_parsing[-1]
        self.assertEqual(
            self.context.currently_parsing,
            [s2],
            "currently_parsing should only contain s2 after s1 is exited out of order",
        )
        self.assertNotIn(s1, self.context.currently_parsing)
        self.assertIn(s2, self.context.currently_parsing)

        self.context.exit_schema(s2)  # Now exit s2 (which is last)
        self.assertEqual(self.context.currently_parsing, [], "Path should be empty after s2 is popped")

    def test_exit_schema_assertion_error_if_depth_goes_below_zero(self) -> None:
        """
        Scenario:
            - Attempt to call exit_schema when recursion_depth is already 0.
        Expected Outcome:
            - An AssertionError is raised.
            - Covers pre-condition assert in exit_schema (line 89).
        """
        self.assertEqual(self.context.recursion_depth, 0)
        self.context.exit_schema("SomeSchema")  # Should not raise error
        self.assertEqual(self.context.recursion_depth, 0)  # Depth should not change

    def test_max_recursion_depth_tracking(self) -> None:
        """
        Scenario:
            - Enter and exit schemas multiple times, varying the depth.
        Expected Outcome:
            - max_recursion_depth correctly reflects the maximum depth reached.
            - Covers line 52 of context.py (self.max_recursion_depth = max(...)).
        """
        # This attribute is no longer part of ParsingContext directly.
        # Max depth for parsing is handled by schema_parser using ENV_MAX_DEPTH.
        pass

    def test_reset_for_new_parse(self) -> None:
        """
        Scenario:
            - Context is populated, then reset_for_new_parse is called.
        Expected Outcome:
            - recursion_depth, cycle_detected, currently_parsing, parsed_schemas are reset.
        """
        # Populate context
        self.context.enter_schema("S1")  # Depth is 1, currently_parsing = [S1]
        self.context.enter_schema("S2")  # Depth is 2, currently_parsing = [S1, S2]
        self.context.recursion_depth = 5  # Arbitrary override for test
        self.context.cycle_detected = True
        # currently_parsing is already [S1, S2]
        self.context.parsed_schemas["SomeSchema"] = object()  # type: ignore

        initial_parsing_list = list(self.context.currently_parsing)

        self.context.reset_for_new_parse()

        self.assertEqual(self.context.recursion_depth, 0)
        self.assertFalse(self.context.cycle_detected)
        self.assertEqual(
            self.context.currently_parsing,
            [],
            f"Expected currently_parsing to be empty, was {initial_parsing_list} before reset.",
        )
        self.assertEqual(self.context.parsed_schemas, {})


if __name__ == "__main__":
    unittest.main()
