"""End-to-end parity between the OpenAPI 3.0 and 3.1 spellings of the same schemas.

Each version spells "a nullable reference to a component" differently - 3.0 wraps
the ``$ref`` in a single-element ``allOf`` beside a ``nullable`` flag, 3.1 puts it
in an ``anyOf`` next to ``{"type": "null"}``. Both must produce the referenced type
with ``| None``, and neither may mint a model file for the field.
"""

import ast
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from pyopenapi_gen.core.utils import NameSanitizer
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


@pytest.mark.parametrize(
    "openapi_version, maybe_thing",
    [
        pytest.param("3.0.3", {"nullable": True, "allOf": [{"$ref": "#/components/schemas/Thing"}]}, id="openapi-3.0"),
        pytest.param(
            "3.1.0",
            {"anyOf": [{"$ref": "#/components/schemas/Thing"}, {"type": "null"}]},
            id="openapi-3.1",
        ),
    ],
)
def test_client_generation__named_nullable_ref_component__aliases_the_referenced_model(
    tmp_path: Path, openapi_version: str, maybe_thing: dict[str, Any]
) -> None:
    """A component that is itself a nullable reference aliases its target, not a dict."""
    # Arrange
    spec = _spec(openapi_version, {"maybeThing": {"$ref": "#/components/schemas/MaybeThing"}})
    spec["components"]["schemas"]["MaybeThing"] = maybe_thing

    # Act
    client_dir = _generate(tmp_path, spec)
    alias_source = (client_dir / "models" / "maybe_thing.py").read_text()

    # Assert
    assert "MaybeThing: TypeAlias = Thing | None" in alias_source
    assert "dict[str, Any]" not in alias_source


def test_client_generation__colliding_sanitized_names__each_alias_keeps_its_own_target(tmp_path: Path) -> None:
    """Two spec names that sanitize alike must not collapse into one another's type."""
    # Arrange: "Foo-Bar" and "FooBar" both sanitize to FooBar; the first is a
    # nullable reference to Thing, the second an unrelated object.
    spec = _spec(
        "3.0.3",
        {
            "real": {"$ref": "#/components/schemas/FooBar"},
            "aliased": {"$ref": "#/components/schemas/Foo-Bar"},
        },
    )
    spec["components"]["schemas"]["FooBar"] = {"type": "object", "properties": {"real": {"type": "string"}}}
    spec["components"]["schemas"]["Foo-Bar"] = {
        "nullable": True,
        "allOf": [{"$ref": "#/components/schemas/Thing"}],
    }

    # Act
    client_dir = _generate(tmp_path, spec)
    aliases = {
        path.name: path.read_text() for path in (client_dir / "models").iterdir() if path.name.startswith("foo_bar")
    }

    # Assert: both survive de-collision, and the alias still points at Thing rather
    # than silently adopting the other schema's shape.
    assert len(aliases) == 2, sorted(aliases)
    alias_source = next(source for source in aliases.values() if "TypeAlias" in source)
    assert "Thing | None" in alias_source
    assert "dict[str, Any]" not in alias_source


def _json_value_spec(component_name: str, null_member: dict[str, Any] | None = None) -> dict[str, Any]:
    """An API whose payloads carry arbitrary JSON: the recursive anyOf zod-openapi emits for z.json()."""
    ref = {"$ref": f"#/components/schemas/{component_name}"}
    members: list[dict[str, Any]] = [{"type": "string"}, {"type": "number"}, {"type": "boolean"}]
    if null_member is not None:
        members.append(null_member)
    members += [{"type": "array", "items": ref}, {"type": "object", "additionalProperties": ref}]
    run_request_ref = {"$ref": "#/components/schemas/RunRequest"}
    return {
        "openapi": "3.1.0",
        "info": {"title": "JSON value probe", "version": "1.0.0"},
        "paths": {
            "/echo": {
                "post": {
                    "operationId": "echo",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": run_request_ref}}},
                    "responses": {
                        "200": {"description": "ok", "content": {"application/json": {"schema": run_request_ref}}}
                    },
                }
            }
        },
        "components": {
            "schemas": {
                component_name: {"anyOf": members},
                "RunRequest": {
                    "type": "object",
                    "required": ["inputs", "single"],
                    "properties": {"inputs": {"type": "object", "additionalProperties": ref}, "single": ref},
                },
            }
        },
    }


def _flatten_union(node: ast.expr) -> list[str]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _flatten_union(node.left) + _flatten_union(node.right)
    if isinstance(node, ast.Subscript) and ast.unparse(node.value) == "Union":
        elements = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        return [member for element in elements for member in _flatten_union(element)]
    return [ast.unparse(node)]


def _alias_union_members(module_source: str, alias_name: str) -> list[str]:
    """The members of ``alias_name: TypeAlias = Union[...]`` (or ``... | None``), as source text, in order."""
    for node in ast.parse(module_source).body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == alias_name
            and node.value is not None
        ):
            return _flatten_union(node.value)
    raise AssertionError(f"No alias {alias_name!r} in:\n{module_source}")


@pytest.mark.parametrize("component_name", ["__schema0", "json_value", "Json-Value", "JsonValue"])
def test_client_generation__recursive_anyof_component__emits_one_alias_whatever_its_spec_name(
    tmp_path: Path, component_name: str
) -> None:
    """A self-referencing anyOf becomes one recursive alias, however its spec key is spelled.

    A key that is not already a valid class name used to leave the parser's self-reference
    stub in place: every $ref resolved to an empty dataclass, and the real union was written
    to a second, colliding module that nothing referenced.
    """
    # Arrange
    class_name = NameSanitizer.sanitize_class_name(component_name)
    module_stem = NameSanitizer.sanitize_module_name(component_name)

    # Act
    client_dir = _generate(tmp_path, _json_value_spec(component_name))
    models = {path.name: path.read_text() for path in (client_dir / "models").iterdir() if path.suffix == ".py"}

    # Assert
    assert {name for name in models if name.startswith(module_stem)} == {f"{module_stem}.py"}
    assert not any("Self-referencing schema" in source for source in models.values())
    assert _alias_union_members(models[f"{module_stem}.py"], class_name) == [
        "str",
        "float",
        "bool",
        f"List['{class_name}']",
        "dict[str, Any]",
    ]
    assert _field_annotations(models["run_request.py"])["single"] == class_name
    assert _field_annotations(models["run_request_inputs.py"])["_data"] == f"dict[str, {class_name}]"


@pytest.mark.parametrize(
    "null_member",
    [
        pytest.param({"type": "null"}, id="3.1-null-type"),
        pytest.param({"type": "string", "nullable": True, "enum": [None]}, id="3.0-nullable-enum-null"),
        pytest.param({"nullable": True}, id="3.0-bare-nullable"),
    ],
)
def test_client_generation__anyof_null_member__keeps_none_in_the_union(
    tmp_path: Path, null_member: dict[str, Any]
) -> None:
    """Every spelling of a null member reaches the generated Union as None."""
    # Act
    client_dir = _generate(tmp_path, _json_value_spec("JsonValue", null_member))

    # Assert: None is present, and the null member did not collapse into the plain str member.
    members = _alias_union_members((client_dir / "models" / "json_value.py").read_text(), "JsonValue")
    assert members == ["str", "float", "bool", "List['JsonValue']", "dict[str, Any]", "None"]


def _mypy_strict(project_root: Path, package: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(project_root)}
    return subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", "-p", package],
        capture_output=True,
        text=True,
        env=env,
        cwd=project_root,
    )


@pytest.mark.parametrize(
    "component_name, null_member",
    [
        pytest.param("__schema0", None, id="unsanitised-name"),
        pytest.param("JsonValue", {"type": "string", "nullable": True, "enum": [None]}, id="nullable-alias"),
    ],
)
def test_client_generation__json_value_client__passes_strict_mypy(
    tmp_path: Path, component_name: str, null_member: dict[str, Any] | None
) -> None:
    """The recursive alias and the typed dict wrapper around it must type-check under mypy --strict.

    The wrapper's structure hook used to hand the Union alias itself to cattrs, whose
    parameter is ``type[T]``; mypy rejects a Union there.
    """
    # Arrange / Act
    _generate(tmp_path, _json_value_spec(component_name, null_member))
    result = _mypy_strict(tmp_path, "probe_client")

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr


def _binding_spec() -> dict[str, Any]:
    """`Binding = oneOf[RegisteredBinding (kind-discriminated oneOf), UnregisteredBinding]`."""
    ref = {"$ref": "#/components/schemas/Request"}
    return {
        "openapi": "3.1.0",
        "info": {"title": "Binding probe", "version": "1.0.0"},
        "paths": {
            "/echo": {
                "post": {
                    "operationId": "echo",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": ref}}},
                    "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": ref}}}},
                }
            }
        },
        "components": {
            "schemas": {
                "ConnectorBinding": {
                    "type": "object",
                    "required": ["kind", "connectorId"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["connector"]},
                        "connectorId": {"type": "string"},
                    },
                },
                "DataSourceBinding": {
                    "type": "object",
                    "required": ["kind", "dataSourceId"],
                    "properties": {
                        "kind": {"type": "string", "enum": ["dataSource"]},
                        "dataSourceId": {"type": "string"},
                    },
                },
                "UnregisteredBinding": {
                    "type": "object",
                    "required": ["kind"],
                    "properties": {"kind": {"type": "string"}},
                },
                "RegisteredBinding": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/ConnectorBinding"},
                        {"$ref": "#/components/schemas/DataSourceBinding"},
                    ],
                    "discriminator": {
                        "propertyName": "kind",
                        "mapping": {
                            "connector": "#/components/schemas/ConnectorBinding",
                            "dataSource": "#/components/schemas/DataSourceBinding",
                        },
                    },
                },
                "Binding": {
                    "oneOf": [
                        {"$ref": "#/components/schemas/RegisteredBinding"},
                        {"$ref": "#/components/schemas/UnregisteredBinding"},
                    ]
                },
                "Request": {
                    "type": "object",
                    "required": ["binding"],
                    "properties": {"binding": {"$ref": "#/components/schemas/Binding"}},
                },
            }
        },
    }


def test_client_generation__nested_discriminated_union_beside_fallback__structures_typed_members(
    tmp_path: Path,
) -> None:
    """The generated converter must pick the typed member for a known kind and the fallback only for an unknown one."""
    # Arrange
    _generate(tmp_path, _binding_spec())
    script = (
        "import json\n"
        "from probe_client.core.cattrs_converter import structure_from_dict\n"
        "from probe_client.models import Request\n"
        "payloads = [{'kind': 'connector', 'connectorId': 'c1'}, {'kind': 'dataSource', 'dataSourceId': 'd1'}, {'kind': 'other'}]\n"
        "print(json.dumps([type(structure_from_dict({'binding': p}, Request).binding).__name__ for p in payloads]))\n"
    )

    # Act
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        cwd=tmp_path,
    )

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == ["ConnectorBinding", "DataSourceBinding", "UnregisteredBinding"]


def test_client_generation__json_value_client__round_trips_every_json_type_at_runtime(tmp_path: Path) -> None:
    """Structuring `dict[str, JsonValue]` through the generated converter keeps every value's type.

    Would have caught 5.1.14, where the union's `str` member swallowed numbers, booleans
    and arrays via cattrs' default `str(value)` coercion.
    """
    # Arrange
    _generate(tmp_path, _json_value_spec("JsonValue", {"type": "null"}))
    script = (
        "import json\n"
        "from probe_client.core.cattrs_converter import structure_from_dict, unstructure_to_dict\n"
        "from probe_client.models import RunRequest\n"
        "payload = {'inputs': {'s': 'text', 'n': 1.5, 'i': 3, 'b': True, 'z': None,"
        " 'arr': [1, 'two', [3.5, None]], 'obj': {'k': {'deep': [True]}}}, 'single': [1.5, 'x']}\n"
        "req = structure_from_dict(payload, RunRequest)\n"
        "types = {k: type(v).__name__ for k, v in req.inputs.items()}\n"
        "print(json.dumps({'types': types, 'round_trip': unstructure_to_dict(req) == payload}))\n"
    )

    # Act
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        cwd=tmp_path,
    )

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
    outcome = json.loads(result.stdout)
    assert outcome["types"] == {
        "s": "str",
        "n": "float",
        "i": "int",
        "b": "bool",
        "z": "NoneType",
        "arr": "list",
        "obj": "dict",
    }
    assert outcome["round_trip"] is True


def _filter_value_spec() -> dict[str, Any]:
    """The sales team's ResourceFilterValue / WorkflowJsonValue shapes, reduced to the minimum."""
    ref = {"$ref": "#/components/schemas/Request"}
    return {
        "openapi": "3.1.0",
        "info": {"title": "Filter probe", "version": "1.0.0"},
        "paths": {
            "/echo": {
                "post": {
                    "operationId": "echo",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": ref}}},
                    "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": ref}}}},
                }
            }
        },
        "components": {
            "schemas": {
                "Principal": {
                    "type": "object",
                    "required": ["kind"],
                    "properties": {"kind": {"type": "string"}, "userId": {"type": "string"}},
                },
                "ListValue": {"anyOf": [{"type": "string"}, {"type": "number"}]},
                "FilterValue": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "number"},
                        {"type": "boolean"},
                        {"type": "array", "items": {"$ref": "#/components/schemas/ListValue"}},
                        {"$ref": "#/components/schemas/Principal"},
                        {"type": "array", "items": {"$ref": "#/components/schemas/Principal"}},
                    ]
                },
                "OpenValue": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "number"},
                        {"type": "boolean"},
                        {"type": "array", "items": {}},
                    ]
                },
                "Request": {
                    "type": "object",
                    "required": ["filter", "open"],
                    "properties": {
                        "filter": {"$ref": "#/components/schemas/FilterValue"},
                        "open": {"$ref": "#/components/schemas/OpenValue"},
                    },
                },
            }
        },
    }


def test_client_generation__open_array_items__emit_list_of_any(tmp_path: Path) -> None:
    """`items: {}` is an open array, so its alias member is `List[Any]`, not `List[dict[str, Any]]`."""
    # Act
    client_dir = _generate(tmp_path, _filter_value_spec())

    # Assert
    members = _alias_union_members((client_dir / "models" / "open_value.py").read_text(), "OpenValue")
    assert members == ["str", "float", "bool", "List[Any]"]


def test_client_generation__list_members_in_a_union__structure_objects_and_open_arrays(tmp_path: Path) -> None:
    """A list of objects reaches the model-list member; an open array keeps its items as they are."""
    # Arrange
    _generate(tmp_path, _filter_value_spec())
    script = (
        "import json\n"
        "from probe_client.core.cattrs_converter import structure_from_dict\n"
        "from probe_client.models import Request\n"
        "first = structure_from_dict({'filter': [{'kind': 'user', 'userId': 'u'}], 'open': 'x'}, Request)\n"
        "second = structure_from_dict({'filter': 'x', 'open': [1, 2, [3]]}, Request)\n"
        "print(json.dumps({'filter_types': [type(v).__name__ for v in first.filter_],"
        " 'user_id': first.filter_[0].user_id, 'open': second.open_}))\n"
    )

    # Act
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        cwd=tmp_path,
    )

    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"filter_types": ["Principal"], "user_id": "u", "open": [1, 2, [3]]}
