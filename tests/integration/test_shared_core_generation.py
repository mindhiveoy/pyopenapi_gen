"""Integration test for shared core package generation.

Tests that the generator correctly handles multi-client scenarios with shared core packages,
ensuring cattrs utilities are properly exported and BaseSchema references are removed.
"""

import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import generate_client


def test_shared_core__generates_cattrs_imports__not_baseschema() -> None:
    """Test shared core package exports cattrs utilities instead of BaseSchema.

    Scenario:
        - Generate first client with shared core package
        - Generate second client using the same core package
        - Verify both clients can import cattrs utilities
        - Verify no BaseSchema references exist

    Expected Outcome:
        - __init__.py imports from cattrs_converter module
        - structure_from_dict, unstructure_to_dict, converter are exported
        - No BaseSchema import or export
        - Both clients can use shared core package
    """
    # Arrange - Generate two clients in temporary directory
    spec_path = "input/business_swagger.json"
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Act - Generate first client with shared core
        generate_client(
            spec_path=spec_path,
            project_root=str(project_root),
            output_package="client_a",
            core_package="shared.core",
            force=True,
            no_postprocess=True,  # Skip formatting for speed
        )

        # Generate second client using same shared core
        generate_client(
            spec_path=spec_path,
            project_root=str(project_root),
            output_package="client_b",
            core_package="shared.core",
            force=True,
            no_postprocess=True,  # Skip formatting for speed
        )

        # Assert - Check client_a __init__.py
        client_a_init = project_root / "client_a" / "__init__.py"
        assert client_a_init.exists(), "client_a __init__.py should exist"

        client_a_content = client_a_init.read_text()

        # Should import cattrs utilities
        assert (
            "from shared.core.cattrs_converter import structure_from_dict" in client_a_content
        ), "client_a should import structure_from_dict from shared core"
        assert "unstructure_to_dict" in client_a_content, "client_a should import unstructure_to_dict"
        assert "converter" in client_a_content, "client_a should import converter"

        # Should NOT import BaseSchema
        assert "BaseSchema" not in client_a_content, "client_a should NOT reference BaseSchema"
        assert "schemas import" not in client_a_content, "client_a should NOT import from schemas module"

        # Should export cattrs utilities in __all__
        assert '"structure_from_dict"' in client_a_content, "client_a should export structure_from_dict"
        assert '"unstructure_to_dict"' in client_a_content, "client_a should export unstructure_to_dict"
        assert '"converter"' in client_a_content, "client_a should export converter"

        # Assert - Check client_b __init__.py
        client_b_init = project_root / "client_b" / "__init__.py"
        assert client_b_init.exists(), "client_b __init__.py should exist"

        client_b_content = client_b_init.read_text()

        # Should import cattrs utilities
        assert (
            "from shared.core.cattrs_converter import structure_from_dict" in client_b_content
        ), "client_b should import structure_from_dict from shared core"

        # Should NOT import BaseSchema
        assert "BaseSchema" not in client_b_content, "client_b should NOT reference BaseSchema"

        # Verify core package was only generated once
        core_dir = project_root / "shared" / "core"
        assert core_dir.exists(), "shared/core directory should exist"
        assert (core_dir / "cattrs_converter.py").exists(), "cattrs_converter.py should exist in shared core"
        assert not (core_dir / "schemas.py").exists(), "schemas.py should NOT exist in shared core"


def test_shared_core__init_structure__matches_expected_format() -> None:
    """Test that shared core __init__.py has correct structure.

    Scenario:
        - Generate client with shared core package
        - Inspect generated __init__.py

    Expected Outcome:
        - Imports section has cattrs_converter import
        - __all__ list has cattrs utilities
        - No deprecated BaseSchema references
    """
    spec_path = "input/business_swagger.json"
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Generate with shared core
        generate_client(
            spec_path=spec_path,
            project_root=str(project_root),
            output_package="myapi",
            core_package="myapi.core",
            force=True,
            no_postprocess=True,
        )

        # Read __init__.py
        init_file = project_root / "myapi" / "__init__.py"
        content = init_file.read_text()

        # Verify structure
        lines = content.split("\\n")

        # Find imports section
        import_lines = [line for line in lines if line.startswith("from myapi.core")]
        assert any("cattrs_converter" in line for line in import_lines), "Should have cattrs_converter import"
        assert not any("schemas" in line for line in import_lines), "Should NOT have schemas import"

        # Find __all__ section
        all_section = "\\n".join(lines[lines.index("__all__ = [") :])
        assert "structure_from_dict" in all_section, "__all__ should contain structure_from_dict"
        assert "unstructure_to_dict" in all_section, "__all__ should contain unstructure_to_dict"
        assert "converter" in all_section, "__all__ should contain converter"
        assert "BaseSchema" not in all_section, "__all__ should NOT contain BaseSchema"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
