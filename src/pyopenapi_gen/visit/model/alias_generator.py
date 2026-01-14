"""
Generates Python code for type aliases from IRSchema objects.
"""

import logging

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.types.services.type_service import UnifiedTypeService

logger = logging.getLogger(__name__)


class AliasGenerator:
    """Generates Python code for a type alias."""

    def __init__(
        self,
        renderer: PythonConstructRenderer,
        all_schemas: dict[str, IRSchema] | None,
    ):
        # Pre-condition
        if renderer is None:
            raise ValueError("PythonConstructRenderer cannot be None")
        self.renderer = renderer
        self.all_schemas = all_schemas if all_schemas is not None else {}
        self.type_service = UnifiedTypeService(self.all_schemas)

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
                - The schema should logically represent a type alias
                  (e.g., not have properties if it's not an array of anonymous objects).
            Post-conditions:
                - Returns a non-empty string containing valid Python code for a type alias.
                - ``TypeAlias`` is imported in the context if not already present.
        """
        # Pre-conditions
        if schema is None:
            raise ValueError("Schema cannot be None for alias generation.")
        if schema.name is None:
            raise ValueError("Schema name must be present for alias generation.")
        if not base_name:
            raise ValueError("Base name cannot be empty for alias generation.")
        if context is None:
            raise ValueError("RenderContext cannot be None.")

        alias_name = NameSanitizer.sanitize_class_name(base_name)
        target_type = self.type_service.resolve_schema_type(schema, context, required=True, resolve_underlying=True)

        # logger.debug(f"AliasGenerator: Rendering alias '{alias_name}' for target type '{target_type}'.")

        # Pass discriminator metadata if this is a union type
        discriminator = schema.discriminator if hasattr(schema, "discriminator") else None

        rendered_code = self.renderer.render_alias(
            alias_name=alias_name,
            target_type=target_type,
            description=schema.description,
            context=context,
            discriminator=discriminator,
        )

        # Post-condition
        if not rendered_code.strip():
            raise RuntimeError("Generated alias code cannot be empty.")
        # PythonConstructRenderer is responsible for adding TypeAlias import
        # We can check if it was added to context if 'TypeAlias' is in the rendered code
        if "TypeAlias" in rendered_code:
            if not (
                "typing" in context.import_collector.imports
                and "TypeAlias" in context.import_collector.imports["typing"]
            ):
                raise RuntimeError("TypeAlias import was not added to context by renderer.")

        return rendered_code
