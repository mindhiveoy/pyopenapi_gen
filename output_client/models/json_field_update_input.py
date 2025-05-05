from dataclasses import dataclass


@dataclass
class JsonFieldUpdateInput:
    """
    Input for partially updating a JSON field. Can be either: - An array of operations conforming to JSON Patch (RFC 6902) for `application/json-patch+json`. - A partial JSON object conforming to JSON Merge Patch (RFC 7386) for `application/merge-patch+json`.


    """

    # No properties defined in schema
    pass
