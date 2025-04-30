from pyopenapi_gen.helpers.url_utils import extract_url_variables


def test_extract_url_variables__typical_url__returns_all_vars() -> None:
    """
    Scenario:
        A URL template contains several variables in curly braces.
        We want to extract all variable names.

    Expected Outcome:
        The function returns a set of all variable names found in the template.
    """
    # Arrange
    url = "/foo/{bar}/baz/{qux}/static/{id}"
    # Act
    result = extract_url_variables(url)
    # Assert
    assert result == {"bar", "qux", "id"}


def test_extract_url_variables__no_vars__returns_empty_set() -> None:
    """
    Scenario:
        A URL template contains no variables.
        We want to ensure the function returns an empty set.

    Expected Outcome:
        The function returns an empty set.
    """
    # Arrange
    url = "/foo/bar/baz"
    # Act
    result = extract_url_variables(url)
    # Assert
    assert result == set()


def test_extract_url_variables__adjacent_vars_and_duplicates__returns_unique_names() -> None:
    """
    Scenario:
        A URL template contains adjacent and duplicate variable names.
        We want to ensure the function returns unique variable names only.

    Expected Outcome:
        The function returns a set of unique variable names.
    """
    # Arrange
    url = "/{foo}/{foo}/{bar}{baz}/{foo}"
    # Act
    result = extract_url_variables(url)
    # Assert
    assert result == {"foo", "bar", "baz"}


def test_extract_url_variables__empty_string__returns_empty_set() -> None:
    """
    Scenario:
        The URL template is an empty string.
        We want to ensure the function returns an empty set.

    Expected Outcome:
        The function returns an empty set.
    """
    # Arrange
    url = ""
    # Act
    result = extract_url_variables(url)
    # Assert
    assert result == set()
