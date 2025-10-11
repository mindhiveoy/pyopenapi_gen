"""Reference resolver implementation."""

import logging
from typing import Dict

from pyopenapi_gen import IRResponse, IRSchema

from ..contracts.protocols import ReferenceResolver

logger = logging.getLogger(__name__)


class OpenAPIReferenceResolver(ReferenceResolver):
    """Resolves OpenAPI $ref references."""

    def __init__(self, schemas: Dict[str, IRSchema], responses: Dict[str, IRResponse] | None = None):
        """
        Initialize reference resolver.

        Args:
            schemas: Dictionary of schemas by name
            responses: Dictionary of responses by name (optional)
        """
        self.schemas = schemas
        self.responses = responses or {}

    def resolve_ref(self, ref: str) -> IRSchema | None:
        """
        Resolve a schema $ref to the target schema.

        Args:
            ref: Reference string like "#/components/schemas/User"

        Returns:
            Target schema or None if not found
        """
        if not ref.startswith("#/components/schemas/"):
            logger.warning(f"Unsupported schema ref format: {ref}")
            return None

        schema_name = ref.split("/")[-1]
        schema = self.schemas.get(schema_name)

        if not schema:
            logger.warning(f"Schema not found for ref: {ref}")
            return None

        return schema

    def resolve_response_ref(self, ref: str) -> IRResponse | None:
        """
        Resolve a response $ref to the target response.

        Args:
            ref: Reference string like "#/components/responses/UserResponse"

        Returns:
            Target response or None if not found
        """
        if not ref.startswith("#/components/responses/"):
            logger.warning(f"Unsupported response ref format: {ref}")
            return None

        response_name = ref.split("/")[-1]
        response = self.responses.get(response_name)

        if not response:
            logger.warning(f"Response not found for ref: {ref}")
            return None

        return response
