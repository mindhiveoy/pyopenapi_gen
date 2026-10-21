from pathlib import Path

import typer
from datamodel_code_generator.preset import PresetName

from pyopenapi_gen.emitters.models_emitter import DEFAULT_PYTHON_MODEL_PRESET

from .core.spec_fetcher import is_url
from .generator.client_generator import ClientGenerator, GenerationError
from .ir import ModelBackend, ModelType, NamingStrategy


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
    model_backend: ModelBackend = typer.Option(
        ModelBackend.LEGACY,
        "--model-backend",
        help=(
            "Implementation that renders the models package. "
            "'legacy' (default) uses the built-in generators. "
            "'dcg' (experimental) renders models with datamodel-code-generator."
        ),
    ),
    model_type: ModelType = typer.Option(
        ModelType.DATACLASS,
        "--model-type",
        help=(
            "Kind of class generated for object schemas; requires '--model-backend dcg' for anything but "
            "'dataclass'. 'dataclass' (default) generates standard-library dataclasses. "
            "'pydantic' generates pydantic v2 models; the generated client then requires 'pydantic>=2'."
        ),
    ),
    model_python_preset: PresetName | None = typer.Option(
        None,
        "--model-python-preset",
        help=(
            "Name of a datamodel-code-generator built-in preset (its '--preset' option), e.g. "
            "'standard-py310-20260909'; requires '--model-backend dcg', which defaults to "
            f"'{DEFAULT_PYTHON_MODEL_PRESET.value}'. The preset's Python version replaces the default 3.10 "
            "target; options this tool fixes take precedence over the preset."
        ),
        autocompletion=lambda: tuple(map(lambda c: c.value, PresetName)),
    ),
) -> None:
    """
    Generate a Python OpenAPI client from a spec file or URL.
    Only parses CLI arguments and delegates to ClientGenerator.
    """
    if model_type is ModelType.PYDANTIC and model_backend is not ModelBackend.DCG:
        raise typer.BadParameter("'--model-type pydantic' requires '--model-backend dcg'.", param_hint="--model-type")
    if model_python_preset is not None and model_backend is not ModelBackend.DCG:
        raise typer.BadParameter(
            "'--model-python-preset' requires '--model-backend dcg'.", param_hint="--model-python-preset"
        )
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
            model_backend=model_backend,
            model_type=model_type,
            model_python_preset=model_python_preset,
        )
        typer.echo("Client generation complete.")
    except GenerationError as e:
        typer.echo(f"Generation failed: {e}", err=True)
        raise typer.Exit(code=1)


app = typer.Typer(help="PyOpenAPI Generator CLI - Generate Python clients from OpenAPI specs.")
app.command()(main)


if __name__ == "__main__":
    app()
