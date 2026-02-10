from pathlib import Path

import typer

from .core.spec_fetcher import is_url
from .generator.client_generator import ClientGenerator, GenerationError
from .ir import NamingStrategy


def main(
    spec: str = typer.Argument(..., help="Path or URL to OpenAPI spec"),
    project_root: Path = typer.Option(
        ...,
        "--project-root",
        help=(
            "Path to the directory containing your top-level Python packages. "
            "Generated code will be placed at project-root + output-package path."
        ),
    ),
    output_package: str = typer.Option(
        ..., "--output-package", help="Python package path for the generated client (e.g., 'pyapis.my_api_client')."
    ),
    force: bool = typer.Option(False, "-f", "--force", help="Overwrite without diff check"),
    no_postprocess: bool = typer.Option(False, "--no-postprocess", help="Skip post-processing (type checking, etc.)"),
    core_package: str | None = typer.Option(
        None,
        "--core-package",
        help=(
            "Python package path for the core package (e.g., 'pyapis.core'). "
            "If not set, defaults to <output-package>.core."
        ),
    ),
    naming_strategy: NamingStrategy = typer.Option(
        NamingStrategy.OPERATION_ID,
        "--naming-strategy",
        help=(
            "Strategy for deriving method names from operations. "
            "'operationId' (default) uses the spec's operationId field. "
            "'clean' strips auto-generated suffixes from frameworks like FastAPI. "
            "'path' ignores operationId and derives names from the HTTP method and path."
        ),
    ),
) -> None:
    """
    Generate a Python OpenAPI client from a spec file or URL.
    Only parses CLI arguments and delegates to ClientGenerator.
    """
    if core_package is None:
        core_package = output_package + ".core"
    generator = ClientGenerator()
    # Handle both URLs (pass as-is) and file paths (resolve to absolute)
    spec_path = spec if is_url(spec) else str(Path(spec).resolve())
    try:
        generator.generate(
            spec_path=spec_path,
            project_root=project_root,
            output_package=output_package,
            force=force,
            no_postprocess=no_postprocess,
            core_package=core_package,
            naming_strategy=naming_strategy,
        )
        typer.echo("Client generation complete.")
    except GenerationError as e:
        typer.echo(f"Generation failed: {e}", err=True)
        raise typer.Exit(code=1)


app = typer.Typer(help="PyOpenAPI Generator CLI - Generate Python clients from OpenAPI specs.")
app.command()(main)


if __name__ == "__main__":
    app()
