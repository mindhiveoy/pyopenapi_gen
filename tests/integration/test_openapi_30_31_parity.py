"""End-to-end parity between the OpenAPI 3.0 and 3.1 spellings of the same schemas.

Each version spells "a nullable reference to a component" differently - 3.0 wraps
the ``$ref`` in a single-element ``allOf`` beside a ``nullable`` flag, 3.1 puts it
in an ``anyOf`` next to ``{"type": "null"}``. Both must produce the referenced type
with ``| None``, and neither may mint a model file for the field.
"""

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from pyopenapi_gen.generator.client_generator import ClientGenerator

REASON: dict[str, Any] = {"type": "string", "enum": ["unpricedSpend", "missingRate"]}
THING: dict[str, Any] = {"type": "object", "properties": {"id": {"type": "string"}}}

# The same API, written once per OpenAPI version.
PROBE_PROPERTIES_30: dict[str, Any] = {
    "plainRef": {"$ref": "#/components/schemas/Reason"},
    "nullablePrimitive": {"type": "string", "nullable": True},
    "nullableEnumRef": {"nullable": True, "allOf": [{"$ref": "#/components/schemas/Reason"}]},
    "nullableObjectRef": {"nullable": True, "allOf": [{"$ref": "#/components/schemas/Thing"}]},
    "aliasRef": {"allOf": [{"$ref": "#/components/schemas/Thing"}]},
    "nullableRefArray": {
        "type": "array",
        "items": {"nullable": True, "allOf": [{"$ref": "#/components/schemas/Thing"}]},
    },
    "binaryBlob": {"type": "string", "format": "binary"},
}

PROBE_PROPERTIES_31: dict[str, Any] = {
    "plainRef": {"$ref": "#/components/schemas/Reason"},
    "nullablePrimitive": {"type": ["string", "null"]},
    "nullableEnumRef": {"anyOf": [{"$ref": "#/components/schemas/Reason"}, {"type": "null"}]},
    "nullableObjectRef": {"oneOf": [{"$ref": "#/components/schemas/Thing"}, {"type": "null"}]},
    "aliasRef": {"allOf": [{"$ref": "#/components/schemas/Thing"}]},
    "nullableRefArray": {
        "type": "array",
        "items": {"anyOf": [{"$ref": "#/components/schemas/Thing"}, {"type": "null"}]},
    },
    "binaryBlob": {"type": "string", "contentMediaType": "application/octet-stream"},
}

# What every property must resolve to, in both versions.
EXPECTED_ANNOTATIONS: dict[str, str] = {
    "plain_ref": "Reason",
    "nullable_primitive": "str | None",
    "nullable_enum_ref": "Reason | None",
    "nullable_object_ref": "Thing | None",
    "alias_ref": "Thing",
    "nullable_ref_array": "List[Thing | None]",
    "binary_blob": "bytes",
}

# Only the components the spec actually declares deserve a module.
EXPECTED_MODEL_MODULES = {"__init__.py", "py.typed", "probe.py", "reason.py", "thing.py"}


def _spec(openapi_version: str, probe_properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "openapi": openapi_version,
        "info": {"title": "Parity probe", "version": "1.0.0"},
        "paths": {
            "/probe": {
                "get": {
                    "operationId": "getProbe",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Probe"}}},
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "Reason": REASON,
                "Thing": THING,
                "Probe": {
                    "type": "object",
                    "properties": probe_properties,
                    "required": sorted(probe_properties),
                },
            }
        },
    }


def _generate(tmp_path: Path, spec: dict[str, Any]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))
    ClientGenerator().generate(
        spec_path=str(spec_file),
        project_root=tmp_path,
        output_package="probe_client",
        force=True,
        no_postprocess=True,
    )
    return tmp_path / "probe_client"


def _field_annotations(model_source: str) -> dict[str, str]:
    """Map field name to annotation for the annotated fields in a generated module.

    Parsed rather than pattern-matched, so formatter line wrapping cannot affect it.
    """
    annotations: dict[str, str] = {}
    for node in ast.walk(ast.parse(model_source)):
        if not isinstance(node, ast.ClassDef):
            continue
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                annotations[statement.target.id] = ast.unparse(statement.annotation)
    return annotations


@pytest.mark.parametrize(
    "openapi_version, probe_properties",
    [
        pytest.param("3.0.3", PROBE_PROPERTIES_30, id="openapi-3.0"),
        pytest.param("3.1.0", PROBE_PROPERTIES_31, id="openapi-3.1"),
    ],
)
def test_client_generation__nullable_refs__resolve_to_referenced_types(
    tmp_path: Path, openapi_version: str, probe_properties: dict[str, Any]
) -> None:
    # Arrange / Act
    client_dir = _generate(tmp_path, _spec(openapi_version, probe_properties))
    annotations = _field_annotations((client_dir / "models" / "probe.py").read_text())

    # Assert
    for field_name, expected in EXPECTED_ANNOTATIONS.items():
        assert annotations.get(field_name) == expected, f"{field_name} in OpenAPI {openapi_version}"


@pytest.mark.parametrize(
    "openapi_version, probe_properties",
    [
        pytest.param("3.0.3", PROBE_PROPERTIES_30, id="openapi-3.0"),
        pytest.param("3.1.0", PROBE_PROPERTIES_31, id="openapi-3.1"),
    ],
)
def test_client_generation__nullable_refs__emit_no_per_field_models(
    tmp_path: Path, openapi_version: str, probe_properties: dict[str, Any]
) -> None:
    # Arrange / Act
    client_dir = _generate(tmp_path, _spec(openapi_version, probe_properties))

    # Assert: no ProbeNullableEnumRef-style module duplicating a component.
    assert {path.name for path in (client_dir / "models").iterdir()} == EXPECTED_MODEL_MODULES


def test_client_generation__equivalent_30_and_31_specs__produce_identical_models(tmp_path: Path) -> None:
    # Arrange / Act
    dir_30 = _generate(tmp_path / "v30", _spec("3.0.3", PROBE_PROPERTIES_30))
    dir_31 = _generate(tmp_path / "v31", _spec("3.1.0", PROBE_PROPERTIES_31))

    # Assert: the two spellings of the same API generate the same model code.
    assert _field_annotations((dir_30 / "models" / "probe.py").read_text()) == _field_annotations(
        (dir_31 / "models" / "probe.py").read_text()
    )


def test_client_generation__ref_with_sibling_description__documents_the_use_site(tmp_path: Path) -> None:
    """OpenAPI 3.1 allows annotations beside `$ref`; they describe the field, not the component."""
    # Arrange
    spec = _spec(
        "3.1.0",
        {
            "annotatedRef": {
                "$ref": "#/components/schemas/Thing",
                "description": "Metadata for this page of results.",
            },
            "plainRef": {"$ref": "#/components/schemas/Thing"},
        },
    )
    spec["components"]["schemas"]["Thing"] = {**THING, "description": "A thing."}

    # Act
    client_dir = _generate(tmp_path, spec)
    probe_source = (client_dir / "models" / "probe.py").read_text()
    thing_source = (client_dir / "models" / "thing.py").read_text()

    # Assert: both fields keep the referenced type...
    annotations = _field_annotations(probe_source)
    assert annotations["annotated_ref"] == "Thing"
    assert annotations["plain_ref"] == "Thing"
    # ...the sibling description reaches the annotated field only...
    assert "Metadata for this page of results." in probe_source
    # ...and the component keeps its own description, unpolluted by the use site.
    assert "A thing." in thing_source
    assert "Metadata for this page of results." not in thing_source
