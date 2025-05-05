import json
from enum import Enum, unique

__all__ = ["VectorDatabaseCreateTypeEnum"]


@unique
class VectorDatabaseCreateTypeEnum(str, Enum):
    """Type of vector database"""

    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    QDRANT = "qdrant"

    @classmethod
    def from_json(cls, json_str: str) -> "VectorDatabaseCreateTypeEnum":
        """Create an instance from a JSON string"""
        return VectorDatabaseCreateTypeEnum(json.loads(json_str))
