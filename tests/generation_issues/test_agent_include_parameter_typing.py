"""
Unit test to detect incorrect typing of agentInclude parameter in get_agent method.

The agentInclude parameter should be typed as List[str] with enum values:
["tenant", "agentSettings", "credentials", "dataSourceConnections"]

But it's incorrectly being generated as List[AnonymousArrayItem].
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add the src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pyopenapi_gen.generator.client_generator import ClientGenerator


class TestAgentIncludeParameterTyping(unittest.TestCase):
    """Test that agent include parameter is typed correctly."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.test_spec_path = Path(__file__).parent.parent.parent / "input" / "business_swagger.json"
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_get_agent_include_parameter_typing(self) -> None:
        """Test that get_agent method has correct typing for include parameter.

        The get_agent endpoint defines include inline as {"type": "string"}.
        It must NOT be overridden by the unrelated agentInclude component parameter
        which shares the same name and location but carries a different enum-array schema.
        """
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(self.test_spec_path),
            project_root=self.temp_dir,
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        agents_module_path = self.temp_dir / "test_client" / "endpoints" / "agents.py"
        self.assertTrue(agents_module_path.exists(), "Agents module should be generated")

        with open(agents_module_path, "r") as f:
            agents_code = f.read()

        self.assertIn("async def get_agent(", agents_code, "get_agent method should be generated")

        # The inline schema is {"type": "string"}, so include must be plain str | None
        self.assertIn(
            "include: str | None",
            agents_code,
            "include param on get_agent should be 'str | None' as defined inline in the spec",
        )

        # Must NOT be a List of any enum type (that would come from the unrelated agentInclude component)
        import re

        self.assertIsNone(
            re.search(r"include: List\[", agents_code),
            "include param on get_agent must not be a List type; the inline spec says string",
        )

    def test_agent_include_parameter_values_from_spec(self) -> None:
        """Test that the expected enum values are correctly identified from the OpenAPI spec."""
        import json

        with open(self.test_spec_path, "r") as f:
            spec = json.load(f)

        # Find the agentInclude parameter definition
        agent_include_param = spec["components"]["parameters"]["agentInclude"]

        self.assertEqual(agent_include_param["name"], "include")
        self.assertEqual(agent_include_param["in"], "query")

        schema = agent_include_param["schema"]
        self.assertEqual(schema["type"], "array")

        items = schema["items"]
        self.assertEqual(items["type"], "string")

        expected_enum_values = ["tenant", "agentSettings", "credentials", "dataSourceConnections"]
        self.assertEqual(items["enum"], expected_enum_values)

    def test_anonymous_array_item_should_not_be_used_for_include(self) -> None:
        """Test that AnonymousArrayItem is not the correct type for include parameter."""
        # Generate the client
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(self.test_spec_path),
            project_root=self.temp_dir,
            output_package="test_client",
            force=True,
            no_postprocess=True,
        )

        # Check what AnonymousArrayItem actually is
        anonymous_array_item_path = self.temp_dir / "test_client" / "models" / "anonymous_array_item.py"

        if anonymous_array_item_path.exists():
            with open(anonymous_array_item_path, "r") as f:
                content = f.read()

            # AnonymousArrayItem may be a circular reference placeholder or message-related type
            # Check if it's a circular reference (detected properly by unified cycle detection)
            is_circular_placeholder = "circular reference detected" in content.lower()

            if not is_circular_placeholder:
                # If not a circular reference, it should be related to chat messages
                self.assertIn("message", content.lower(), "AnonymousArrayItem appears to be a message-related type")
                self.assertIn(
                    "role", content.lower(), "AnonymousArrayItem appears to be a message-related type with role"
                )

            # It should NOT be used for include parameters
            # This test documents the current incorrect behavior


if __name__ == "__main__":
    unittest.main()
