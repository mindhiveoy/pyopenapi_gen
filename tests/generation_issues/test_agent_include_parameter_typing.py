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
        """Test that get_agent method has correct typing for include parameter."""
        # Generate the client
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(self.test_spec_path),
            project_root=self.temp_dir,
            output_package="test_client",
            force=True,
            no_postprocess=True,  # Skip to avoid external dependencies
        )

        # Read the generated agents client file
        agents_module_path = self.temp_dir / "test_client" / "endpoints" / "agents.py"
        self.assertTrue(agents_module_path.exists(), "Agents module should be generated")

        with open(agents_module_path, "r") as f:
            agents_code = f.read()

        # Check that get_agent method exists
        self.assertIn("async def get_agent(", agents_code, "get_agent method should be generated")

        # Check the current (incorrect) typing - this should fail once we fix the issue
        current_incorrect_typing = "include: Optional[List[AnonymousArrayItem]]"
        expected_correct_typing = "include: Optional[List[str]]"

        if current_incorrect_typing in agents_code:
            self.fail(
                f"DETECTED ISSUE: The include parameter is incorrectly typed as '{current_incorrect_typing}'. "
                f"It should be '{expected_correct_typing}' to match the OpenAPI spec which defines it as "
                f"an array of strings with enum values: "
                f"['tenant', 'agentSettings', 'credentials', 'dataSourceConnections']"
            )

        # If the fix has been applied, check for the correct typing
        self.assertIn(
            expected_correct_typing,
            agents_code,
            f"include parameter should be typed as '{expected_correct_typing}' but was not found in generated code",
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

            # AnonymousArrayItem should be related to chat messages, not include parameters
            self.assertIn("message", content.lower(), "AnonymousArrayItem appears to be a message-related type")
            self.assertIn("role", content.lower(), "AnonymousArrayItem appears to be a message-related type with role")

            # It should NOT be used for include parameters
            # This test documents the current incorrect behavior


if __name__ == "__main__":
    unittest.main()
