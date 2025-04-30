import os

import pytest
from pyopenapi_gen.context.render_context import RenderContext


@pytest.fixture
def context() -> RenderContext:
    ctx = RenderContext()
    return ctx


def set_file(ctx: RenderContext, rel_path: str) -> None:
    # Simulate setting the current file being rendered
    root = os.path.abspath("/fake/out")
    ctx.set_current_file(os.path.join(root, rel_path))


@pytest.mark.parametrize(
    "current_file,module,symbol,expected",
    [
        # Endpoints importing from models
        (
            "endpoints/agent_datasources.py",
            "models.foo",
            "Bar",
            "from ..models.foo import Bar",
        ),
        # Endpoints importing from another endpoint
        (
            "endpoints/agent_datasources.py",
            "endpoints.pets",
            "PetsClient",
            "from .pets import PetsClient",
        ),
        # Models importing from models
        ("models/foo.py", "models.bar", "Baz", "from .bar import Baz"),
        # Client importing from endpoints
        (
            "client.py",
            "endpoints.pets",
            "PetsClient",
            "from .endpoints.pets import PetsClient",
        ),
        # External import
        (
            "endpoints/agent_datasources.py",
            "requests",
            "Session",
            "from requests import Session",
        ),
    ],
)
def test_add_import_logic(context: RenderContext, current_file: str, module: str, symbol: str, expected: str) -> None:
    set_file(context, current_file)
    context.add_import(module, symbol)
    imports = context.render_imports("/fake/out")
    # Remove whitespace and split lines for comparison
    lines = [line.strip() for line in imports.splitlines() if line.strip()]
    assert any(expected in line for line in lines), f"Expected '{expected}' in imports: {lines}"


def test_render_imports__endpoint_to_models__double_dot() -> None:
    """
    Scenario:
        - Simulate an endpoint file context and add a models import.
        - Render imports for the file.
    Expected Outcome:
        - The rendered imports include 'from ..models.foo import Bar'.
    """
    ctx = RenderContext()
    # Simulate being in an endpoint file
    root = os.path.abspath("/fake/out")
    ctx.set_current_file(os.path.join(root, "endpoints/agent_datasources.py"))
    ctx.add_import("models.foo", "Bar")
    imports = ctx.render_imports("/fake/out/endpoints")
    assert "from ..models.foo import Bar" in imports
