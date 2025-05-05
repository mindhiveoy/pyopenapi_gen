from enum import Enum


class VectorIndexCreateMetricEnum(Enum):
    """Distance metric used for similarity search"""

    COSINE = "cosine"
    DOT = "dot"
    L2 = "l2"
    L1 = "l1"
