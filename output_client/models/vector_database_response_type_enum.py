import json
from enum import Enum, unique

__all__ = ["VectorDatabaseResponseTypeEnum"]


@unique
class VectorDatabaseResponseTypeEnum(str, Enum):
    """Type of the vector database"""

    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    QDRANT = "qdrant"

    @classmethod
    def from_json(cls, json_str: str) -> "VectorDatabaseResponseTypeEnum":
        """Create an instance from a JSON string"""
        return VectorDatabaseResponseTypeEnum(json.loads(json_str))
