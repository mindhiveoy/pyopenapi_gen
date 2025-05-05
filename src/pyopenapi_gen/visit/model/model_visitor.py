from typing import Dict, Optional
import sys

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from ...core.utils import Formatter, NameSanitizer
from ...core.writers.code_writer import CodeWriter
from ...helpers.type_helper import get_python_type_for_schema
from ..visitor import Visitor


class ModelVisitor(Visitor[IRSchema, str]):
    """
    Visitor for rendering a Python model (dataclass or enum) from an IRSchema.
    Returns the rendered code as a string (does not write files).
    Only adds imports/types to the context if they are actually used in the rendered code for the module.
    """

    def __init__(self, schemas: Optional[Dict[str, IRSchema]] = None) -> None:
        self.formatter = Formatter()
        self.schemas = schemas or {}

    def visit_IRSchema(self, schema: IRSchema, context: RenderContext) -> str:
        """Render a Python model (Dataclass, Enum, or Type Alias) from IRSchema."""

        # # <<< DEBUG PRINT for SuccessSuccessEnum >>>
        # if schema.name == "SuccessSuccessEnum":
        #     print(f"DEBUG [ModelVisitor]: Inspecting schema '{schema.name}':", file=sys.stderr)
        #     print(f"  - schema.type: {schema.type}", file=sys.stderr)
        #     print(f"  - schema.enum: {schema.enum}", file=sys.stderr)
        #     print(f"  - schema.properties: {schema.properties}", file=sys.stderr)
        # # <<< END DEBUG >>>

        # ---- Determine Output Type (Prioritize Enum) ----
        is_enum = schema.enum and schema.name and schema.type in ("string", "integer", "boolean")

        # Initialize flags
        is_primitive_alias = False
        is_array_alias = False
        is_type_alias = False
        is_dataclass = False

        # --- Dataclass Detection ---
        is_dataclass = not is_enum and not is_type_alias

        # # --- Debug Print for Success.success ---
        # if schema.name == "Success.success":
        #     print(f"DEBUG [ModelVisitor]: Classifying 'Success.success':", file=sys.stderr)
        #     print(f"  - schema.enum: {schema.enum}", file=sys.stderr)
        #     print(f"  - schema.type: {schema.type}", file=sys.stderr)
        #     print(f"  - schema.properties: {schema.properties}", file=sys.stderr)
        #     print(f"  - is_enum: {is_enum}", file=sys.stderr)
        #     print(f"  - is_primitive_alias: {is_primitive_alias}", file=sys.stderr)
        #     print(f"  - is_array_alias: {is_array_alias}", file=sys.stderr)
        #     print(f"  - is_type_alias: {is_type_alias}", file=sys.stderr)
        #     print(f"  - is_dataclass: {is_dataclass}", file=sys.stderr)
        # # --- End Debug Print ---

        # <<< Start Change: Only check for alias/dataclass if NOT an enum >>>
        if not is_enum:
            # Calculate alias flags
            is_primitive_alias = bool(
                schema.name and not schema.properties and schema.type in ("string", "integer", "number", "boolean")
            )
            is_array_alias = bool(
                schema.name and not schema.properties and schema.type == "array" and schema.items is not None
            )
            is_type_alias = is_primitive_alias or is_array_alias

            # Calculate dataclass flag (only if not an alias)
            if not is_type_alias:
                is_dataclass = bool(
                    schema.type == "object"
                    or (schema.type is None and (schema.properties or schema.any_of or schema.one_of or schema.all_of))
                )
        # <<< End Change >>>

        # --- Generate Code (Will trigger import collection in context) --- (Call specific helper)
        writer = CodeWriter()
        generated_code: str = ""
        if is_enum:
            generated_code = self._render_enum(writer, schema, context)
        elif is_type_alias:
            # <<< Change Start >>>
            # Don't generate standalone files for primitive aliases
            if is_primitive_alias:
                # Log or print a warning if desired
                print(f"[INFO] Skipping file generation for primitive alias: {schema.name}")
                return ""  # Return empty string to prevent file writing
            else:  # It's an array alias, generate the file
                generated_code = self._render_alias(writer, schema, context)
            # <<< Change End >>>
        elif is_dataclass:
            generated_code = self._render_dataclass(writer, schema, context)
        else:
            # Handle cases like basic types used directly without alias or object structure
            # This might occur for schemas used only in parameters/responses directly
            # We typically don't generate standalone files for these, but handle them inline.
            # If a direct generation is needed, logic would go here.
            # For now, we assume schemas needing files are covered by enum/alias/dataclass.
            print(
                f"[WARN] Skipping generation for schema '{schema.name}' - Not an enum, alias, or recognized dataclass structure."
            )
            return ""  # Return empty string, don't write a file

        # --- Render Imports (Collected during generation) ---
        import_block = context.render_imports()  # Calls import_collector.get_formatted_imports()

        # --- Combine Imports and Code ---
        # Mark module as generated (already done earlier)
        if context.current_file:
            context.mark_generated_module(context.current_file)
        # Return formatted code directly, skipping local 'final_code' variable
        return self.formatter.format(f"{import_block}\n\n{generated_code}")

    # --------------------------------------------------------------------------
    # Private Helper Methods for Rendering
    # --------------------------------------------------------------------------

    def _render_alias(self, writer: CodeWriter, schema: IRSchema, context: RenderContext) -> str:
        """
        Renders a type alias (e.g., UserId = str).

        Preconditions:
            - schema.name is not None.
            - The schema represents a primitive type or an array.
        Postconditions:
            - The writer contains the type alias definition.
            - Necessary types are added to context imports.
        """
        if not schema.name:
            return ""  # Should not happen

        alias_name = NameSanitizer.sanitize_class_name(schema.name)
        target_type: str

        if schema.type == "array" and schema.items:
            # Get item type, ensuring nested types are processed and imported
            item_type = get_python_type_for_schema(
                schema.items, self.schemas, context, required=True
            )  # Array items are always non-optional within the List
            target_type = f"List[{item_type}]"
            context.add_import("typing", "List")
        elif schema.type in ("string", "integer", "number", "boolean"):
            # Use get_python_type_for_schema for consistency (handles format like date/datetime)
            # Pass required=True as the alias itself isn't optional
            target_type = get_python_type_for_schema(schema, self.schemas, context, required=True)
            # Add datetime/date imports if needed
            if schema.format == "date":
                context.add_import("datetime", "date")
            elif schema.format == "date-time":
                context.add_import("datetime", "datetime")
        else:
            # Should not happen based on visit_IRSchema logic
            print(f"[WARN] Cannot render alias for non-primitive/non-array schema: {schema.name}")
            return ""

        context.add_import("typing", "TypeAlias")
        writer.write_line(f"{alias_name}: TypeAlias = {target_type}")
        if schema.description:
            # Use write_line with triple quotes for potentially multi-line description
            writer.write_line(f'""" {schema.description} """')

        return writer.get_code()  # Return generated code

    def _render_enum(self, writer: CodeWriter, schema: IRSchema, context: RenderContext) -> str:
        """
        Renders an Enum definition.

        Preconditions:
            - schema.name is not None.
            - schema.enum is not None and non-empty.
            - schema.type is 'string' or 'integer'.
        Postconditions:
            - The writer contains the Enum definition.
            - Necessary types (Enum) are added to context imports.
        """
        if not schema.name or not schema.enum:
            return ""  # Should not happen if called correctly

        class_name = NameSanitizer.sanitize_class_name(schema.name)

        # <<< Start Changes >>>
        # Add necessary imports to context
        context.add_import("enum", "Enum")
        context.add_import("enum", "unique")
        context.add_plain_import("json")  # Add import json

        # Write __all__ export
        writer.write_line(f'__all__ = ["{class_name}"]')
        writer.write_line("")  # Add a blank line

        # Add unique decorator
        writer.write_line("@unique")
        # <<< End Changes >>>

        # Use base_type for class definition (already derived in visit_IRSchema, but let's be explicit)
        base_type = "str" if schema.type == "string" else "int"
        writer.write_line(f"class {class_name}({base_type}, Enum):")
        writer.indent()

        summary = schema.description or f"An enumeration."
        writer.write_line(f'"""{summary}"""')

        # Write enum members
        for val in schema.enum:
            member_name: str
            if schema.type == "string":
                member_name_str = str(val)
                member_name = NameSanitizer.sanitize_method_name(member_name_str).upper()
                if not member_name or not (member_name[0].isalpha() or member_name[0] == "_"):
                    member_name = "_" + member_name
                writer.write_line(f'{member_name} = "{member_name_str}"')
            elif schema.type == "integer":
                int_member_name_str = str(val)
                member_name = NameSanitizer.sanitize_method_name(f"VALUE_{int_member_name_str}").upper()
                if not member_name or not (member_name[0].isalpha() or member_name[0] == "_"):
                    member_name = "_" + member_name
                writer.write_line(f"{member_name} = {int(val)}")

        # <<< Start Changes: Add from_json method >>>
        writer.write_line("")  # Blank line
        writer.write_line("@classmethod")
        writer.write_line(f'def from_json(cls, json_str: str) -> "{class_name}":')
        writer.indent()
        writer.write_line('"""Create an instance from a JSON string"""')
        writer.write_line(f"return {class_name}(json.loads(json_str))")
        writer.dedent()
        # <<< End Changes >>>

        writer.dedent()
        return writer.get_code()

    def _render_dataclass(self, writer: CodeWriter, schema: IRSchema, context: RenderContext) -> str:
        """
        Renders a dataclass definition.

        Preconditions:
            - schema represents an object type or has properties/composition.
            - schema.name is not None.
        Postconditions:
            - The writer contains the dataclass definition.
            - Necessary types (dataclass, field, typing imports) are added to context imports.
        """
        if not schema.name:
            return ""  # Should not happen

        class_name = NameSanitizer.sanitize_class_name(schema.name)
        context.add_import("dataclasses", "dataclass")

        writer.write_line("@dataclass")
        writer.write_line(f"class {class_name}:")
        writer.indent()

        # Build docstring and collect field info (this also triggers type import registration)
        summary = schema.description or f"Data model for {class_name}"
        field_args: list[tuple[str, str, str]] = []
        required_props = []
        optional_props = []
        needs_field_import = False
        has_optional_props = False
        has_list_props = False
        has_dict_props = False
        has_union_props = False  # Track if Union is potentially needed
        has_any_props = False  # Track if Any is potentially needed

        # First pass: Collect info and register base types
        if schema.properties:
            for prop, ps in schema.properties.items():
                prop_name_sanitized = NameSanitizer.sanitize_method_name(prop)
                is_required = prop in (schema.required or [])
                # Determine type string AND register imports via helper
                py_type = get_python_type_for_schema(ps, self.schemas, context, required=is_required)
                desc = ps.description or ""
                field_args.append((prop_name_sanitized, py_type, desc))

                # Track property characteristics for explicit imports
                if not is_required:
                    has_optional_props = True
                if "List[" in py_type:
                    has_list_props = True
                if "Dict[" in py_type:
                    has_dict_props = True
                if "Union[" in py_type:
                    has_union_props = True
                if "Any" in py_type:
                    has_any_props = True

                # Prepare default value if necessary
                default_factory = None
                if not is_required:
                    # Optional fields default to None
                    default_value = " = None"
                    optional_props.append(prop_name_sanitized)
                elif py_type.startswith("List[") and is_required:
                    # Required lists should default to empty list via factory
                    default_factory = "list"
                    default_value = f" = field(default_factory={default_factory})"
                    needs_field_import = True
                elif py_type.startswith("Dict[") and is_required:
                    # Required dicts should default to empty dict via factory
                    default_factory = "dict"
                    default_value = f" = field(default_factory={default_factory})"
                    needs_field_import = True
                else:  # Required property with no default
                    default_value = ""
                    required_props.append(prop_name_sanitized)

        # TODO: Handle composition (allOf, anyOf, oneOf) - complex, requires careful merging/inheritance/union handling
        # if schema.all_of: ...
        # if schema.any_of: ... # Often leads to Union types
        # if schema.one_of: ... # Also leads to Union types

        # Add explicit imports based on collected info BEFORE writing fields
        if has_optional_props:
            context.add_import("typing", "Optional")
        if has_list_props:
            context.add_import("typing", "List")
        if has_dict_props:
            context.add_import("typing", "Dict")
        if has_union_props:
            context.add_import("typing", "Union")
        if has_any_props:
            context.add_import("typing", "Any")
        if needs_field_import:
            context.add_import("dataclasses", "field")

        # Add datetime imports if needed
        has_date_props = any(f[1] == "date" for f in field_args)
        has_datetime_props = any(f[1] == "datetime" for f in field_args)
        if has_date_props:
            context.add_import("datetime", "date")
        if has_datetime_props:
            context.add_import("datetime", "datetime")

        # Write docstring
        docstring_lines = [summary, ""]
        if schema.properties:
            docstring_lines.append("Attributes:")
            # Unpack 3 values consistently
            for prop_name, py_type, desc in field_args:
                docstring_lines.append(f"    {prop_name} ({py_type}): {desc if desc else 'No description provided.'}")
        # TODO: Add example from schema.example if present
        # Write multi-line docstring using write_line
        writer.write_line('"""')
        for line in docstring_lines:
            writer.write_line(line)
        writer.write_line('"""')

        # Write fields (with defaults)
        if not schema.properties:
            writer.write_line("# No properties defined in schema")
            writer.write_line("pass")  # Ensure class body is not empty
        else:
            # Write required fields first
            for prop_name, py_type, _ in field_args:
                if prop_name in required_props:
                    # Determine if default factory is needed for required list/dict
                    df = None
                    if py_type.startswith("List["):
                        df = "list"
                    elif py_type.startswith("Dict["):
                        df = "dict"

                    if df:
                        writer.write_line(f"{prop_name}: {py_type} = field(default_factory={df})")
                        needs_field_import = True  # Re-check in case it wasn't set before
                    else:
                        writer.write_line(f"{prop_name}: {py_type}")

            # Write optional fields (with defaults or None)
            for prop_name, py_type, _ in field_args:
                if prop_name in optional_props:
                    # Always default optional fields to None unless a default_factory was needed (handled above)
                    # Check if it's a field that needs a default factory (shouldn't happen for optional unless
                    # explicitly defaulted in schema, which we are not handling yet)
                    df = None
                    if py_type.startswith("List["):
                        df = "list"
                    elif py_type.startswith("Dict["):
                        df = "dict"

                    if (
                        df and prop_name not in required_props
                    ):  # Optional fields needing factory (less common, maybe default=[] in schema?)
                        writer.write_line(f"{prop_name}: {py_type} = field(default_factory={df})")
                        needs_field_import = True
                    else:  # Standard optional field defaults to None
                        writer.write_line(f"{prop_name}: {py_type} = None")

        writer.dedent()
        # Re-add field import if needed after processing all fields
        if needs_field_import:
            context.add_import("dataclasses", "field")

        return writer.get_code()  # Return generated code

    # --- Removed _analyze_and_register_rendering_imports --- imports added directly ---

    def _get_default_factory(self, prop: IRSchema) -> Optional[str]:
        if prop.type == "array":
            return "list"
        if prop.type == "object":
            return "dict"
        return None
