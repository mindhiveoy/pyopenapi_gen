"""Operation post-processing utilities.

Provides functions to finalize and enhance parsed operations.
"""

from __future__ import annotations

import logging

from pyopenapi_gen import IROperation
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


def post_process_operation(op: IROperation, context: ParsingContext) -> None:
    """Post-process an operation to finalize schema names and register them.

    Contracts:
        Preconditions:
            - op is a valid IROperation
            - context is properly initialized
        Postconditions:
            - All request body and response schemas are properly named and registered
    """
    if not isinstance(op, IROperation):
        raise TypeError("op must be an IROperation")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext")

    # Handle request body schemas
    if op.request_body:
        for _, sch_val in op.request_body.content.items():
            if not sch_val.name:
                generated_rb_name = NameSanitizer.sanitize_class_name(op.operation_id + "Request")
                sch_val.name = generated_rb_name
                context.parsed_schemas[generated_rb_name] = sch_val
            elif sch_val.name not in context.parsed_schemas:
                context.parsed_schemas[sch_val.name] = sch_val

    # Handle response schemas
    for resp_val in op.responses:
        for _, sch_resp_val in resp_val.content.items():
            if sch_resp_val.name is None:
                if getattr(sch_resp_val, "_from_unresolved_ref", False):
                    continue
                is_streaming = getattr(resp_val, "stream", False)
                if is_streaming:
                    continue

                should_synthesize_name = False
                if sch_resp_val.type == "object" and (sch_resp_val.properties or sch_resp_val.additional_properties):
                    should_synthesize_name = True

                if should_synthesize_name:
                    generated_name = NameSanitizer.sanitize_class_name(op.operation_id + "Response")
                    sch_resp_val.name = generated_name
                    context.parsed_schemas[generated_name] = sch_resp_val

            elif sch_resp_val.name and sch_resp_val.name not in context.parsed_schemas:
                context.parsed_schemas[sch_resp_val.name] = sch_resp_val
