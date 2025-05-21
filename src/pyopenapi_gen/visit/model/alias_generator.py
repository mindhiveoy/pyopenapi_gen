"""
Generates Python code for type aliases from IRSchema objects.
"""

import logging
from typing import Dict, Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.helpers.type_helper import TypeHelper
from pyopenapi_gen.helpers.type_resolution.finalizer import TypeFinalizer

logger = logging.getLogger(__name__)


class AliasGenerator:
    """Generates Python code for a type alias."""

    def __init__(
        self,
        renderer: PythonConstructRenderer,
        all_schemas: Optional[Dict[str, IRSchema]],
    ):
        # Pre-condition
        assert renderer is not None, "PythonConstructRenderer cannot be None"
        self.renderer = renderer
        self.all_schemas = all_schemas if all_schemas is not None else {}

    def generate(
        self,
        schema: IRSchema,
        base_name: str,
        context: RenderContext,
    ) -> str:
        """
        Generates the Python code for a type alias.

        Args:
            schema: The IRSchema for the alias.
            base_name: The base name for the alias (e.g., schema.name).
            context: The render context.

        Returns:
            The generated Python code string for the type alias.

        Contracts:
            Pre-conditions:
                - ``schema`` is not None and ``schema.name`` is not None.
                - ``base_name`` is a non-empty string.
                - ``context`` is not None.
                - The schema should logically represent a type alias (e.g., not have properties if it's not an array of anonymous objects).
            Post-conditions:
                - Returns a non-empty string containing valid Python code for a type alias.
                - ``TypeAlias`` is imported in the context if not already present.
        """
        # Pre-conditions
        assert schema is not None, "Schema cannot be None for alias generation."
        assert schema.name is not None, "Schema name must be present for alias generation."
        assert base_name, "Base name cannot be empty for alias generation."
        assert context is not None, "RenderContext cannot be None."

        alias_name = NameSanitizer.sanitize_class_name(base_name)
        target_type = TypeHelper.get_python_type_for_schema(
            schema, self.all_schemas, context, required=True, resolve_alias_target=True
        )
        target_type = TypeFinalizer(context)._clean_type(target_type)

        # logger.debug(f"AliasGenerator: Rendering alias '{alias_name}' for target type '{target_type}'.")

        rendered_code = self.renderer.render_alias(
            alias_name=alias_name,
            target_type=target_type,
            description=schema.description,
            context=context,
        )

        # Post-condition
        assert rendered_code.strip(), "Generated alias code cannot be empty."
        # PythonConstructRenderer is responsible for adding TypeAlias import
        # We can check if it was added to context if 'TypeAlias' is in the rendered code
        if "TypeAlias" in rendered_code:
            assert (
                "typing" in context.import_collector.imports
                and "TypeAlias" in context.import_collector.imports["typing"]
            ), "TypeAlias import was not added to context by renderer."

        return rendered_code
