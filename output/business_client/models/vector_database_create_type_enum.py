from enum import Enum


class VectorDatabaseCreateTypeEnum(Enum):
    """Type of vector database"""

    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    QDRANT = "qdrant"
