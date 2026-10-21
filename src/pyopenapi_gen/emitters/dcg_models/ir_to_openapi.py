"""
Serialise named ``IRSchema`` objects into an OpenAPI 3.1 document for datamodel-code-generator.

The IR, not the raw spec, is the source of truth for code generation. By the time this runs,
``ModelsEmitter`` has already promoted inline objects/enums to named schemas and assigned every
model a unique ``generation_name``. Emitting each of those under its ``generation_name`` means
datamodel-code-generator's class names are the IR's class names by construction, so the endpoint
generators (which import models by ``generation_name``) keep working unchanged.

Python field names are chosen here, not by datamodel-code-generator: every property key in the
document is already the final Python attribute name, and the original JSON key is returned in
``SerializedModels.field_mappings`` so the ``Meta`` class the cattrs runtime reads can be rendered.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.visit.model.enum_generator import EnumGenerator

from .literal_enums import EnumReferenceResolver

logger = logging.getLogger(__name__)

COMPONENTS_PREFIX = "#/components/schemas/"
_BASIC_TYPES = frozenset({"object", "array", "string", "integer", "number", "boolean", "null"})
_SCALAR_DEFAULT_TYPES = (str, int, float, bool)
_NO_DEFAULT: Any = object()


@dataclass(frozen=True)
class SerializedModels:
    """The document handed to datamodel-code-generator plus the facts needed to post-process its output."""

    document: dict[str, Any]
    """OpenAPI document whose ``components.schemas`` keys are the IR ``generation_name`` values."""

    field_mappings: dict[str, dict[str, str]]
    """Class name -> {JSON key: Python attribute name}, only for keys whose Python name differs."""

    field_names: dict[str, list[str]]
    """Class name -> expected Python attribute names in declaration order (used to verify the output)."""

    anonymous_objects_flattened: int = 0
    """Count of anonymous inline objects rendered as ``dict[str, Any]`` because they have no class to own a ``Meta``."""

    definitions: frozenset[str] = field(default_factory=frozenset)
    """Every class name that was emitted as a definition."""

    literal_enum_fields: frozenset[str] = frozenset()
    """
    Python attribute names of the properties whose enum was inlined, to be rendered as ``Literal[...]``.

    DCG matches its literal map against the final attribute name (after aliases), not the key in ``document``.
    """


class IRSchemaSerializer:
    """
    Converts a fixed set of named IR schemas to an OpenAPI document.

    Contracts:
        Preconditions:
            - every schema in ``named_schemas`` has a non-empty ``generation_name``
            - ``generation_name`` values are unique
        Postconditions:
            - ``document["components"]["schemas"]`` has exactly one entry per named schema
            - any schema reachable from a named schema that is itself named (and not excluded) is
              referenced with ``$ref`` rather than copied inline
    """

    def __init__(
        self,
        named_schemas: Sequence[IRSchema],
        keep_json_names: bool = False,
        literal_enums: Sequence[IRSchema] = (),
    ) -> None:
        """
        Args:
            named_schemas: The schemas to serialise as definitions.
            literal_enums: Enums that get no definition: every property that uses one is serialised with
                the enum values in place, and reported in ``SerializedModels.literal_enum_fields`` so the
                caller can ask DCG for a ``Literal`` there.
            keep_json_names: When False (dataclass models) object properties are renamed to their Python
                attribute names in the document and the mapping back is reported in ``field_mappings``.
                When True (pydantic models) the document keeps the JSON keys, and the caller passes
                ``field_mappings`` to DCG as aliases so it emits ``Field(alias=...)``.
        """
        names = [s.generation_name for s in named_schemas]
        assert all(
            names
        ), "every named schema must have a generation_name"  # nosec B101 - design-by-contract precondition; must stay active
        assert len(set(names)) == len(
            names
        ), "generation_name values must be unique"  # nosec B101 - design-by-contract precondition; must stay active

        self._schemas = list(named_schemas)
        self._keep_json_names = keep_json_names
        self._names_by_id: dict[int, str] = {id(s): s.generation_name for s in named_schemas if s.generation_name}
        self._names_by_ir_name = self._unambiguous_ir_names(named_schemas)
        self._literal_enums = EnumReferenceResolver(literal_enums)
        self._literal_fields: set[str] = set()
        self._stack: set[int] = set()
        self._field_mappings: dict[str, dict[str, str]] = {}
        self._field_names: dict[str, list[str]] = {}
        self._anonymous_objects = 0

    @staticmethod
    def _unambiguous_ir_names(schemas: Sequence[IRSchema]) -> dict[str, str]:
        """Map an IR ``name`` to its ``generation_name`` when exactly one schema carries that name."""
        seen: dict[str, list[str]] = {}
        for s in schemas:
            if s.name and s.generation_name:
                seen.setdefault(s.name, []).append(s.generation_name)
        return {name: gens[0] for name, gens in seen.items() if len(gens) == 1}

    def serialize(self) -> SerializedModels:
        """Build the OpenAPI document."""
        definitions: dict[str, Any] = {}
        for schema in sorted(self._schemas, key=lambda s: s.generation_name or ""):
            class_name = schema.generation_name
            assert class_name is not None  # nosec B101 - type narrowing; guaranteed by the constructor precondition
            self._stack = {id(schema)}
            definitions[class_name] = self._body(schema, owner=class_name)

        document = {
            "openapi": "3.1.0",
            "info": {"title": "pyopenapi-gen models", "version": "0"},
            "paths": {},
            "components": {"schemas": definitions},
        }
        assert set(definitions) == set(
            self._names_by_id.values()
        ), "one definition per named schema"  # nosec B101 - design-by-contract postcondition; must stay active
        return SerializedModels(
            document=document,
            field_mappings=self._field_mappings,
            field_names=self._field_names,
            anonymous_objects_flattened=self._anonymous_objects,
            definitions=frozenset(definitions),
            literal_enum_fields=frozenset(self._literal_fields),
        )

    # -- references ---------------------------------------------------------------------------

    def _definition_name(self, schema: IRSchema, _depth: int = 0) -> str | None:
        """Return the class name ``schema`` should be referenced by, if it is (or points at) a named model."""
        by_id = self._names_by_id.get(id(schema))
        if by_id is not None:
            return by_id
        linked = schema._refers_to_schema
        if linked is not None and _depth < 10:
            return self._definition_name(linked, _depth + 1)
        if schema.type and schema.type not in _BASIC_TYPES:
            return self._names_by_ir_name.get(schema.type)
        return None

    def _use_site(self, schema: IRSchema) -> dict[str, Any]:
        """Serialise ``schema`` where it is used: a ``$ref`` when it is a named model, else its structure."""
        target = self._definition_name(schema)
        if target is not None:
            node: dict[str, Any] = {"$ref": f"{COMPONENTS_PREFIX}{target}"}
        elif id(schema) in self._stack:
            node = {}  # Cyclic anonymous structure: nothing named to point at, so fall back to Any.
        else:
            self._stack.add(id(schema))
            try:
                node = self._body(schema, owner=None)
            finally:
                self._stack.discard(id(schema))
        return _make_nullable(node) if schema.is_nullable else node

    # -- bodies -------------------------------------------------------------------------------

    def _body(self, schema: IRSchema, owner: str | None) -> dict[str, Any]:
        """
        Serialise the structure of ``schema`` (no nullability, no ``$ref``).

        ``owner`` is the class name when ``schema`` is a definition and None when it is nested inline. Only
        definitions become enums: an anonymous inline enum is rendered as its primitive type (as legacy does),
        because handing DCG an unnamed enum makes it invent a class name that can collide with its parent.
        """
        body: dict[str, Any] = {}
        if schema.description:
            body["description"] = schema.description

        if schema.enum and schema.type in ("string", "integer") and owner is not None:
            body.update(self._enum_body(schema))
        elif schema.properties:
            body.update(self._object_body(schema, owner))
        elif schema.one_of or schema.any_of:
            body.update(self._union_body(schema))
        elif schema.all_of:
            body["allOf"] = [self._use_site(part) for part in schema.all_of]
        elif schema.type == "array":
            body.update({"type": "array", "items": self._use_site(schema.items) if schema.items else {}})
        elif schema.type == "object":
            body.update(self._free_form_body(schema))
        elif schema.type in _BASIC_TYPES and schema.type != "null":
            # ``null`` is deliberately absent: the parser uses it for "type unknown" and legacy renders it as Any.
            body["type"] = schema.type
            if schema.format:
                body["format"] = schema.format
        return body

    @staticmethod
    def _enum_body(schema: IRSchema) -> dict[str, Any]:
        """Enum values plus the member names legacy would generate (public API), via ``x-enum-varnames``."""
        names = EnumGenerator.member_names_by_value(schema)
        values = list(schema.enum or [])
        return {"type": schema.type, "enum": values, "x-enum-varnames": [names[v] for v in values]}

    def _free_form_body(self, schema: IRSchema) -> dict[str, Any]:
        extra = schema.additional_properties
        if isinstance(extra, IRSchema):
            return {"type": "object", "additionalProperties": self._use_site(extra)}
        if extra is True:
            return {"type": "object", "additionalProperties": True}
        return {"type": "object"}

    def _union_body(self, schema: IRSchema) -> dict[str, Any]:
        keyword = "oneOf" if schema.one_of else "anyOf"
        body: dict[str, Any] = {keyword: [self._use_site(v) for v in (schema.one_of or schema.any_of or [])]}
        discriminator = self._discriminator(schema)
        if discriminator:
            body["discriminator"] = discriminator
        return body

    def _discriminator(self, schema: IRSchema) -> dict[str, Any] | None:
        if schema.discriminator is None:
            return None
        result: dict[str, Any] = {"propertyName": schema.discriminator.property_name}
        mapping = {
            value: f"{COMPONENTS_PREFIX}{target}"
            for value, ref in (schema.discriminator.mapping or {}).items()
            if (target := self._mapping_target(ref)) is not None
        }
        if mapping:
            result["mapping"] = mapping
        return result

    def _mapping_target(self, ref: str) -> str | None:
        tail = ref.rsplit("/", 1)[-1]
        candidate = self._names_by_ir_name.get(NameSanitizer.sanitize_class_name(tail))
        if candidate is not None:
            return candidate
        return tail if tail in self._names_by_id.values() else None

    def _object_body(self, schema: IRSchema, owner: str | None) -> dict[str, Any]:
        """Serialise an object with properties; a class-less (anonymous) one degrades to ``dict[str, Any]``."""
        if owner is None:
            self._anonymous_objects += 1
            logger.debug("Anonymous object with properties rendered as dict[str, Any]: %s", schema.name)
            return {"type": "object"}

        ordered = self._python_field_names(owner, schema)
        properties: dict[str, Any] = {}
        for api_name, python_name in ordered:
            prop = schema.properties[api_name]
            literal_enum = self._literal_enums.resolve(prop)
            if literal_enum is not None:
                literal_body = _literal_enum_body(literal_enum)
                node = _make_nullable(literal_body) if prop.is_nullable else literal_body
                self._literal_fields.add(python_name)
            else:
                node = self._use_site(prop)
            if api_name not in schema.required:
                default = self._optional_field_default(prop, is_reference=self._definition_name(prop) is not None)
                if default is not _NO_DEFAULT:
                    node["default"] = default
            properties[api_name if self._keep_json_names else python_name] = node

        self._field_names[owner] = [python for _, python in ordered]
        self._field_mappings[owner] = {api: py for api, py in ordered if api != py}
        body: dict[str, Any] = {"type": "object", "properties": properties}
        required = [api if self._keep_json_names else py for api, py in ordered if api in schema.required]
        if required:
            body["required"] = required
        return body

    @staticmethod
    def _optional_field_default(prop: IRSchema, is_reference: bool) -> Any:
        """
        The default for an optional field, following the legacy ``DataclassGenerator`` rules.

        Arrays default to an empty list and anonymous objects to an empty dict (DCG renders these as
        ``field(default_factory=...)``); otherwise only scalar defaults are carried over. A reference to a
        named model never gets ``{}``, because that would not be a valid value of the referenced type.
        """
        if prop.type == "array":
            return []
        if (
            prop.type == "object"
            and not is_reference
            and prop.name is None
            and not (prop.any_of or prop.one_of or prop.all_of)
        ):
            return {}
        if isinstance(prop.default, _SCALAR_DEFAULT_TYPES):
            return prop.default
        return _NO_DEFAULT

    @staticmethod
    def _python_field_names(owner: str, schema: IRSchema) -> list[tuple[str, str]]:
        """
        Pair each JSON property key with its Python attribute name, in declaration order.

        Order (required first, then alphabetical) and collision suffixes (``name_2``) follow the
        legacy ``DataclassGenerator`` so field names and positional-argument order do not change.
        """
        ordered_keys = sorted(schema.properties, key=lambda key: (key not in schema.required, key))
        used: dict[str, str] = {}
        pairs: list[tuple[str, str]] = []
        for api_name in ordered_keys:
            python_name = NameSanitizer.sanitize_method_name(api_name)
            if python_name in used:
                base, suffix = python_name, 2
                while python_name in used:
                    python_name = f"{base}_{suffix}"
                    suffix += 1
                logger.warning(
                    f"Field name collision in schema '{owner}': '{used[base]}' and '{api_name}' both sanitize to "
                    f"'{base}'. Using '{python_name}' for '{api_name}'."
                )
            used[python_name] = api_name
            pairs.append((api_name, python_name))
        return pairs


def _literal_enum_body(enum: IRSchema) -> dict[str, Any]:
    """An enum's values in place of a ``$ref``; DCG renders it as a ``Literal`` when the field is in the literal map."""
    return {"type": enum.type, "enum": list(enum.enum or [])}


def _make_nullable(node: dict[str, Any]) -> dict[str, Any]:
    """Allow ``null`` in addition to whatever ``node`` describes."""
    if not node:
        return node  # ``{}`` already means Any
    plain_type = node.get("type")
    structural = any(key in node for key in ("$ref", "oneOf", "anyOf", "allOf", "enum", "properties"))
    if isinstance(plain_type, str) and not structural:
        return {**node, "type": [plain_type, "null"]}
    return {"anyOf": [node, {"type": "null"}]}
