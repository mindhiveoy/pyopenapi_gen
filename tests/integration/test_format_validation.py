"""
Runtime tests for format validation.

Tests that generated format validation actually works by:
1. Generating dataclass code with format constraints
2. Dynamically importing the generated code
3. Verifying validation accepts/rejects values correctly
"""

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.dataclass_generator import DataclassGenerator


def _create_module_from_code(code: str, module_name: str = "test_module"):
    """Create a Python module from generated code and import it."""
    # Write code to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        temp_path = Path(f.name)
        f.write(code)

    try:
        # Import the module
        spec = importlib.util.spec_from_file_location(module_name, temp_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create spec for {module_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        # Clean up temp file
        temp_path.unlink()


def test_email_format__rejects_invalid_email():
    """Test email format validation rejects invalid emails.

    Scenario:
        Field with format: email and invalid email value

    Expected Outcome:
        ValueError raised mentioning email validation
    """
    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "email": IRSchema(name="email", type="string", format="email"),
        },
        required=["email"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})
    generated_code = generator.generate(schema, "User", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import re

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_email_invalid")

    # Invalid emails should be rejected
    # Note: 'email' is a Python keyword, so it gets sanitized to 'email_'
    with pytest.raises(ValueError) as exc_info:
        module.User(email_="not-an-email")
    assert "email" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        module.User(email_="missing@domain")
    assert "email" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        module.User(email_="@nodomain.com")
    assert "email" in str(exc_info.value).lower()


def test_email_format__accepts_valid_email():
    """Test email format validation accepts valid emails.

    Scenario:
        Field with format: email and valid email values

    Expected Outcome:
        Objects created successfully
    """
    schema = IRSchema(
        name="User",
        type="object",
        properties={
            "email": IRSchema(name="email", type="string", format="email"),
        },
        required=["email"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"User": schema})
    generated_code = generator.generate(schema, "User", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import re

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_email_valid")

    # Valid emails should be accepted
    user1 = module.User(email_="test@example.com")
    assert user1.email_ == "test@example.com"

    user2 = module.User(email_="user.name+tag@example.co.uk")
    assert user2.email_ == "user.name+tag@example.co.uk"


def test_uuid_format__rejects_invalid_uuid():
    """Test UUID format validation rejects invalid UUIDs.

    Scenario:
        Field with format: uuid and invalid UUID value

    Expected Outcome:
        ValueError raised mentioning UUID validation
    """
    schema = IRSchema(
        name="Resource",
        type="object",
        properties={
            "id": IRSchema(name="id", type="string", format="uuid"),
        },
        required=["id"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Resource": schema})
    generated_code = generator.generate(schema, "Resource", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import uuid
from uuid import UUID

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_uuid_invalid")

    # Invalid UUIDs should be rejected
    # Note: 'id' is a Python builtin, so it gets sanitized to 'id_'
    with pytest.raises(ValueError) as exc_info:
        module.Resource(id_="not-a-uuid")
    assert "uuid" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        module.Resource(id_="12345")
    assert "uuid" in str(exc_info.value).lower()


def test_uuid_format__accepts_valid_uuid():
    """Test UUID format validation accepts valid UUIDs.

    Scenario:
        Field with format: uuid and valid UUID values

    Expected Outcome:
        Objects created successfully
    """
    schema = IRSchema(
        name="Resource",
        type="object",
        properties={
            "id": IRSchema(name="id", type="string", format="uuid"),
        },
        required=["id"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Resource": schema})
    generated_code = generator.generate(schema, "Resource", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import uuid
from uuid import UUID

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_uuid_valid")

    # Valid UUIDs should be accepted
    resource = module.Resource(id_="550e8400-e29b-41d4-a716-446655440000")
    assert resource.id_ == "550e8400-e29b-41d4-a716-446655440000"


def test_date_format__rejects_invalid_date():
    """Test date format validation rejects invalid dates.

    Scenario:
        Field with format: date and invalid date value

    Expected Outcome:
        ValueError raised mentioning date validation
    """
    schema = IRSchema(
        name="Event",
        type="object",
        properties={
            "date": IRSchema(name="date", type="string", format="date"),
        },
        required=["date"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Event": schema})
    generated_code = generator.generate(schema, "Event", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import datetime
from datetime import date

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_date_invalid")

    # Invalid dates should be rejected
    with pytest.raises(ValueError) as exc_info:
        module.Event(date="not-a-date")
    assert "date" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        module.Event(date="2023-13-01")  # Invalid month
    assert "date" in str(exc_info.value).lower()


def test_date_format__accepts_valid_date():
    """Test date format validation accepts valid dates.

    Scenario:
        Field with format: date and valid ISO 8601 date

    Expected Outcome:
        Object created successfully
    """
    schema = IRSchema(
        name="Event",
        type="object",
        properties={
            "date": IRSchema(name="date", type="string", format="date"),
        },
        required=["date"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Event": schema})
    generated_code = generator.generate(schema, "Event", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import datetime
from datetime import date

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_date_valid")

    # Valid dates should be accepted
    event = module.Event(date="2023-12-25")
    assert event.date == "2023-12-25"


def test_datetime_format__rejects_invalid_datetime():
    """Test date-time format validation rejects invalid datetimes.

    Scenario:
        Field with format: date-time and invalid datetime value

    Expected Outcome:
        ValueError raised mentioning date-time validation
    """
    schema = IRSchema(
        name="Timestamp",
        type="object",
        properties={
            "created_at": IRSchema(name="created_at", type="string", format="date-time"),
        },
        required=["created_at"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Timestamp": schema})
    generated_code = generator.generate(schema, "Timestamp", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
from datetime import datetime

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_datetime_invalid")

    # Invalid datetimes should be rejected
    with pytest.raises(ValueError) as exc_info:
        module.Timestamp(created_at="not-a-datetime")
    assert "date-time" in str(exc_info.value).lower() or "datetime" in str(exc_info.value).lower()


def test_datetime_format__accepts_valid_datetime():
    """Test date-time format validation accepts valid datetimes.

    Scenario:
        Field with format: date-time and valid ISO 8601 datetime

    Expected Outcome:
        Object created successfully
    """
    schema = IRSchema(
        name="Timestamp",
        type="object",
        properties={
            "created_at": IRSchema(name="created_at", type="string", format="date-time"),
        },
        required=["created_at"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Timestamp": schema})
    generated_code = generator.generate(schema, "Timestamp", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
from datetime import datetime

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_datetime_valid")

    # Valid datetimes should be accepted
    ts1 = module.Timestamp(created_at="2023-12-25T10:30:00")
    assert ts1.created_at == "2023-12-25T10:30:00"

    ts2 = module.Timestamp(created_at="2023-12-25T10:30:00Z")
    assert ts2.created_at == "2023-12-25T10:30:00Z"

    ts3 = module.Timestamp(created_at="2023-12-25T10:30:00+01:00")
    assert ts3.created_at == "2023-12-25T10:30:00+01:00"


def test_uri_format__rejects_invalid_uri():
    """Test URI format validation rejects invalid URIs.

    Scenario:
        Field with format: uri and invalid URI value

    Expected Outcome:
        ValueError raised mentioning URI validation
    """
    schema = IRSchema(
        name="Link",
        type="object",
        properties={
            "url": IRSchema(name="url", type="string", format="uri"),
        },
        required=["url"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Link": schema})
    generated_code = generator.generate(schema, "Link", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import urllib.parse

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_uri_invalid")

    # Invalid URIs should be rejected
    with pytest.raises(ValueError) as exc_info:
        module.Link(url="not-a-uri")
    assert "uri" in str(exc_info.value).lower()

    with pytest.raises(ValueError) as exc_info:
        module.Link(url="example.com")  # Missing scheme
    assert "uri" in str(exc_info.value).lower()


def test_uri_format__accepts_valid_uri():
    """Test URI format validation accepts valid URIs.

    Scenario:
        Field with format: uri and valid URI values

    Expected Outcome:
        Objects created successfully
    """
    schema = IRSchema(
        name="Link",
        type="object",
        properties={
            "url": IRSchema(name="url", type="string", format="uri"),
        },
        required=["url"],
    )

    context = RenderContext()
    renderer = PythonConstructRenderer()
    generator = DataclassGenerator(renderer, {"Link": schema})
    generated_code = generator.generate(schema, "Link", context)

    full_code = """
from dataclasses import dataclass
from typing import Any
import urllib.parse

class BaseSchema:
    pass

""" + generated_code

    module = _create_module_from_code(full_code, "test_uri_valid")

    # Valid URIs should be accepted
    link1 = module.Link(url="https://example.com")
    assert link1.url == "https://example.com"

    link2 = module.Link(url="https://example.com/path?query=value")
    assert link2.url == "https://example.com/path?query=value"
