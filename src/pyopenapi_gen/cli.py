from pathlib import Path
from typing import Any

import typer
import yaml

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


@app.command()
def gen(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec"),
    project_root: Path = typer.Option(
        ...,
        "--project-root",
        help="Path to the directory containing your top-level Python packages. Generated code will be placed at project-root + output-package path.",
    ),
    output_package: str = typer.Option(
        ..., "--output-package", help="Python package path for the generated client (e.g., 'pyapis.my_api_client')."
    ),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite without diff check"),
    no_postprocess: bool = typer.Option(False, "--no-postprocess", help="Skip post-processing (type checking, etc.)"),
    core_package: str | None = typer.Option(
        None,
        "--core-package",
        help="Python package path for the core package (e.g., 'pyapis.core'). If not set, defaults to <output-package>.core.",
    ),
) -> None:
    """
    Generate a Python OpenAPI client from a spec file or URL.
    Only parses CLI arguments and delegates to ClientGenerator.
    """
    if core_package is None:
        core_package = output_package + ".core"
    generator = ClientGenerator()
    try:
        generator.generate(
            spec_path=str(Path(spec).resolve()),
            project_root=project_root,
            output_package=output_package,
            force=force,
            no_postprocess=no_postprocess,
            core_package=core_package,
        )
        typer.echo("Client generation complete.")
    except GenerationError as e:
        typer.echo(f"Generation failed: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
