"""
Emitter for generating mock helper classes.

This module creates the mocks/ directory structure with mock implementations
for both tag-based endpoint clients and the main API client.
"""

import tempfile
import traceback
from collections import defaultdict
from pathlib import Path

from pyopenapi_gen import IROperation, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer

from ..visit.client_visitor import ClientVisitor
from ..visit.endpoint.endpoint_visitor import EndpointVisitor


class MocksEmitter:
    """Generates mock helper classes for testing."""

    def __init__(self, context: RenderContext) -> None:
        self.endpoint_visitor = EndpointVisitor()
        self.client_visitor = ClientVisitor()
        self.context = context

    def emit(self, spec: IRSpec, output_dir_str: str) -> list[str]:
        """
        Generate all mock files in mocks/ directory structure.

        Args:
            spec: IR specification
            output_dir_str: Output directory path

        Returns:
            List of generated file paths
        """
        error_log = Path(tempfile.gettempdir()) / "pyopenapi_gen_mocks_error.log"
        generated_files = []

        try:
            output_dir_abs = Path(output_dir_str)
            mocks_dir = output_dir_abs / "mocks"
            mocks_dir.mkdir(parents=True, exist_ok=True)

            # Group operations by tag
            operations_by_tag = self._group_operations_by_tag(spec)

            # Track tag information for main client generation
            tag_tuples = []

            # Generate mock endpoint classes
            mock_endpoints_dir = mocks_dir / "endpoints"
            mock_endpoints_dir.mkdir(parents=True, exist_ok=True)

            for tag, ops_for_tag in operations_by_tag.items():
                if not ops_for_tag:
                    continue

                canonical_tag_name = tag if tag else "default"
                class_name = NameSanitizer.sanitize_class_name(canonical_tag_name) + "Client"
                module_name = NameSanitizer.sanitize_module_name(canonical_tag_name)

                # Track for main client generation
                tag_tuples.append((canonical_tag_name, class_name, module_name))

                # Generate mock class
                mock_file_path = mock_endpoints_dir / f"mock_{module_name}.py"
                self.context.set_current_file(str(mock_file_path))

                mock_code = self.endpoint_visitor.generate_endpoint_mock_class(
                    canonical_tag_name, ops_for_tag, self.context
                )
                imports_code = self.context.render_imports()
                file_content = imports_code + "\n\n" + mock_code

                self.context.file_manager.write_file(str(mock_file_path), file_content)
                generated_files.append(str(mock_file_path))

            # Generate mock endpoints __init__.py
            endpoints_init_path = mock_endpoints_dir / "__init__.py"
            endpoints_init_content = self._generate_mock_endpoints_init(tag_tuples)
            self.context.file_manager.write_file(str(endpoints_init_path), endpoints_init_content)
            generated_files.append(str(endpoints_init_path))

            # Generate main mock client
            mock_client_path = mocks_dir / "mock_client.py"
            self.context.set_current_file(str(mock_client_path))

            mock_client_code = self.client_visitor.generate_client_mock_class(spec, self.context, tag_tuples)
            imports_code = self.context.render_imports()
            file_content = imports_code + "\n\n" + mock_client_code

            self.context.file_manager.write_file(str(mock_client_path), file_content)
            generated_files.append(str(mock_client_path))

            # Generate mocks __init__.py
            mocks_init_path = mocks_dir / "__init__.py"
            mocks_init_content = self._generate_mocks_init(tag_tuples)
            self.context.file_manager.write_file(str(mocks_init_path), mocks_init_content)
            generated_files.append(str(mocks_init_path))

            return generated_files

        except Exception as e:
            with open(error_log, "a") as f:
                f.write(f"ERROR in MocksEmitter.emit: {e}\n")
                f.write(traceback.format_exc())
            raise

    def _group_operations_by_tag(self, spec: IRSpec) -> dict[str, list[IROperation]]:
        """Group operations by their OpenAPI tag."""
        operations_by_tag: dict[str, list[IROperation]] = defaultdict(list)

        for operation in spec.operations:
            tag = operation.tags[0] if operation.tags else "default"
            operations_by_tag[tag].append(operation)

        return operations_by_tag

    def _generate_mock_endpoints_init(self, tag_tuples: list[tuple[str, str, str]]) -> str:
        """Generate __init__.py for mocks/endpoints/ directory."""
        lines = []
        lines.append('"""')
        lines.append("Mock endpoint clients for testing.")
        lines.append("")
        lines.append("Import mock classes to use as base classes for your test doubles.")
        lines.append('"""')
        lines.append("")

        # Import statements
        all_exports = []
        for tag, class_name, module_name in sorted(tag_tuples, key=lambda x: x[2]):
            mock_class_name = f"Mock{class_name}"
            lines.append(f"from .mock_{module_name} import {mock_class_name}")
            all_exports.append(mock_class_name)

        lines.append("")
        lines.append("__all__ = [")
        for export in all_exports:
            lines.append(f'    "{export}",')
        lines.append("]")

        return "\n".join(lines)

    def _generate_mocks_init(self, tag_tuples: list[tuple[str, str, str]]) -> str:
        """Generate __init__.py for mocks/ directory."""
        lines = []
        lines.append('"""')
        lines.append("Mock implementations for testing.")
        lines.append("")
        lines.append("These mocks implement the Protocol contracts without requiring")
        lines.append("network transport or authentication. Use them as base classes")
        lines.append("in your tests.")
        lines.append("")
        lines.append("Example:")
        lines.append("    from myapi.mocks import MockAPIClient, MockPetsClient")
        lines.append("")
        lines.append("    class TestPetsClient(MockPetsClient):")
        lines.append("        async def list_pets(self, limit: int | None = None) -> list[Pet]:")
        lines.append("            return [Pet(id=1, name='Test Pet')]")
        lines.append("")
        lines.append("    client = MockAPIClient(pets=TestPetsClient())")
        lines.append('"""')
        lines.append("")

        # Import main mock client
        lines.append("from .mock_client import MockAPIClient")

        # Import mock endpoint classes
        all_exports = ["MockAPIClient"]
        for tag, class_name, module_name in sorted(tag_tuples, key=lambda x: x[2]):
            mock_class_name = f"Mock{class_name}"
            lines.append(f"from .endpoints.mock_{module_name} import {mock_class_name}")
            all_exports.append(mock_class_name)

        lines.append("")
        lines.append("__all__ = [")
        for export in all_exports:
            lines.append(f'    "{export}",')
        lines.append("]")

        return "\n".join(lines)
