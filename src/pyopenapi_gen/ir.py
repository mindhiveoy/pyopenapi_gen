from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# Import NameSanitizer at the top for type hints and __post_init__ usage
from pyopenapi_gen.core.utils import NameSanitizer

# Import HTTPMethod as it's used by IROperation
from .http_types import HTTPMethod

# Forward declaration for IRSchema itself if needed for self-references in type hints
# class IRSchema:
#     pass


@dataclass
class IRSchema:
    name: Optional[str] = None
    type: Optional[str] = None  # E.g., "object", "array", "string", or a reference to another schema name
    format: Optional[str] = None
    description: Optional[str] = None
    required: List[str] = field(default_factory=list)
    properties: Dict[str, IRSchema] = field(default_factory=dict)
    items: Optional[IRSchema] = None  # For type: "array"
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None  # Added default value
    example: Optional[Any] = None  # Added example value
    additional_properties: Optional[Union[bool, IRSchema]] = None  # True, False, or an IRSchema
    is_nullable: bool = False
    any_of: Optional[List[IRSchema]] = None
    one_of: Optional[List[IRSchema]] = None
    all_of: Optional[List[IRSchema]] = None  # Store the list of IRSchema objects from allOf
    title: Optional[str] = None  # Added title
    is_data_wrapper: bool = False  # True if schema is a simple {{ "data": OtherSchema }} wrapper

    # Internal generator flags/helpers
    _from_unresolved_ref: bool = False  # True if this IRSchema was created as a placeholder for an unresolvable $ref
    _refers_to_schema: Optional[IRSchema] = (
        None  # If this schema is a reference (e.g. a promoted property), this can link to the actual definition
    )
    _is_circular_ref: bool = False  # True if this schema was detected as part of a circular reference
    _circular_ref_path: Optional[str] = None  # Contains the path of the circular reference if detected
    _is_name_derived: bool = field(
        default=False, repr=False
    )  # True if the name was derived (e.g. for promoted inline objects)
    _inline_name_resolution_path: Optional[str] = field(
        default=None, repr=False
    )  # Path used for resolving inline names

    def __post_init__(self) -> None:
        # >>> DIAGNOSTIC PRINT (REMOVED) <<<
        # if self.name == "PropA":
        #     print(f"IRSCHEMA_POST_INIT_ENTRY for PropA: self.type='{self.type}', raw_node={getattr(self, '_raw_schema_node', 'N/A')}, id={id(self)}")

        # Ensure name is always a valid Python identifier if set
        # This must happen BEFORE type inference that might use the name (though current logic doesn't)
        if self.name:
            # Store original name if needed for specific logic before sanitization, though not currently used here.
            # original_name = self.name
            self.name = NameSanitizer.sanitize_class_name(self.name)

        # Ensure that if type is a reference (string not matching basic types),
        # other structural fields like properties/items/enum are usually None or empty.
        basic_types = ["object", "array", "string", "integer", "number", "boolean", "null"]
        if self.type and self.type not in basic_types:
            # This schema acts as a reference by name to another schema.
            # It shouldn't typically define its own structure beyond description/nullability.
            pass

        # The check for is_valid_python_identifier is somewhat redundant if sanitize_class_name works correctly,
        # but can be kept as a safeguard or for logging if a raw name was problematic *before* sanitization.
        if self.name and not NameSanitizer.is_valid_python_identifier(self.name):
            pass  # logger.warning or handle as needed elsewhere

        # Ensure nested schemas are IRSchema instances
        if isinstance(self.items, dict):
            self.items = IRSchema(**self.items)

        if isinstance(self.properties, dict):
            new_props = {}
            for k, v in self.properties.items():
                if isinstance(v, dict):
                    new_props[k] = IRSchema(**v)
                elif isinstance(v, IRSchema):  # Already an IRSchema instance
                    new_props[k] = v
                # else: it might be some other unexpected type, raise error or log
            self.properties = new_props

        if isinstance(self.additional_properties, dict):
            self.additional_properties = IRSchema(**self.additional_properties)

        for comp_list_attr in ["any_of", "one_of", "all_of"]:
            comp_list = getattr(self, comp_list_attr)
            if isinstance(comp_list, list):
                new_comp_list = []
                for item in comp_list:
                    if isinstance(item, dict):
                        new_comp_list.append(IRSchema(**item))
                    elif isinstance(item, IRSchema):
                        new_comp_list.append(item)
                    # else: item is some other type, could skip or raise
                setattr(self, comp_list_attr, new_comp_list)


# NameSanitizer is now imported at the top
# from pyopenapi_gen.core.utils import NameSanitizer


@dataclass(slots=True)
class IRParameter:
    name: str
    param_in: str  # Renamed from 'in' to avoid keyword clash, was in_: str in original __init__.py
    required: bool
    schema: IRSchema
    description: Optional[str] = None
    # example: Optional[Any] = None # This was in my latest ir.py but not __init__.py, keeping it from my version


# Adding other IR classes from the original __init__.py structure
@dataclass(slots=True)
class IRResponse:
    status_code: str  # can be "default" or specific status like "200"
    description: Optional[str]
    content: Dict[str, IRSchema]  # media‑type → schema mapping
    stream: bool = False  # Indicates a binary or streaming response
    stream_format: Optional[str] = None  # Indicates the stream type


@dataclass(slots=True)
class IRRequestBody:
    required: bool
    content: Dict[str, IRSchema]  # media‑type → schema mapping
    description: Optional[str] = None


@dataclass(slots=True)
class IROperation:
    operation_id: str
    method: HTTPMethod  # Enforced via enum for consistency
    path: str  # e.g. "/pets/{petId}"
    summary: Optional[str]
    description: Optional[str]
    parameters: List[IRParameter] = field(default_factory=list)
    request_body: Optional[IRRequestBody] = None
    responses: List[IRResponse] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass(slots=True)
class IRSpec:
    title: str
    version: str
    description: Optional[str] = None
    schemas: Dict[str, IRSchema] = field(default_factory=dict)
    operations: List[IROperation] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)
