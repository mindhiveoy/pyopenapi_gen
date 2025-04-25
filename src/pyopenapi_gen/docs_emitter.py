import os

from . import IRSpec
from .utils import NameSanitizer

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
    """Generates markdown documentation per tag from IRSpec."""

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        """Render docs into <output_dir> as markdown files."""
        # Create docs directory
        docs_dir = os.path.join(output_dir)
        os.makedirs(docs_dir, exist_ok=True)

        # List tags
        tags = sorted({t for op in spec.operations for t in op.tags})

        # Generate index.md with sanitized links
        tags_list = "\n".join(
            f"- [{tag}]({NameSanitizer.sanitize_module_name(tag)}.md)" for tag in tags
        )
        index_content = DOCS_INDEX_TEMPLATE.format(tags_list=tags_list)
        with open(os.path.join(docs_dir, "index.md"), "w") as f:
            f.write(index_content)

        # Generate docs per tag
        for tag in tags:
            ops = [op for op in spec.operations if tag in op.tags]
            operations_list = ""
            for op in ops:
                desc = op.description or ""
                operations_list += (
                    DOCS_OPERATION_TEMPLATE.format(
                        operation_id=op.operation_id,
                        method=op.method.value,
                        path=op.path,
                        description=desc,
                    )
                    + "\n"
                )
            tag_content = DOCS_TAG_TEMPLATE.format(
                tag=tag.capitalize(), operations_list=operations_list
            )
            filename = NameSanitizer.sanitize_module_name(tag) + ".md"
            with open(os.path.join(docs_dir, filename), "w") as f:
                f.write(tag_content)
