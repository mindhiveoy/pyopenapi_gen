from enum import Enum


class VectorDatabaseResponseTypeEnum(Enum):
    """Type of the vector database"""

    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    QDRANT = "qdrant"
