from pathlib import Path
from typer.testing import CliRunner

from pyopenapi_gen.cli import app


def test_business_swagger_generation(tmp_path: Path) -> None:
    """End-to-end test: generate client for the business_swagger.json spec and verify output files."""
    # Copy the provided business_swagger.json into a temporary spec file
    spec_source = Path(__file__).parent.parent / "input" / "business_swagger.json"
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(spec_source.read_text())

    out_dir = tmp_path / "out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["gen", str(spec_file), "-o", str(out_dir), "--force"],
    )
    # CLI should succeed
    assert result.exit_code == 0, result.stdout

    # Check core files
    assert (out_dir / "config.py").exists(), "config.py not generated"
    assert (out_dir / "client.py").exists(), "client.py not generated"

    # Check endpoints directory and modules
    endpoints_dir = out_dir / "endpoints"
    assert endpoints_dir.exists(), "endpoints directory not generated"
    assert (endpoints_dir / "__init__.py").exists(), "__init__.py missing in endpoints"
    py_files = [p for p in endpoints_dir.glob("*.py") if p.name != "__init__.py"]
    assert py_files, "no endpoint modules generated"
