import pytest
from pyopenapi_gen.core.loader import load_ir_from_spec


def test_loader_raises_on_missing_paths() -> None:
    # 'paths' key is required by OpenAPI
    bad_spec = {
        "openapi": "3.1.0",
        "info": {"title": "X API", "version": "0.1.0"},
        # missing 'paths'
    }
    with pytest.raises(Exception):
        load_ir_from_spec(bad_spec)


def test_loader_raises_on_missing_openapi_field() -> None:
    # 'openapi' field is required by spec validator
    bad_spec = {
        "info": {"title": "X API", "version": "0.1.0"},
        "paths": {},
    }
    with pytest.raises(Exception):
        load_ir_from_spec(bad_spec)
