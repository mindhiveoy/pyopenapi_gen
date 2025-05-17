# Initialize the parsing module

# Expose the main schema parsing entry point if desired,
# otherwise, it remains internal (_parse_schema).
# from .schema_parser import _parse_schema as parse_openapi_schema_node

# Other parsers can be imported here if they need to be part of the public API
# of this sub-package, though most are internal helpers for _parse_schema.
from typing import List

__all__: List[str] = [
    # "parse_openapi_schema_node", # Example if we were to expose it
]
