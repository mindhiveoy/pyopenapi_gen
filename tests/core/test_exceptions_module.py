from pytest import raises

from pyopenapi_gen.core.exceptions import ClientError, HTTPError, ServerError


def test_http_error_attributes_and_str() -> None:
    error = HTTPError(404, "Not found")
    # Attributes are set correctly
    assert error.status_code == 404
    assert error.message == "Not found"
    # __str__ (via Exception) includes status code and message
    assert str(error) == "404: Not found"


def test_client_error_inherits_http_error() -> None:
    err = ClientError(400, "Bad request")
    # Inheritance
    assert isinstance(err, HTTPError)
    # Type is ClientError
    assert type(err) is ClientError
    # Attributes
    assert err.status_code == 400
    assert err.message == "Bad request"
    assert str(err) == "400: Bad request"


def test_server_error_inherits_http_error() -> None:
    err = ServerError(500, "Server error")
    # Inheritance
    assert isinstance(err, HTTPError)
    # Type is ServerError
    assert type(err) is ServerError
    # Attributes
    assert err.status_code == 500
    assert err.message == "Server error"
    assert str(err) == "500: Server error"


def test_http_error_raise_and_catch() -> None:
    with raises(HTTPError) as excinfo:
        raise HTTPError(403, "Forbidden")
    caught = excinfo.value
    assert caught.status_code == 403
    assert caught.message == "Forbidden"
    assert str(caught) == "403: Forbidden"
