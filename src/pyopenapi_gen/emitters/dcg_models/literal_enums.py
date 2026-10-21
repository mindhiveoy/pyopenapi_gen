"""
Decide which enums datamodel-code-generator should render as ``Literal[...]`` instead of ``Enum`` classes.

An enum the spec author wrote inline on a property (``status: {type: string, enum: [...]}``) has no name of
its own in the spec; the generator invents ``<Schema><Property>`` for it. Such an enum is clearer as a
``Literal`` on the field. That is only safe when nothing else needs a class for it, so an enum qualifies
when it is generator-named, used as a plain property of a rendered model, and used nowhere else (not as a
list item, a union member, or anywhere in an operation signature).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from pyopenapi_gen.ir import IROperation, IRSchema

_LITERAL_TYPES = frozenset({"string", "integer"})
_MAX_REFERENCE_DEPTH = 10


def is_literal_candidate(schema: IRSchema) -> bool:
    """True for an enum the generator, not the spec author, named."""
    return bool(schema.enum) and schema.type in _LITERAL_TYPES and schema._is_name_derived and bool(schema.name)


class EnumReferenceResolver:
    """
    Finds which of a fixed set of schemas a use site points at.

    A use site points at a schema directly (same object), through ``_refers_to_schema``, or by naming it in
    ``type`` (the shape ``extract_inline_enums`` leaves on a property).
    """

    def __init__(self, targets: Iterable[IRSchema]) -> None:
        self._by_id = {id(t): t for t in targets}
        by_name: dict[str, list[IRSchema]] = {}
        for target in self._by_id.values():
            if target.name:
                by_name.setdefault(target.name, []).append(target)
        self._by_name = {name: found[0] for name, found in by_name.items() if len(found) == 1}

    def resolve(self, schema: IRSchema, _depth: int = 0) -> IRSchema | None:
        """The target ``schema`` points at, or None."""
        found = self._by_id.get(id(schema))
        if found is not None:
            return found
        if schema._refers_to_schema is not None and _depth < _MAX_REFERENCE_DEPTH:
            return self.resolve(schema._refers_to_schema, _depth + 1)
        if schema.type:
            return self._by_name.get(schema.type)
        return None


def find_literal_enums(named_schemas: Sequence[IRSchema], operations: Sequence[IROperation]) -> list[IRSchema]:
    """
    The enums among ``named_schemas`` that can be rendered as literals on their fields.

    Contracts:
        Preconditions:
            - ``named_schemas`` are the schemas rendered as models (each has a ``generation_name``)
        Postconditions:
            - every returned schema is generator-named and referenced as a direct property of at least one
              other schema in ``named_schemas``
            - no returned schema is referenced in any other position, including by ``operations``
    """
    candidates = [s for s in named_schemas if is_literal_candidate(s)]
    if not candidates:
        return []

    candidate_ids = {id(c) for c in candidates}
    other_models = [s for s in named_schemas if id(s) not in candidate_ids]
    enums = EnumReferenceResolver(candidates)
    models = EnumReferenceResolver(other_models)
    used_as_property: set[int] = set()
    used_elsewhere: set[int] = set()

    def visit_anonymous(schema: IRSchema, seen: set[int]) -> None:
        """Every reference to a candidate reached through ``schema`` disqualifies it."""
        enum = enums.resolve(schema)
        if enum is not None:
            used_elsewhere.add(id(enum))
            return
        if models.resolve(schema) is not None or id(schema) in seen:
            return  # A rendered model's own slots are visited when that model is
        seen.add(id(schema))
        visit_slots(schema, seen, property_use_allowed=False)

    def visit_slots(schema: IRSchema, seen: set[int], property_use_allowed: bool) -> None:
        properties, others = _rendered_slots(schema)
        for prop in properties:
            enum = enums.resolve(prop)
            if enum is not None and property_use_allowed:
                used_as_property.add(id(enum))
            else:
                visit_anonymous(prop, seen)
        for child in others:
            visit_anonymous(child, seen)

    for model in other_models:
        visit_slots(model, {id(model)}, property_use_allowed=True)
    for operation in operations:
        for operation_schema in _operation_schemas(operation):
            visit_anonymous(operation_schema, set())

    return [c for c in candidates if id(c) in used_as_property and id(c) not in used_elsewhere]


def _rendered_slots(schema: IRSchema) -> tuple[list[IRSchema], list[IRSchema]]:
    """
    The sub-schemas the serializer renders for ``schema``: (object properties, every other member).

    Mirrors the precedence in ``IRSchemaSerializer._body`` - merged ``properties`` win over compositions,
    so an ``allOf`` whose members were already merged into ``properties`` contributes nothing of its own.
    """
    if schema.properties:
        return list(schema.properties.values()), []
    if schema.one_of or schema.any_of:
        return [], list(schema.one_of or schema.any_of or [])
    if schema.all_of:
        return [], list(schema.all_of)
    if schema.type == "array":
        return [], [schema.items] if schema.items is not None else []
    if schema.type == "object" and isinstance(schema.additional_properties, IRSchema):
        return [], [schema.additional_properties]
    return [], []


def _operation_schemas(operation: IROperation) -> Iterable[IRSchema]:
    for parameter in operation.parameters:
        yield parameter.schema
    if operation.request_body is not None:
        yield from operation.request_body.content.values()
    for response in operation.responses:
        yield from response.content.values()
