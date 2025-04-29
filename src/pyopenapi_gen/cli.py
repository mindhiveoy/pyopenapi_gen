from pathlib import Path
import tempfile
import shutil
import difflib
import yaml
import typer
from typing import Any
import subprocess
import sys
import os

from .core.loader import load_ir_from_spec
from .emitters.models_emitter import ModelsEmitter
from .emitters.endpoints_emitter import EndpointsEmitter
from .emitters.client_emitter import ClientEmitter
from .emitters.docs_emitter import DocsEmitter
from .emitters.config_emitter import ConfigEmitter
from pyopenapi_gen.core.warning_collector import WarningCollector

app = typer.Typer(invoke_without_command=True)


@app.callback()
def main(ctx: typer.Context):
    """
    PyOpenAPI Generator CLI.
    """
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


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
    no_postprocess: bool = typer.Option(
        False, "--no-postprocess", help="Skip post-processing (type checking, etc.)"
    ),
):
    print(f"[DEBUG] gen() called. Output directory: {output}")
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

    if not force and output.exists():
        # Generate to a temp directory, diff, and only overwrite if no changes
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_output = Path(tmpdir) / "out"
            tmp_output.mkdir(parents=True, exist_ok=True)
            # Always create an empty __init__.py at the root of the output directory
            root_init_path = tmp_output / "__init__.py"
            if not root_init_path.exists():
                root_init_path.write_text("")
            # Emit code to temp dir
            ModelsEmitter().emit(ir, str(tmp_output))
            EndpointsEmitter().emit(ir, str(tmp_output))
            ConfigEmitter().emit(str(tmp_output))
            ClientEmitter().emit(ir, str(tmp_output))
            # Run post-processing script to check types and clean imports
            if not no_postprocess:
                postprocess_script = (
                    Path(__file__).parent.parent.parent / "postprocess_generated.py"
                )
                if postprocess_script.exists():
                    typer.echo("Running post-processing on generated code...")
                    env = os.environ.copy()
                    env["PYTHONPATH"] = str(tmp_output.parent.resolve())
                    result = subprocess.run(
                        [sys.executable, str(postprocess_script)],
                        capture_output=True,
                        text=True,
                        env=env,
                    )
                    if result.stdout:
                        typer.echo(result.stdout)
                    if result.stderr:
                        typer.echo(result.stderr, err=True)
                    if result.returncode != 0:
                        typer.echo("Post-processing failed.", err=True)
                        raise typer.Exit(code=result.returncode)
                else:
                    typer.echo(
                        f"Warning: {postprocess_script} not found. Skipping post-processing.",
                        err=True,
                    )
            # Diff temp output with existing output
            has_diff = _show_diffs(str(output), str(tmp_output))
            if has_diff:
                raise typer.Exit(code=1)
            # No diff, overwrite output
            shutil.rmtree(out_dir)
            shutil.copytree(str(tmp_output), out_dir)
    else:
        # Always clean output directory before generation if --force or not exists
        if output.exists():
            shutil.rmtree(out_dir)
        output.mkdir(parents=True, exist_ok=True)
        # Always create an empty __init__.py at the root of the output directory
        root_init_path = output / "__init__.py"
        if not root_init_path.exists():
            root_init_path.write_text("")
        # Emit code
        ModelsEmitter().emit(ir, out_dir)
        EndpointsEmitter().emit(ir, out_dir)
        ConfigEmitter().emit(out_dir)
        ClientEmitter().emit(ir, out_dir)
        # Run post-processing script to check types and clean imports
        if not no_postprocess:
            postprocess_script = (
                Path(__file__).parent.parent.parent / "postprocess_generated.py"
            )
            if postprocess_script.exists():
                typer.echo("Running post-processing on generated code...")
                env = os.environ.copy()
                env["PYTHONPATH"] = str(output.parent.resolve())
                result = subprocess.run(
                    [sys.executable, str(postprocess_script)],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                if result.stdout:
                    typer.echo(result.stdout)
                if result.stderr:
                    typer.echo(result.stderr, err=True)
                if result.returncode != 0:
                    typer.echo("Post-processing failed.", err=True)
                    raise typer.Exit(code=result.returncode)
            else:
                typer.echo(
                    f"Warning: {postprocess_script} not found. Skipping post-processing.",
                    err=True,
                )
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
