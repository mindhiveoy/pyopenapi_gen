import unittest

from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.cycle_helpers import _handle_cycle_detection, _handle_max_depth_exceeded


class TestCycleHelpers(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext()

    def test_handle_cycle_detection__new_name__creates_placeholder(self) -> None:
        """
        Scenario:
            - A cycle is detected for a schema name not yet in context.
        Expected Outcome:
            - Returns an IRSchema with correct flags and registers it in context.
        """
        name = "MySchema"
        cycle_path = "MySchema -> MySchema"
        schema = _handle_cycle_detection(name, cycle_path, self.context)
        assert schema.name == name
        assert schema._is_circular_ref
        assert schema._from_unresolved_ref
        assert schema._circular_ref_path == cycle_path
        assert self.context.parsed_schemas[name] is schema

    def test_handle_cycle_detection__existing_name__reuses_and_sets_flags(self) -> None:
        """
        Scenario:
            - A cycle is detected for a schema name already in context.
        Expected Outcome:
            - Returns the same IRSchema, ensures flags are set, and does not create a new object.
        """
        name = "ExistingSchema"
        cycle_path = "ExistingSchema -> ExistingSchema"
        # Pre-populate context with a stub
        from pyopenapi_gen import IRSchema

        stub = IRSchema(name=name)
        self.context.parsed_schemas[name] = stub
        schema = _handle_cycle_detection(name, cycle_path, self.context)
        assert schema is stub
        assert schema._is_circular_ref
        assert schema._from_unresolved_ref
        assert schema._circular_ref_path == cycle_path

    def test_handle_max_depth_exceeded__new_name__creates_placeholder(self) -> None:
        """
        Scenario:
            - Max recursion depth is exceeded for a schema name not yet in context.
        Expected Outcome:
            - Returns an IRSchema with correct flags and registers it in context.
        """
        name = "DeepSchema"
        max_depth = 5
        schema = _handle_max_depth_exceeded(name, self.context, max_depth)
        assert schema.name == name
        assert schema._is_circular_ref
        assert schema._from_unresolved_ref
        if schema._circular_ref_path is not None:
            assert "MAX_DEPTH_EXCEEDED" in schema._circular_ref_path
        assert self.context.parsed_schemas[name] is schema

    def test_handle_max_depth_exceeded__existing_name__reuses_and_sets_flags(self) -> None:
        """
        Scenario:
            - Max recursion depth is exceeded for a schema name already in context.
        Expected Outcome:
            - Returns the same IRSchema, ensures flags are set, and does not create a new object.
        """
        name = "DeepExisting"
        max_depth = 7
        from pyopenapi_gen import IRSchema

        stub = IRSchema(name=name)
        self.context.parsed_schemas[name] = stub
        schema = _handle_max_depth_exceeded(name, self.context, max_depth)
        assert schema is stub
        assert schema._is_circular_ref
        assert schema._from_unresolved_ref
        if schema._circular_ref_path is not None:
            assert "MAX_DEPTH_EXCEEDED" in schema._circular_ref_path

    def test_handle_cycle_detection__none_name__raises_assertion_error(self) -> None:
        """
        Scenario:
            - A cycle is detected with a None schema name.
        Expected Outcome:
            - Precondition of _handle_cycle_detection is original_name: str.
            - Passing None violates this. NameSanitizer would raise TypeError.
        """
        # _handle_cycle_detection expects original_name: str. Caller (_parse_schema) ensures this.
        # If called with None, NameSanitizer.sanitize_class_name(None) would raise TypeError.
        with self.assertRaises(TypeError):  # Expect TypeError from NameSanitizer
            _handle_cycle_detection(None, "None -> None", self.context)  # type: ignore

    def test_handle_max_depth_exceeded__none_name__creates_anonymous_placeholder(self) -> None:
        """
        Scenario:
            - Max recursion depth is exceeded with a None schema name.
        Expected Outcome:
            - Returns an anonymous IRSchema placeholder, no AssertionError raised.
        """
        # _handle_max_depth_exceeded correctly handles original_name=None.
        # It should return a valid IRSchema, not raise an AssertionError.
        schema = _handle_max_depth_exceeded(None, self.context, 5)
        self.assertIsNotNone(schema)
        self.assertIsNone(schema.name)  # Anonymous placeholder
        self.assertTrue(schema._is_circular_ref)
        self.assertTrue(schema._from_unresolved_ref)
        self.assertIn("[Maximum recursion depth", schema.description or "")  # Check part of the actual description
        self.assertIn("anonymous", schema.description or "")
        self.assertIsNotNone(schema._circular_ref_path)
        self.assertIn("MAX_DEPTH_EXCEEDED", schema._circular_ref_path or "")  # Correct place to check for this string
        self.assertTrue(self.context.cycle_detected)
