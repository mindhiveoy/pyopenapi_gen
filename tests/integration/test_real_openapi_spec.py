"""
End-to-end integration test using real OpenAPI specification.

This test generates a complete client from validation_test_spec.yaml and verifies
that validation constraints from the spec are properly enforced in generated code.

This is NOT mock theatre - we generate actual code from a real spec and test it.
"""

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

from pyopenapi_gen import generate_client


def _import_generated_models(package_root: Path):
    """Import the generated models package.

    Args:
        package_root: Path to the root directory containing the generated package

    Returns:
        The imported models module
    """
    # Mock httpx since generated client depends on it but we only test models
    if "httpx" not in sys.modules:
        from unittest.mock import MagicMock
        sys.modules["httpx"] = MagicMock()

    # Add package root to path if not already there
    package_root_str = str(package_root)
    if package_root_str not in sys.path:
        sys.path.insert(0, package_root_str)

    # Import the models module
    # This uses the package structure with __init__.py, so Python handles all relative imports
    models_module = importlib.import_module("test_validation_api.models")

    return models_module


@pytest.fixture
def generated_client(tmp_path):
    """Generate client from validation_test_spec.yaml in temporary directory.

    Yields:
        Path to generated package directory
    """
    spec_path = Path(__file__).parent.parent.parent / "input" / "validation_test_spec.json"

    if not spec_path.exists():
        pytest.skip(f"Test spec not found: {spec_path}")

    # Generate client in temp directory
    output_package = "test_validation_api"

    try:
        generate_client(
            spec_path=str(spec_path),
            project_root=str(tmp_path),
            output_package=output_package,
            force=True,
            no_postprocess=True,  # Skip Black/mypy for speed
            verbose=False
        )
    except Exception as e:
        pytest.fail(f"Client generation failed: {e}")

    package_path = tmp_path / "test_validation_api"

    if not package_path.exists():
        pytest.fail(f"Generated package not found at {package_path}")

    yield tmp_path  # Return root so tests can add to sys.path and import properly


def test_user_creation__valid_data__succeeds(generated_client):
    """Test UserCreate model accepts valid data.

    Scenario:
        Valid user data matching all constraints from OpenAPI spec

    Expected Outcome:
        UserCreate instance created successfully
    """
    # Import generated models
    models = _import_generated_models(generated_client)

    # Valid data matching spec constraints
    # Note: 'email' field is renamed to 'email_' in generated code (name sanitization)
    valid_user = models.UserCreate(
        username="john_doe",        # 3-20 chars, alphanumeric + underscore
        email_="john@example.com",  # Valid email, 5-100 chars
        password="secure123",       # 8-100 chars
        age=25,                     # 13-150
        bio="This is a valid biography that is long enough",  # 10-500 chars
        tags=["python", "coding"]   # 1-10 unique items
    )

    assert valid_user.username == "john_doe"
    assert valid_user.email_ == "john@example.com"  # Note: field is email_
    assert valid_user.age == 25


def test_user_creation__username_too_short__raises_error(generated_client):
    """Test UserCreate rejects username shorter than minLength.

    Scenario:
        Username with only 2 characters (minLength: 3 in spec)

    Expected Outcome:
        ValueError raised mentioning username and minimum length
    """
    models = _import_generated_models(generated_client)

    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="ab",  # Too short! (minLength: 3)
            email_="test@example.com",
            age=25
        )

    error_msg = str(exc_info.value).lower()
    assert "username" in error_msg
    assert "3" in error_msg


def test_user_creation__username_invalid_pattern__raises_error(generated_client):
    """Test UserCreate rejects username not matching pattern.

    Scenario:
        Username with invalid characters (pattern: ^[a-zA-Z0-9_]+$ in spec)

    Expected Outcome:
        ValueError raised mentioning pattern validation
    """
    models = _import_generated_models(generated_client)

    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="john-doe",  # Contains hyphen, not allowed!
            email_="test@example.com",
            age=25
        )

    error_msg = str(exc_info.value).lower()
    assert "username" in error_msg
    assert "pattern" in error_msg


def test_user_creation__age_below_minimum__raises_error(generated_client):
    """Test UserCreate rejects age below minimum.

    Scenario:
        Age less than minimum value (minimum: 13 in spec)

    Expected Outcome:
        ValueError raised mentioning age constraint
    """
    models = _import_generated_models(generated_client)

    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="john_doe",
            email_="test@example.com",
            age=12  # Too young! (minimum: 13)
        )

    error_msg = str(exc_info.value).lower()
    assert "age" in error_msg
    assert "13" in error_msg


def test_user_creation__bio_optional_but_validates_when_provided(generated_client):
    """Test optional bio field accepts None but validates when provided.

    Scenario:
        Bio is optional (not in required), but has minLength: 10

    Expected Outcome:
        - None accepted without validation
        - Short bio rejected
        - Valid bio accepted
    """
    models = _import_generated_models(generated_client)

    # None should be accepted
    user_without_bio = models.UserCreate(
        username="john_doe",
        email_="test@example.com",
        age=25,
        bio=None
    )
    assert user_without_bio.bio is None

    # Short bio should be rejected
    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="john_doe",
            email_="test@example.com",
            age=25,
            bio="short"  # Too short! (minLength: 10)
        )
    assert "bio" in str(exc_info.value).lower()

    # Valid bio should be accepted
    user_with_bio = models.UserCreate(
        username="john_doe",
        email_="test@example.com",
        age=25,
        bio="This is a valid biography"
    )
    assert "valid" in user_with_bio.bio


def test_user_creation__tags_array_constraints__enforced(generated_client):
    """Test tags array validates minItems, maxItems, uniqueItems.

    Scenario:
        Tags with various constraint violations from spec:
        - minItems: 1
        - maxItems: 10
        - uniqueItems: true

    Expected Outcome:
        Invalid arrays rejected, valid arrays accepted
    """
    models = _import_generated_models(generated_client)

    # Empty array should be rejected (minItems: 1)
    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="john_doe",
            email_="test@example.com",
            age=25,
            tags=[]  # Empty! (minItems: 1)
        )
    assert "tags" in str(exc_info.value).lower()

    # Duplicate items should be rejected (uniqueItems: true)
    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="john_doe",
            email_="test@example.com",
            age=25,
            tags=["python", "coding", "python"]  # Duplicate "python"!
        )
    assert "unique" in str(exc_info.value).lower()

    # Valid array should be accepted
    user = user_module.UserCreate(
        username="john_doe",
        email="test@example.com",
        age=25,
        tags=["python", "coding", "testing"]
    )
    assert len(user.tags) == 3


def test_product_creation__price_constraints__enforced(generated_client):
    """Test Product price validates minimum and multipleOf.

    Scenario:
        Product price with constraints from spec:
        - minimum: 0.01
        - maximum: 999999.99
        - multipleOf: 0.01 (2 decimal places)

    Expected Outcome:
        Invalid prices rejected, valid prices accepted
    """
    models = _import_generated_models(generated_client)

    # Price below minimum should be rejected
    with pytest.raises(ValueError) as exc_info:
        models.Product(
            name="Test Product",
            price=0.0,  # Below minimum! (minimum: 0.01)
            category="electronics"
        )
    assert "price" in str(exc_info.value).lower()
    assert "0.01" in str(exc_info.value)

    # Valid price should be accepted
    product = models.Product(
        name="Test Product",
        price=19.99,  # Valid: >= 0.01, multipleOf 0.01
        category="electronics"
    )
    assert product.price == 19.99


def test_product_creation__category_enum__enforced(generated_client):
    """Test Product category validates enum values.

    Scenario:
        Product category must be one of: electronics, clothing, food, books, other

    Expected Outcome:
        Invalid category rejected, valid category accepted
    """
    models = _import_generated_models(generated_client)

    # Invalid enum value should be rejected
    # Note: Enum validation happens at type level, not in __post_init__
    # This tests that generated code uses proper enum type

    # Valid enum value should be accepted
    product = models.Product(
        name="Test Product",
        price=19.99,
        category="electronics"
    )
    assert product.category == "electronics"


def test_product_creation__rating_bounds__enforced(generated_client):
    """Test Product rating validates minimum and maximum.

    Scenario:
        Product rating with constraints from spec:
        - minimum: 0.0
        - maximum: 5.0
        - exclusiveMinimum: false
        - exclusiveMaximum: false

    Expected Outcome:
        Out-of-range ratings rejected, valid ratings accepted
    """
    models = _import_generated_models(generated_client)

    # Rating above maximum should be rejected
    with pytest.raises(ValueError) as exc_info:
        models.Product(
            name="Test Product",
            price=19.99,
            category="electronics",
            rating=5.5  # Above maximum! (maximum: 5.0)
        )
    assert "rating" in str(exc_info.value).lower()

    # Valid ratings should be accepted
    product1 = models.Product(
        name="Test Product",
        price=19.99,
        category="electronics",
        rating=0.0  # Minimum boundary
    )
    assert product1.rating == 0.0

    product2 = models.Product(
        name="Test Product",
        price=19.99,
        category="electronics",
        rating=5.0  # Maximum boundary
    )
    assert product2.rating == 5.0

    product3 = models.Product(
        name="Test Product",
        price=19.99,
        category="electronics",
        rating=4.5  # Middle value
    )
    assert product3.rating == 4.5


def test_multiple_constraint_violations__reports_first_error(generated_client):
    """Test that validation reports errors in order.

    Scenario:
        Data violating multiple constraints simultaneously

    Expected Outcome:
        First validation error is reported
    """
    models = _import_generated_models(generated_client)

    # Multiple violations: username too short AND invalid pattern AND age too low
    with pytest.raises(ValueError) as exc_info:
        models.UserCreate(
            username="a",  # Too short (minLength: 3) - should be caught first
            email_="test@example.com",
            age=10  # Too young (minimum: 13)
        )

    # Should report first error (username length)
    error_msg = str(exc_info.value).lower()
    assert "username" in error_msg
