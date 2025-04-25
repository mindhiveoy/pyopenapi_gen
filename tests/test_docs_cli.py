from pathlib import Path
from typer.testing import CliRunner
import json

from pyopenapi_gen.cli import app

# Minimal spec with tags for docs generation
DOC_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Docs API", "version": "1.0.0"},
    "paths": {
        "/items": {
            "get": {
                "operationId": "list_items",
                "summary": "List items",
                "responses": {"200": {"description": "OK"}},
                "tags": ["items"],
            }
        }
    },
}


def test_docs_cli_generates_markdown(tmp_path: Path) -> None:
    """Test that the 'docs' CLI generates index and per-tag markdown files."""
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(DOC_SPEC))
    out_dir = tmp_path / "docs_out"
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["docs", str(spec_file), "-o", str(out_dir)],
    )
    assert result.exit_code == 0, result.stdout

    # Confirm index.md and tag-specific docs
    index_md = out_dir / "index.md"
    items_md = out_dir / "items.md"
    assert index_md.exists(), "index.md not generated"
    assert items_md.exists(), "items.md not generated"

    index_content = index_md.read_text()
    assert "# API Documentation" in index_content
    assert "- [items](items.md)" in index_content

    items_content = items_md.read_text()
    assert "### list_items" in items_content
    assert "**Method:** `GET`" in items_content
    assert "**Path:** `/items`" in items_content
