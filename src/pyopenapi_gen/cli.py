from pathlib import Path
import tempfile
import shutil
import difflib
import yaml
import typer
from typing import Any

from .loader import load_ir_from_spec
from .models_emitter import ModelsEmitter
from .endpoints_emitter import EndpointsEmitter
from .client_emitter import ClientEmitter
from .docs_emitter import DocsEmitter
from .warning_collector import WarningCollector

app = typer.Typer()


def _load_spec(path_or_url: str) -> dict[str, Any]:
    """Load a spec from a file path or URL."""
    if Path(path_or_url).exists():
        return yaml.safe_load(Path(path_or_url).read_text())
    typer.echo("URL loading not implemented", err=True)
    raise typer.Exit(code=1)


def _show_diffs(old_dir: str, new_dir: str) -> bool:
    """Compare two directories and print diffs, returning True if any differences."""
    has_diff = False
    for new_file in Path(new_dir).rglob("*.py"):
        old_file = Path(old_dir) / new_file.relative_to(new_dir)
        if old_file.exists():
            old_lines = old_file.read_text().splitlines()
            new_lines = new_file.read_text().splitlines()
            diff = list(
                difflib.unified_diff(
                    old_lines, new_lines, fromfile=str(old_file), tofile=str(new_file)
                )
            )
            if diff:
                has_diff = True
                typer.echo("\n".join(diff))
    return has_diff


@app.command()
def gen(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec"),
    output: Path = typer.Option(..., "-o", "--output", help="Output directory"),
    force: bool = typer.Option(
        False, "-f", "--force", help="Overwrite without diff check"
    ),
    name: str = typer.Option(None, "-n", "--name", help="Custom client package name"),
    docs: bool = typer.Option(False, help="Also generate docs"),
    telemetry: bool = typer.Option(False, help="Enable telemetry"),
    auth: str = typer.Option(None, help="Auth plugins comma-separated"),
):
    """Generate a Python client from an OpenAPI spec."""
    # Load and convert spec to IR
    spec_dict = _load_spec(spec)
    ir = load_ir_from_spec(spec_dict)
    # Collect and display warnings without stopping generation
    collector = WarningCollector()
    reports = collector.collect(ir)
    for report in reports:
        typer.secho(
            f"WARNING [{report.code}]: {report.message} (Hint: {report.hint})",
            fg="yellow",
            err=True,
        )

    out_dir = str(output)
    # Prepare backup variable for diff check
    backup = None

    # Backup existing output for diff checking
    if output.exists() and not force:
        backup = tempfile.mkdtemp()
        shutil.copytree(out_dir, backup, dirs_exist_ok=True)

    # Prepare output directory
    if output.exists():
        shutil.rmtree(out_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Emit code
    ModelsEmitter().emit(ir, out_dir)
    EndpointsEmitter().emit(ir, out_dir)
    ClientEmitter().emit(ir, out_dir)

    # If we created a backup, show diffs and exit non-zero on changes
    if backup:
        if _show_diffs(backup, out_dir):
            raise typer.Exit(code=1)

    typer.echo("Client generation complete.")


@app.command()
def docs(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec"),
    output: Path = typer.Option(..., "-o", "--output", help="Docs output dir"),
):
    """Generate documentation from an OpenAPI spec."""
    # Load and convert spec
    spec_dict = _load_spec(spec)
    ir = load_ir_from_spec(spec_dict)
    # Emit markdown docs
    DocsEmitter().emit(ir, str(output))
    typer.echo("Documentation generation complete.")


if __name__ == "__main__":
    app()
