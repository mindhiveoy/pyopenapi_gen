"""
Generates validation code for dataclass fields based on OpenAPI constraints.
"""

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext


class ValidationCodeGenerator:
    """Generates validation code for dataclass fields based on constraints."""

    @staticmethod
    def _indent_code(code: str, spaces: int = 4) -> str:
        """Indent all lines of code by the specified number of spaces."""
        indent = " " * spaces
        lines = code.split("\n")
        return "\n".join(indent + line if line.strip() else line for line in lines)

    @staticmethod
    def _generate_string_validation(field_name: str, schema: IRSchema) -> list[str]:
        """Generate string validation code."""
        validations = []

        # Length constraints
        if schema.min_length is not None or schema.max_length is not None:
            if schema.min_length is not None and schema.max_length is not None:
                validations.append(
                    f"if not ({schema.min_length} <= len(self.{field_name}) <= {schema.max_length}):\n"
                    f"            raise ValueError(\"Field '{field_name}' length must be between "
                    f'{schema.min_length} and {schema.max_length}, got " + str(len(self.{field_name})))'
                )
            elif schema.min_length is not None:
                validations.append(
                    f"if len(self.{field_name}) < {schema.min_length}:\n"
                    f"            raise ValueError(\"Field '{field_name}' length must be at least "
                    f'{schema.min_length}, got " + str(len(self.{field_name})))'
                )
            elif schema.max_length is not None:
                validations.append(
                    f"if len(self.{field_name}) > {schema.max_length}:\n"
                    f"            raise ValueError(\"Field '{field_name}' length must be at most "
                    f'{schema.max_length}, got " + str(len(self.{field_name})))'
                )

        # Pattern constraint
        if schema.pattern:
            # Properly escape pattern for Python string literal
            # Replace backslash first (must be first), then quotes
            escaped_pattern = schema.pattern.replace("\\", "\\\\").replace('"', '\\"')
            validations.append(
                f'if not re.match(r"{escaped_pattern}", self.{field_name}):\n'
                f"            raise ValueError(\"Field '{field_name}' does not match required pattern\")"
            )

        return validations

    @staticmethod
    def _generate_numeric_validation(field_name: str, schema: IRSchema) -> list[str]:
        """Generate numeric validation code."""
        validations = []

        # Range constraints
        has_min = schema.minimum is not None
        has_max = schema.maximum is not None

        if has_min and has_max:
            # Both min and max
            if schema.exclusive_minimum and schema.exclusive_maximum:
                validations.append(
                    f"if not ({schema.minimum} < self.{field_name} < {schema.maximum}):\n"
                    f"            raise ValueError(\"Field '{field_name}' must be greater than "
                    f'{schema.minimum} and less than {schema.maximum}, got " + str(self.{field_name}))'
                )
            elif schema.exclusive_minimum:
                validations.append(
                    f"if not ({schema.minimum} < self.{field_name} <= {schema.maximum}):\n"
                    f"            raise ValueError(\"Field '{field_name}' must be greater than "
                    f'{schema.minimum} and at most {schema.maximum}, got " + str(self.{field_name}))'
                )
            elif schema.exclusive_maximum:
                validations.append(
                    f"if not ({schema.minimum} <= self.{field_name} < {schema.maximum}):\n"
                    f"            raise ValueError(\"Field '{field_name}' must be at least "
                    f'{schema.minimum} and less than {schema.maximum}, got " + str(self.{field_name}))'
                )
            else:
                validations.append(
                    f"if not ({schema.minimum} <= self.{field_name} <= {schema.maximum}):\n"
                    f"            raise ValueError(\"Field '{field_name}' must be between "
                    f'{schema.minimum} and {schema.maximum}, got " + str(self.{field_name}))'
                )
        elif has_min:
            # Only minimum
            if schema.exclusive_minimum:
                validations.append(
                    f"if self.{field_name} <= {schema.minimum}:\n"
                    f"            raise ValueError(\"Field '{field_name}' must be greater than "
                    f'{schema.minimum}, got " + str(self.{field_name}))'
                )
            else:
                validations.append(
                    f"if self.{field_name} < {schema.minimum}:\n"
                    f"            raise ValueError(\"Field '{field_name}' must be at least "
                    f'{schema.minimum}, got " + str(self.{field_name}))'
                )
        elif has_max:
            # Only maximum
            if schema.exclusive_maximum:
                validations.append(
                    f"if self.{field_name} >= {schema.maximum}:\n"
                    f"            raise ValueError(\"Field '{field_name}' must be less than "
                    f'{schema.maximum}, got " + str(self.{field_name}))'
                )
            else:
                validations.append(
                    f"if self.{field_name} > {schema.maximum}:\n"
                    f"            raise ValueError(\"Field '{field_name}' must be at most "
                    f'{schema.maximum}, got " + str(self.{field_name}))'
                )

        # multipleOf constraint
        if schema.multiple_of is not None:
            if schema.type == "integer":
                validations.append(
                    f"if self.{field_name} % {schema.multiple_of} != 0:\n"
                    f"            raise ValueError(\"Field '{field_name}' must be a multiple of "
                    f'{schema.multiple_of}, got " + str(self.{field_name}))'
                )
            else:
                # For floats, use relative epsilon based on value magnitude
                # Use Python's math.isclose logic: tolerance = max(rel_tol * max(abs(a), abs(b)), abs_tol)
                # Note: This returns a multi-line validation. Each line except the first needs base indentation
                # since generate_validation_method() joins with "\n        " which only indents the first line.
                validations.append(
                    f"_remainder = abs(self.{field_name} % {schema.multiple_of})\n"
                    f"        _tolerance = max(1e-09 * max(abs(self.{field_name}), abs({schema.multiple_of})), 1e-10)\n"
                    f"        if _remainder > _tolerance and abs(_remainder - {schema.multiple_of}) > _tolerance:\n"
                    f"            raise ValueError(\"Field '{field_name}' must be a multiple of "
                    f'{schema.multiple_of}, got " + str(self.{field_name}))'
                )

        return validations

    @staticmethod
    def _generate_array_validation(field_name: str, schema: IRSchema) -> list[str]:
        """Generate array validation code."""
        validations = []

        # Length constraints
        if schema.min_items is not None or schema.max_items is not None:
            if schema.min_items is not None and schema.max_items is not None:
                validations.append(
                    f"if not ({schema.min_items} <= len(self.{field_name}) <= {schema.max_items}):\n"
                    f"            raise ValueError(\"Field '{field_name}' must contain between "
                    f'{schema.min_items} and {schema.max_items} items, got " + str(len(self.{field_name})))'
                )
            elif schema.min_items is not None:
                validations.append(
                    f"if len(self.{field_name}) < {schema.min_items}:\n"
                    f"            raise ValueError(\"Field '{field_name}' must contain at least "
                    f'{schema.min_items} items, got " + str(len(self.{field_name})))'
                )
            elif schema.max_items is not None:
                validations.append(
                    f"if len(self.{field_name}) > {schema.max_items}:\n"
                    f"            raise ValueError(\"Field '{field_name}' must contain at most "
                    f'{schema.max_items} items, got " + str(len(self.{field_name})))'
                )

        # Unique items constraint
        if schema.unique_items:
            # Try to use set() for hashable items, fall back to manual comparison for unhashable
            validations.append(
                f"try:\n"
                f"            if len(self.{field_name}) != len(set(self.{field_name})):\n"
                f"                raise ValueError(\"Field '{field_name}' must contain unique items\")\n"
                f"        except TypeError:\n"
                f"            # Items are unhashable (dicts, lists), use manual comparison\n"
                f"            seen = []\n"
                f"            for item in self.{field_name}:\n"
                f"                if item in seen:\n"
                f"                    raise ValueError(\"Field '{field_name}' must contain unique items\")\n"
                f"                seen.append(item)"
            )

        return validations

    @staticmethod
    def _generate_object_validation(field_name: str, schema: IRSchema) -> list[str]:
        """Generate object validation code."""
        validations = []

        # Property count constraints (only if both are set - simpler)
        if schema.min_properties is not None and schema.max_properties is not None:
            validations.append(
                f"if hasattr(self.{field_name}, '__dict__'):\n"
                f'            prop_count = len([k for k in vars(self.{field_name}).keys() if not k.startswith("_")])\n'
                f"            if not ({schema.min_properties} <= prop_count <= {schema.max_properties}):\n"
                f"                raise ValueError(\"Field '{field_name}' must have between "
                f'{schema.min_properties} and {schema.max_properties} properties, got " + str(prop_count))'
            )
        elif schema.min_properties is not None:
            validations.append(
                f"if hasattr(self.{field_name}, '__dict__'):\n"
                f'            prop_count = len([k for k in vars(self.{field_name}).keys() if not k.startswith("_")])\n'
                f"            if prop_count < {schema.min_properties}:\n"
                f"                raise ValueError(\"Field '{field_name}' must have at least "
                f'{schema.min_properties} properties, got " + str(prop_count))'
            )
        elif schema.max_properties is not None:
            validations.append(
                f"if hasattr(self.{field_name}, '__dict__'):\n"
                f'            prop_count = len([k for k in vars(self.{field_name}).keys() if not k.startswith("_")])\n'
                f"            if prop_count > {schema.max_properties}:\n"
                f"                raise ValueError(\"Field '{field_name}' must have at most "
                f'{schema.max_properties} properties, got " + str(prop_count))'
            )

        return validations

    @staticmethod
    def _generate_format_validation(field_name: str, schema: IRSchema) -> tuple[list[str], set[str]]:
        """Generate format validation code for string fields.

        Returns:
            Tuple of (validation code lines, required imports)
        """
        validations = []
        imports_needed = set()

        if not schema.format or schema.type != "string":
            return validations, imports_needed

        format_type = schema.format.lower()

        if format_type == "email":
            # Simple email validation using regex (RFC 5322 simplified)
            # Requires TLD (e.g., .com) for practical email validation
            imports_needed.add("re")
            # Email pattern: local-part@domain.tld (requires at least one dot in domain)
            # Note: Pattern will be embedded in r"..." raw string, so use single backslashes
            email_pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
            validations.append(
                f'if not re.match(r"{email_pattern}", self.{field_name}):\n'
                f'            raise ValueError("Field \'{field_name}\' must be a valid email address")'
            )

        elif format_type in ("uri", "url"):
            # URI validation using urllib.parse
            imports_needed.add("urllib.parse")
            validations.append(
                f"try:\n"
                f"            _parsed = urllib.parse.urlparse(self.{field_name})\n"
                f"            if not all([_parsed.scheme, _parsed.netloc]):\n"
                f"                raise ValueError(\"Field '{field_name}' must be a valid URI with scheme and netloc\")\n"
                f"        except Exception:\n"
                f'            raise ValueError("Field \'{field_name}\' must be a valid URI")'
            )

        elif format_type == "uuid":
            # UUID validation
            # Note: Type resolver already imports UUID from uuid module
            validations.append(
                f"try:\n"
                f"            UUID(self.{field_name})\n"
                f"        except (ValueError, AttributeError):\n"
                f'            raise ValueError("Field \'{field_name}\' must be a valid UUID")'
            )

        elif format_type == "date":
            # ISO 8601 date validation
            # Note: Type resolver already imports date from datetime module
            validations.append(
                f"try:\n"
                f"            date.fromisoformat(self.{field_name})\n"
                f"        except (ValueError, TypeError):\n"
                f'            raise ValueError("Field \'{field_name}\' must be a valid ISO 8601 date (YYYY-MM-DD)")'
            )

        elif format_type == "date-time":
            # ISO 8601 datetime validation
            # Note: Type resolver already imports datetime from datetime module
            validations.append(
                f"try:\n"
                f"            # Try parsing as ISO 8601 datetime\n"
                f"            datetime.fromisoformat(self.{field_name}.replace('Z', '+00:00'))\n"
                f"        except (ValueError, TypeError, AttributeError):\n"
                f'            raise ValueError("Field \'{field_name}\' must be a valid ISO 8601 date-time")'
            )

        elif format_type == "time":
            # ISO 8601 time validation
            # Note: Type resolver already imports time from datetime module
            validations.append(
                f"try:\n"
                f"            time.fromisoformat(self.{field_name})\n"
                f"        except (ValueError, TypeError):\n"
                f'            raise ValueError("Field \'{field_name}\' must be a valid ISO 8601 time (HH:MM:SS)")'
            )

        elif format_type in ("ipv4", "hostname"):
            # IP/hostname validation using simple regex
            imports_needed.add("re")
            if format_type == "ipv4":
                pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                error_msg = "valid IPv4 address"
            else:  # hostname
                pattern = r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
                error_msg = "valid hostname"

            validations.append(
                f'if not re.match(r"{pattern}", self.{field_name}):\n'
                f'            raise ValueError("Field \'{field_name}\' must be a {error_msg}")'
            )

        elif format_type == "ipv6":
            # IPv6 validation using ipaddress module
            imports_needed.add("ipaddress")
            validations.append(
                f"try:\n"
                f"            ipaddress.IPv6Address(self.{field_name})\n"
                f"        except (ValueError, ipaddress.AddressValueError):\n"
                f'            raise ValueError("Field \'{field_name}\' must be a valid IPv6 address")'
            )

        # For other formats (byte, binary, password, etc.), we don't validate
        # as they don't have specific validation requirements beyond being strings

        return validations, imports_needed

    @classmethod
    def generate_validation_method(
        cls,
        schema: IRSchema,
        sanitized_field_names: dict[str, str],
        context: RenderContext,
    ) -> str | None:
        """
        Generate __post_init__ validation method for a dataclass.

        Args:
            schema: The schema with properties and constraints
            sanitized_field_names: Mapping from original names to sanitized Python field names
            context: Render context for adding imports

        Returns:
            Python code for __post_init__ method, or None if no validation needed
        """
        if not schema.properties:
            return None

        all_validations = []
        imports_needed = set()

        for prop_name, prop_schema in schema.properties.items():
            field_name = sanitized_field_names.get(prop_name, prop_name)

            # Skip validation for fields that are None (optional fields might be None)
            # Wrap all field validations in a None check
            field_validations = []

            # String validation
            if prop_schema.type == "string" and (
                prop_schema.min_length is not None
                or prop_schema.max_length is not None
                or prop_schema.pattern is not None
            ):
                field_validations.extend(cls._generate_string_validation(field_name, prop_schema))
                if prop_schema.pattern:
                    imports_needed.add("re")

            # Format validation (for string fields)
            if prop_schema.type == "string" and prop_schema.format:
                format_validations, format_imports = cls._generate_format_validation(field_name, prop_schema)
                field_validations.extend(format_validations)
                imports_needed.update(format_imports)

            # Numeric validation
            if prop_schema.type in ("integer", "number") and (
                prop_schema.minimum is not None
                or prop_schema.maximum is not None
                or prop_schema.multiple_of is not None
            ):
                field_validations.extend(cls._generate_numeric_validation(field_name, prop_schema))

            # Array validation
            # Check for array constraints regardless of type name (type might be "array" or a type alias like "Tags")
            # If min_items, max_items, or unique_items is set, this is an array field
            if (
                prop_schema.min_items is not None or prop_schema.max_items is not None or prop_schema.unique_items
            ):
                field_validations.extend(cls._generate_array_validation(field_name, prop_schema))

            # Object validation
            if prop_schema.type == "object" and (
                prop_schema.min_properties is not None or prop_schema.max_properties is not None
            ):
                field_validations.extend(cls._generate_object_validation(field_name, prop_schema))

            # If this field has validations and might be None, wrap in None check
            if field_validations and prop_name not in schema.required:
                all_validations.append(f"if self.{field_name} is not None:")
                for validation in field_validations:
                    # Properly indent all lines of the validation code
                    indented = cls._indent_code(validation, spaces=4)
                    all_validations.append(indented)
            else:
                all_validations.extend(field_validations)

        if not all_validations:
            return None

        # Add required imports for validation
        for import_name in imports_needed:
            if import_name == "urllib.parse":
                context.add_import("urllib.parse", None)
            elif import_name == "ipaddress":
                context.add_import("ipaddress", None)
            else:
                # For re, datetime, uuid - simple imports
                context.add_import(import_name, None)

        # Generate the __post_init__ method
        validation_code = "\n        ".join(all_validations)
        return f"""
    def __post_init__(self) -> None:
        \"\"\"Validate field constraints.\"\"\"
        {validation_code}"""
