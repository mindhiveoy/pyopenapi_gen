from pyopenapi_gen import IRSpec

from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer
from ..core.writers.code_writer import CodeWriter


class DocsVisitor:
    """Visitor for rendering markdown documentation from IRSpec."""

    def visit(self, spec: IRSpec, context: RenderContext) -> dict[str, str]:
        # List tags
        tags = sorted({t for op in spec.operations for t in op.tags})
        # Generate index.md with sanitized links
        writer = CodeWriter()
        writer.write_line("# API Documentation\n")
        writer.write_line("Generated documentation for the API.\n")
        writer.write_line("## Tags")
        for tag in tags:
            writer.write_line(f"- [{tag}]({NameSanitizer.sanitize_module_name(tag)}.md)")
        index_content = writer.get_code()
        result = {"index.md": index_content}
        # Generate docs per tag
        for tag in tags:
            ops = [op for op in spec.operations if tag in op.tags]
            tag_writer = CodeWriter()
            tag_writer.write_line(f"# {tag.capitalize()} Operations\n")
            for op in ops:
                tag_writer.write_line(f"### {op.operation_id}\n")
                tag_writer.write_line(f"**Method:** `{op.method.value}`  ")
                tag_writer.write_line(f"**Path:** `{op.path}`  \n")
                desc = op.description or ""
                if desc:
                    tag_writer.write_line(desc)
                tag_writer.write_line("")
            filename = NameSanitizer.sanitize_module_name(tag) + ".md"
            result[filename] = tag_writer.get_code()
        return result
