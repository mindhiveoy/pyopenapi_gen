import os

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..visit.docs_visitor import DocsVisitor

"""Simple documentation emitter using markdown with Python str.format placeholders."""
DOCS_INDEX_TEMPLATE = """# API Documentation

Generated documentation for the API.

## Tags
{tags_list}
"""

DOCS_TAG_TEMPLATE = """# {tag} Operations

{operations_list}
"""

DOCS_OPERATION_TEMPLATE = """### {operation_id}

**Method:** `{method}`
**Path:** `{path}`

{description}
"""


class DocsEmitter:
    """Generates markdown documentation per tag from IRSpec using visitor/context."""

    def __init__(self) -> None:
        self.visitor = DocsVisitor()

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        """Render docs into <output_dir> as markdown files."""
        docs_dir = os.path.join(output_dir)
        context = RenderContext()
        context.file_manager.ensure_dir(docs_dir)
        docs = self.visitor.visit(spec, context)
        for filename, content in docs.items():
            context.file_manager.write_file(os.path.join(docs_dir, filename), content)
