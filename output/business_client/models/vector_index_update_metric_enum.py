from enum import Enum


class VectorIndexUpdateMetricEnum(Enum):
    """Distance metric used for similarity search"""

    COSINE = "cosine"
    DOT = "dot"
    L2 = "l2"
    L1 = "l1"
