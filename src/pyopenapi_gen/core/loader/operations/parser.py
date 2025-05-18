"""Operation parsers for OpenAPI IR transformation.

Provides the main parse_operations function to transform OpenAPI paths into IR operations.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any, List, Mapping, Optional, cast

from pyopenapi_gen import HTTPMethod, IROperation, IRParameter, IRRequestBody, IRResponse
from pyopenapi_gen.core.loader.operations.post_processor import post_process_operation
from pyopenapi_gen.core.loader.operations.request_body import parse_request_body
from pyopenapi_gen.core.loader.parameters import parse_parameter, resolve_parameter_node_if_ref
from pyopenapi_gen.core.loader.responses import parse_response
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


def parse_operations(
    paths: Mapping[str, Any],
    raw_parameters: Mapping[str, Any],
    raw_responses: Mapping[str, Any],
    raw_request_bodies: Mapping[str, Any],
    context: ParsingContext,
) -> List[IROperation]:
    """Iterate paths to build IROperation list.

    Contracts:
        Preconditions:
            - paths is a valid paths object from OpenAPI spec
            - raw_parameters, raw_responses, raw_request_bodies are component mappings
            - context is properly initialized with schemas
        Postconditions:
            - Returns a list of IROperation objects
            - All operations have correct path, method, parameters, responses, etc.
            - All referenced schemas are properly stored in context
    """
    assert isinstance(paths, Mapping), "paths must be a Mapping"
    assert isinstance(raw_parameters, Mapping), "raw_parameters must be a Mapping"
    assert isinstance(raw_responses, Mapping), "raw_responses must be a Mapping"
    assert isinstance(raw_request_bodies, Mapping), "raw_request_bodies must be a Mapping"
    assert isinstance(context, ParsingContext), "context must be a ParsingContext"

    ops: List[IROperation] = []

    for path, item in paths.items():
        if not isinstance(item, Mapping):
            continue
        entry = cast(Mapping[str, Any], item)

        base_params_nodes = cast(List[Mapping[str, Any]], entry.get("parameters", []))

        for method, on in entry.items():
            try:
                if method in {
                    "parameters",
                    "summary",
                    "description",
                    "servers",
                    "$ref",
                }:
                    continue
                mu = method.upper()
                if mu not in HTTPMethod.__members__:
                    continue

                node_op = cast(Mapping[str, Any], on)

                # Get operation_id for this specific operation
                if "operationId" in node_op:
                    operation_id = node_op["operationId"]
                else:
                    operation_id = NameSanitizer.sanitize_method_name(f"{mu}_{path}".strip("/"))

                # Parse base parameters (path-level) with operation_id context
                base_params: List[IRParameter] = []
                for p_node_data_raw in base_params_nodes:
                    resolved_p_node_data = resolve_parameter_node_if_ref(p_node_data_raw, context)
                    base_params.append(
                        parse_parameter(resolved_p_node_data, context, operation_id_for_promo=operation_id)
                    )

                # Parse operation-specific parameters
                params: List[IRParameter] = list(base_params)  # Start with copies of path-level params
                for p_param_node_raw in cast(List[Mapping[str, Any]], node_op.get("parameters", [])):
                    resolved_p_param_node = resolve_parameter_node_if_ref(p_param_node_raw, context)
                    params.append(parse_parameter(resolved_p_param_node, context, operation_id_for_promo=operation_id))

                # Parse request body
                rb: Optional[IRRequestBody] = None
                if "requestBody" in node_op:
                    rb = parse_request_body(
                        cast(Mapping[str, Any], node_op["requestBody"]),
                        raw_request_bodies,
                        context,
                        operation_id,
                    )

                # Parse responses
                resps: List[IRResponse] = []
                for sc, rn_node in cast(Mapping[str, Any], node_op.get("responses", {})).items():
                    if (
                        isinstance(rn_node, Mapping)
                        and "$ref" in rn_node
                        and isinstance(rn_node.get("$ref"), str)
                        and rn_node["$ref"].startswith("#/components/responses/")
                    ):
                        ref_name = rn_node["$ref"].split("/")[-1]
                        resp_node_resolved = raw_responses.get(ref_name, {}) or rn_node
                    else:
                        resp_node_resolved = rn_node
                    resps.append(parse_response(sc, resp_node_resolved, context, operation_id_for_promo=operation_id))

                op = IROperation(
                    operation_id=operation_id,
                    method=HTTPMethod[mu],
                    path=path,
                    summary=node_op.get("summary"),
                    description=node_op.get("description"),
                    parameters=params,
                    request_body=rb,
                    responses=resps,
                    tags=list(node_op.get("tags", [])),
                )
            except Exception as e:
                warnings.warn(
                    f"Skipping operation parsing for {method.upper()} {path}: {e}",
                    UserWarning,
                )
                continue
            else:
                # Post-process the parsed operation to fill in schema names
                post_process_operation(op, context)
                ops.append(op)

    # Post-condition check
    assert all(isinstance(op, IROperation) for op in ops), "All items must be IROperation objects"

    return ops
