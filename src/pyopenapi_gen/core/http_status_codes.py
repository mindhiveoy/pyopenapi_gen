"""HTTP status code definitions and human-readable names.

This module provides a registry of standard HTTP status codes with their
canonical names according to RFC specifications.

References:
    - RFC 9110 (HTTP Semantics): https://www.rfc-editor.org/rfc/rfc9110.html
    - IANA HTTP Status Code Registry: https://www.iana.org/assignments/http-status-codes/
"""

# Standard HTTP status codes with human-readable names
HTTP_STATUS_CODES: dict[int, str] = {
    # 1xx Informational
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing",
    103: "Early Hints",
    # 2xx Success
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status",
    208: "Already Reported",
    226: "IM Used",
    # 3xx Redirection
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    # 4xx Client Error
    400: "Bad Request",
    401: "Unauthorised",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity",
    423: "Locked",
    424: "Failed Dependency",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    # 5xx Server Error
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage",
    508: "Loop Detected",
    510: "Not Extended",
    511: "Network Authentication Required",
}


def get_status_name(code: int) -> str:
    """Get the human-readable name for an HTTP status code.

    Args:
        code: HTTP status code (e.g., 404)

    Returns:
        Human-readable status name (e.g., "Not Found"), or "Unknown" if not found
    """
    return HTTP_STATUS_CODES.get(code, "Unknown")


def is_error_code(code: int) -> bool:
    """Check if a status code represents an error (4xx or 5xx).

    Args:
        code: HTTP status code

    Returns:
        True if the code is a client or server error, False otherwise
    """
    return 400 <= code < 600


def is_client_error(code: int) -> bool:
    """Check if a status code represents a client error (4xx).

    Args:
        code: HTTP status code

    Returns:
        True if the code is a client error, False otherwise
    """
    return 400 <= code < 500


def is_server_error(code: int) -> bool:
    """Check if a status code represents a server error (5xx).

    Args:
        code: HTTP status code

    Returns:
        True if the code is a server error, False otherwise
    """
    return 500 <= code < 600


def is_success_code(code: int) -> bool:
    """Check if a status code represents success (2xx).

    Args:
        code: HTTP status code

    Returns:
        True if the code is a success code, False otherwise
    """
    return 200 <= code < 300


# Mapping of HTTP status codes to Python exception class names
# These are semantically meaningful names that Python developers expect
HTTP_EXCEPTION_NAMES: dict[int, str] = {
    # 4xx Client Errors
    400: "BadRequestError",
    401: "UnauthorisedError",
    402: "PaymentRequiredError",
    403: "ForbiddenError",
    404: "NotFoundError",
    405: "MethodNotAllowedError",
    406: "NotAcceptableError",
    407: "ProxyAuthenticationRequiredError",
    408: "RequestTimeoutError",
    409: "ConflictError",
    410: "GoneError",
    411: "LengthRequiredError",
    412: "PreconditionFailedError",
    413: "PayloadTooLargeError",
    414: "UriTooLongError",
    415: "UnsupportedMediaTypeError",
    416: "RangeNotSatisfiableError",
    417: "ExpectationFailedError",
    418: "ImATeapotError",
    421: "MisdirectedRequestError",
    422: "UnprocessableEntityError",
    423: "LockedError",
    424: "FailedDependencyError",
    425: "TooEarlyError",
    426: "UpgradeRequiredError",
    428: "PreconditionRequiredError",
    429: "TooManyRequestsError",
    431: "RequestHeaderFieldsTooLargeError",
    451: "UnavailableForLegalReasonsError",
    # 5xx Server Errors
    500: "InternalServerError",
    501: "NotImplementedError",  # Note: Conflicts with Python built-in, will be handled
    502: "BadGatewayError",
    503: "ServiceUnavailableError",
    504: "GatewayTimeoutError",
    505: "HttpVersionNotSupportedError",
    506: "VariantAlsoNegotiatesError",
    507: "InsufficientStorageError",
    508: "LoopDetectedError",
    510: "NotExtendedError",
    511: "NetworkAuthenticationRequiredError",
}


def get_exception_class_name(code: int) -> str:
    """Get the Python exception class name for an HTTP status code.

    Args:
        code: HTTP status code (e.g., 404)

    Returns:
        Python exception class name (e.g., "NotFoundError"), or "Error{code}" as fallback

    Examples:
        >>> get_exception_class_name(404)
        'NotFoundError'
        >>> get_exception_class_name(429)
        'TooManyRequestsError'
        >>> get_exception_class_name(999)  # Unknown code
        'Error999'
    """
    # Check if we have a semantic name for this code
    if code in HTTP_EXCEPTION_NAMES:
        name = HTTP_EXCEPTION_NAMES[code]
        # Handle Python keyword conflicts
        if name == "NotImplementedError":
            # Avoid conflict with Python's built-in NotImplementedError
            return "HttpNotImplementedError"
        return name

    # Fallback to Error{code} for codes we don't have semantic names for
    return f"Error{code}"
