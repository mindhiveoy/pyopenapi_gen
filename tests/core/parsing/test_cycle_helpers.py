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
        schema = _handle_cycle_detection(name, cycle_path, self.context, allow_self_reference=False)
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
        schema = _handle_cycle_detection(name, cycle_path, self.context, allow_self_reference=False)
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
        assert schema._max_depth_exceeded_marker, "Should be marked for max depth exceeded"
        assert not schema._is_circular_ref, "Should NOT be marked as circular for only max depth"
        assert not schema._from_unresolved_ref, "Should NOT be marked as unresolved for only max depth"
        assert schema._circular_ref_path is None, "Circular ref path should not be set for only max depth"
        assert schema.description is not None, "Description should be set for max depth exceeded"
        assert f"Maximum recursion depth ({max_depth}) exceeded" in schema.description
        assert self.context.parsed_schemas[name] is schema
        assert not self.context.cycle_detected, "Context cycle_detected should NOT be true for only max depth"

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
        assert schema._max_depth_exceeded_marker, "Should be marked for max depth exceeded on existing stub"
        assert not stub._is_circular_ref, "Existing stub should NOT become circular for only max depth"
        assert not stub._from_unresolved_ref, "Existing stub should NOT become unresolved for only max depth"
        assert stub._circular_ref_path is None, "Existing stub circular path should remain None for only max depth"
        assert schema.description is not None, "Description should be updated for max depth exceeded on existing stub"
        assert f"Maximum recursion depth ({max_depth}) exceeded" in schema.description
        assert not self.context.cycle_detected, "Context cycle_detected should NOT be true for only max depth"

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
        self.assertTrue(schema._max_depth_exceeded_marker, "Anonymous placeholder should be marked for max depth")
        self.assertFalse(schema._is_circular_ref, "Anonymous placeholder should NOT be circular for max depth")
        self.assertFalse(schema._from_unresolved_ref, "Anonymous placeholder should NOT be unresolved for max depth")
        self.assertIsNone(schema._circular_ref_path, "Anonymous placeholder should have no circular path for max depth")
        self.assertIn("[Maximum recursion depth", schema.description or "")
        self.assertIn("anonymous", schema.description or "")
        self.assertFalse(self.context.cycle_detected, "Context cycle_detected should NOT be true for only max depth")

    def test_handle_cycle_detection__allow_self_reference_true__direct_cycle__creates_stub(self) -> None:
        """
        Scenario:
            - A direct self-reference cycle is detected for a new schema name.
            - allow_self_reference is True.
        Expected Outcome:
            - Returns an IRSchema marked as a self-referential stub, not a full error cycle.
            - Registers it in context.
            - context.cycle_detected should NOT be True from this specific call.
        """
        name = "SelfRefSchema"
        cycle_path = "SelfRefSchema -> SelfRefSchema"  # Path indicating direct self-ref
        # Pre-condition: context.cycle_detected might be False or True from other operations
        initial_cycle_detected_state = self.context.cycle_detected

        schema = _handle_cycle_detection(name, cycle_path, self.context, allow_self_reference=True)

        assert schema.name == name
        assert not schema._is_circular_ref, "Should not be marked as a full error cycle"
        assert not schema._from_unresolved_ref, "Should not be marked as unresolved in error sense"
        assert getattr(schema, "_is_self_referential_stub", False), "Should be marked as a self-referential stub"
        assert self.context.parsed_schemas[name] is schema
        # Check that this specific call did not set context.cycle_detected to True if it wasn't already
        # (though other indirect cycles might still set it)
        # For a direct self-reference handled as a stub, it shouldn't set it.
        if not initial_cycle_detected_state:
            assert not self.context.cycle_detected, (
                "context.cycle_detected should not be set by a permitted self-ref stub creation"
            )

    def test_handle_cycle_detection__allow_self_reference_true__existing_stub__returns_stub(self) -> None:
        """
        Scenario:
            - A direct self-reference cycle is detected for a schema name already in context as a stub.
            - allow_self_reference is True.
        Expected Outcome:
            - Returns the existing stub, ensures it's marked appropriately.
        """
        from pyopenapi_gen import IRSchema

        name = "SelfRefStubSchema"
        cycle_path = "SelfRefStubSchema -> SelfRefStubSchema"

        # Pre-populate context with a stub that might have been created by a forward reference
        existing_stub = IRSchema(name=name, _is_self_referential_stub=True)
        self.context.parsed_schemas[name] = existing_stub

        schema = _handle_cycle_detection(name, cycle_path, self.context, allow_self_reference=True)

        assert schema is existing_stub
        assert not schema._is_circular_ref
        assert getattr(schema, "_is_self_referential_stub", False)

    def test_handle_cycle_detection__allow_self_reference_true__indirect_cycle__marks_as_error(self) -> None:
        """
        Scenario:
            - An indirect cycle is detected (A -> B -> A).
            - allow_self_reference is True.
        Expected Outcome:
            - Even with allow_self_reference=True, indirect cycles are still treated as errors.
            - Returns an IRSchema marked as circular.
        """
        name = "IndirectCycleStart"
        cycle_path = "IndirectCycleStart -> OtherSchema -> IndirectCycleStart"  # Path indicating indirect cycle

        schema = _handle_cycle_detection(name, cycle_path, self.context, allow_self_reference=True)

        assert schema.name == name
        assert schema._is_circular_ref, "Indirect cycle should still be marked as an error cycle"
        assert schema._from_unresolved_ref
        assert schema._circular_ref_path == cycle_path
        assert self.context.parsed_schemas[name] is schema
        assert self.context.cycle_detected, "context.cycle_detected should be set for indirect error cycles"
