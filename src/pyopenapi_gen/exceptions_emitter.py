from jinja2 import Environment
import os
from . import IRSpec

# Template for spec-specific exception aliases
EXCEPTIONS_ALIASES_TEMPLATE = '''
from .exceptions import HTTPError, ClientError, ServerError

# Generated exception aliases for specific status codes
{% for code in codes %}
class Error{{ code }}({% if code < 500 %}ClientError{% else %}ServerError{% endif %}):
    """Exception alias for HTTP {{ code }} responses."""
    pass
{% endfor %}
'''


class ExceptionsEmitter:
    """Generates spec-specific exception aliases in exceptions.py"""

    def __init__(self) -> None:
        self.env = Environment(trim_blocks=True, lstrip_blocks=True)

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        # Prepare output file path for exceptions alias file
        file_path = os.path.join(output_dir, "exceptions.py")
        # Collect unique numeric status codes
        codes = sorted(
            {
                int(resp.status_code)
                for op in spec.operations
                for resp in op.responses
                if resp.status_code.isdigit()
            }
        )
        # Render template
        template = self.env.from_string(EXCEPTIONS_ALIASES_TEMPLATE)
        content = template.render(codes=codes)
        # Write file
        os.makedirs(output_dir, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
