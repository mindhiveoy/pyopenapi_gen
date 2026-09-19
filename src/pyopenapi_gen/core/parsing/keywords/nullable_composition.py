"""
Detection of composition nodes that merely wrap a single subschema.

OpenAPI has no direct spelling for "a nullable reference to a component", so both
major versions express it by wrapping the reference:

* 3.0 forbids siblings next to ``$ref``, so the idiom is a single-element
  ``allOf`` carrying the ``nullable`` flag::

      {"nullable": true, "allOf": [{"$ref": "#/components/schemas/Reason"}]}

* 3.1 drops ``nullable`` in favour of the JSON Schema null type::

      {"anyOf": [{"$ref": "#/components/schemas/Reason"}, {"type": "null"}]}

Both denote the referenced type with nullability applied - not a new anonymous
object. Treating them as objects mints an empty (or cloned) model per field, so
the parser unwraps them before deciding on names and types.
"""

from __future__ import annotations

from typing import Any, List, Mapping, Tuple

# Keywords that give a node content of its own. A wrapper may carry none of these
# beyond the single composition keyword it is built from; anything else means the
# node genuinely composes or constrains, and must be parsed as a schema.
_STRUCTURAL_KEYWORDS = frozenset(
    {
        "type",
        "properties",
        "items",
        "prefixItems",
        "enum",
        "const",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "additionalProperties",
        "patternProperties",
        "unevaluatedProperties",
        "required",
        "discriminator",
        "format",
        "$ref",
    }
)

_COMPOSITION_KEYWORDS = ("allOf", "anyOf", "oneOf")

# Keywords that annotate a schema without changing its shape, and that the IR can
# carry. OpenAPI 3.0 forbids any sibling beside ``$ref``; 3.1 allows them, and they
# describe the use site rather than the component being referenced.
# `deprecated`, `readOnly` and `writeOnly` are deliberately absent: the IR has
# nowhere to put them, so honouring them would only change the shape of the IR
# without preserving anything.
_ANNOTATION_KEYWORDS = frozenset({"nullable", "description", "title", "default", "example", "examples"})


def _is_null_member(node: Any) -> bool:
    """Is this subschema the JSON Schema null type (the 3.1 nullability marker)?"""
    if not isinstance(node, Mapping):
        return False
    node_type = node.get("type")
    if node_type == "null":
        return True
    return isinstance(node_type, list) and set(node_type) == {"null"}


def _sole_composition_keyword(node: Mapping[str, Any]) -> str | None:
    """The one composition keyword in ``node``, or None if there are zero or many."""
    present = [kw for kw in _COMPOSITION_KEYWORDS if kw in node]
    return present[0] if len(present) == 1 else None


def unwrap_nullable_composition(node: Any) -> Tuple[Mapping[str, Any], bool] | None:
    """Unwrap a composition node that only wraps a single subschema.

    Args:
        node: A raw OpenAPI schema node.

    Returns:
        ``(inner_node, is_nullable)`` when ``node`` is such a wrapper, else None.
        ``inner_node`` is the wrapped subschema exactly as written in the spec;
        ``is_nullable`` folds together the ``nullable`` flag and any ``{"type": "null"}``
        member.

    Contracts:
        Post-conditions:
            - The returned inner node is one of the node's own subschemas.
            - Returns None for genuine unions, genuine allOf merges, and for any
              node carrying structural keywords of its own.
    """
    if not isinstance(node, Mapping):
        return None

    is_nullable = node.get("nullable") is True

    # `$ref` with a sibling `nullable` flag: not valid 3.0, but emitted in the wild.
    if "$ref" in node:
        if not is_nullable:
            return None
        extra_structural = _STRUCTURAL_KEYWORDS.intersection(node) - {"$ref"}
        if extra_structural:
            return None
        return {"$ref": node["$ref"]}, True

    keyword = _sole_composition_keyword(node)
    if keyword is None:
        return None

    # Anything structural beyond the composition keyword itself means the node
    # contributes content and cannot be collapsed to its single member.
    if _STRUCTURAL_KEYWORDS.intersection(node) - {keyword}:
        return None

    members = node[keyword]
    if not isinstance(members, list):
        return None

    non_null_members: List[Mapping[str, Any]] = []
    for member in members:
        if _is_null_member(member):
            is_nullable = True
        elif isinstance(member, Mapping):
            non_null_members.append(member)
        else:
            return None

    # Exactly one real subschema is what makes this a wrapper rather than a union.
    if len(non_null_members) != 1:
        return None

    return non_null_members[0], is_nullable


def _has_ref_siblings(node: Any) -> bool:
    """Does this ``$ref`` carry annotations of its own?

    A bare ``$ref`` is interchangeable with its target, so it can resolve straight
    to the shared schema. One carrying annotations cannot: those belong to this use
    site alone, and writing them onto the shared target would leak them into every
    other reference to the same component.
    """
    if not isinstance(node, Mapping) or "$ref" not in node:
        return False
    return bool(_ANNOTATION_KEYWORDS.intersection(node))


def is_annotated_ref_node(node: Any) -> bool:
    """Is this node itself a ``$ref`` that carries annotations of its own?

    Answers one question for callers holding a ``$ref`` node: may it resolve straight
    to its shared target, or does it need a holder for its own annotations? False for
    a bare ``$ref``, and false for a ``$ref`` beside structural keywords - an
    intersection this module does not model, which must fall back to the plain
    reference path rather than be dropped.

    Wrapper nodes such as ``{"nullable": true, "allOf": [{"$ref": ...}]}`` are not
    ``$ref`` nodes and are false here; they are handled by
    :func:`resolve_reference_wrapper`.
    """
    return _has_ref_siblings(node) and resolve_reference_wrapper(node) is not None


def resolve_reference_wrapper(node: Any) -> Tuple[str, bool] | None:
    """Follow wrapper layers down to the ``$ref`` they ultimately denote.

    Args:
        node: A raw OpenAPI schema node.

    Returns:
        ``(ref_path, is_nullable)`` when ``node`` is a bare ``$ref`` or a chain of
        wrappers around one, else None. ``is_nullable`` is true if any layer in the
        chain marked the reference nullable.

    Contracts:
        Post-conditions:
            - Returns None whenever the node introduces structure of its own, so
              genuine objects, unions and allOf merges are never collapsed.
    """
    current: Any = node
    is_nullable = False
    # Each iteration strips one wrapper layer, so this terminates on the node's depth.
    while isinstance(current, Mapping):
        if "$ref" in current and not _STRUCTURAL_KEYWORDS.intersection(current) - {"$ref"}:
            ref_path = current["$ref"]
            if not isinstance(ref_path, str):
                return None
            return ref_path, is_nullable or current.get("nullable") is True
        unwrapped = unwrap_nullable_composition(current)
        if unwrapped is None:
            return None
        current, layer_nullable = unwrapped
        is_nullable = is_nullable or layer_nullable
    return None


def is_reference_like_node(node: Any) -> bool:
    """Does this node denote an existing component rather than a new schema?

    True for a bare ``$ref`` and for any wrapper that bottoms out at one. Such
    nodes must not be given a synthetic name, because doing so registers - and
    emits - a standalone model that merely duplicates the referenced component.
    """
    return resolve_reference_wrapper(node) is not None


def merge_wrapper_annotations(
    wrapper_node: Mapping[str, Any], inner_node: Mapping[str, Any], is_nullable: bool
) -> dict[str, Any]:
    """Fold a wrapper's nullability and annotations into the subschema it wraps.

    Used when the wrapped subschema is inline rather than a ``$ref``: the result is
    parsed as though the spec had written the inner schema directly.
    """
    merged: dict[str, Any] = dict(inner_node)
    if is_nullable:
        merged["nullable"] = True
    for key in ("description", "title", "default", "example", "examples", "deprecated", "readOnly", "writeOnly"):
        if key in wrapper_node and key not in merged:
            merged[key] = wrapper_node[key]
    return merged
