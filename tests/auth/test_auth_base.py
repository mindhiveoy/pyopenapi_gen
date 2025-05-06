import inspect
from typing import Any, Dict

import pytest

from pyopenapi_gen.core.auth.base import BaseAuth


def test_base_auth_method_signature() -> None:
    """BaseAuth should define authenticate_request(request_args: Dict[str, Any]) -> Dict[str, Any]"""
    sig = inspect.signature(BaseAuth.authenticate_request)
    params = sig.parameters
    assert list(params.keys()) == ["self", "request_args"]
    assert params["request_args"].annotation == dict[str, Any]
    assert sig.return_annotation == dict[str, Any]
