import difflib
from pathlib import Path
from typing import Any

import typer
import yaml

from .core.loader import load_ir_from_spec
from .emitters.docs_emitter import DocsEmitter
from .generator.client_generator import ClientGenerator, GenerationError

app = typer.Typer(invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context) -> None:
    """
    PyOpenAPI Generator CLI.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def _load_spec(path_or_url: str) -> dict[str, Any] | Any:
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
            diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=str(old_file), tofile=str(new_file)))
            if diff:
                has_diff = True
                typer.echo("\n".join(diff))
    return has_diff


@app.command()
def gen(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec"),
    output: Path = typer.Option(..., "-o", "--output", help="Output directory"),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite without diff check"),
    name: str = typer.Option(None, "-n", "--name", help="Custom client package name"),
    docs: bool = typer.Option(False, help="Also generate docs"),
    telemetry: bool = typer.Option(False, help="Enable telemetry"),
    auth: str = typer.Option(None, help="Auth plugins comma-separated"),
    no_postprocess: bool = typer.Option(False, "--no-postprocess", help="Skip post-processing (type checking, etc.)"),
    core_package: str = typer.Option("core", "--core-package", help="Name of the core package/folder (default: core)"),
) -> None:
    """
    Generate a Python OpenAPI client from a spec file or URL.
    This function only parses CLI arguments and delegates to ClientGenerator.
    """
    generator = ClientGenerator()
    try:
        generator.generate(
            spec_path=spec,
            output=output,
            force=force,
            name=name,
            docs=docs,
            telemetry=telemetry,
            auth=auth,
            no_postprocess=no_postprocess,
            core_package=core_package,
        )
        typer.echo("Client generation complete.")
    except GenerationError as e:
        typer.echo(f"Generation failed: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def docs(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec"),
    output: Path = typer.Option(..., "-o", "--output", help="Docs output dir"),
) -> None:
    """Generate documentation from an OpenAPI spec."""
    # Load and convert spec
    spec_dict = _load_spec(spec)
    ir = load_ir_from_spec(spec_dict)
    # Emit markdown docs
    DocsEmitter().emit(ir, str(output))
    typer.echo("Documentation generation complete.")


if __name__ == "__main__":
    app()
