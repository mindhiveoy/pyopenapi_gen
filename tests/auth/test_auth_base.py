import inspect
from typing import Any, Dict

from pyopenapi_gen.auth.base import BaseAuth


def test_base_auth_method_signature() -> None:
    """BaseAuth should define authenticate_request(request_args: Dict[str, Any]) -> Dict[str, Any]"""
    sig = inspect.signature(BaseAuth.authenticate_request)
    # The method should accept two parameters: self and request_args
    params = list(sig.parameters.values())
    assert len(params) == 2
    assert params[1].name == "request_args"
    # Return annotation should be Dict[str, Any]
    assert sig.return_annotation == Dict[str, Any]
