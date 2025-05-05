from dataclasses import dataclass


@dataclass
class EmbeddingResponse:
    """
    Data model for EmbeddingResponse

    Attributes:
        data (Dict[str, Any]): Embedding model for vector representations of text used in semantic search and retrieval.
    """
