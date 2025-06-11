"""Unit tests for EnumGenerator class."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.import_collector import ImportCollector
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.visit.model.enum_generator import EnumGenerator


class TestEnumGeneratorInit:
    def test_init__valid_renderer__stores_renderer(self) -> None:
        """
        Scenario:
            EnumGenerator is initialized with a valid PythonConstructRenderer.

        Expected Outcome:
            The renderer should be stored as an instance attribute.
        """
        # Arrange
        mock_renderer = Mock(spec=PythonConstructRenderer)

        # Act
        generator = EnumGenerator(mock_renderer)

        # Assert
        assert generator.renderer is mock_renderer

    def test_init__none_renderer__raises_assertion_error(self) -> None:
        """
        Scenario:
            EnumGenerator is initialized with None as the renderer.

        Expected Outcome:
            An AssertionError should be raised with an appropriate message.
        """
        # Arrange & Act & Assert
        with pytest.raises(AssertionError, match="PythonConstructRenderer cannot be None"):
            EnumGenerator(None)  # type: ignore


class TestGenerateMemberNameForStringEnum:
    @pytest.fixture
    def generator(self) -> EnumGenerator:
        """Provides an EnumGenerator instance for testing."""
        mock_renderer = Mock(spec=PythonConstructRenderer)
        return EnumGenerator(mock_renderer)

    def test_generate_member_name_for_string_enum__simple_string__returns_uppercase(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A simple string value like "active" is passed to generate a member name.

        Expected Outcome:
            The method should return "ACTIVE" as a valid Python identifier.
        """
        # Arrange
        value = "active"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "ACTIVE"

    def test_generate_member_name_for_string_enum__string_with_hyphens__replaces_with_underscores(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string value with hyphens like "active-user" is passed.

        Expected Outcome:
            Hyphens should be replaced with underscores, returning "ACTIVE_USER".
        """
        # Arrange
        value = "active-user"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "ACTIVE_USER"

    def test_generate_member_name_for_string_enum__string_with_spaces__replaces_with_underscores(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string value with spaces like "inactive user" is passed.

        Expected Outcome:
            Spaces should be replaced with underscores, returning "INACTIVE_USER".
        """
        # Arrange
        value = "inactive user"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "INACTIVE_USER"

    def test_generate_member_name_for_string_enum__string_starting_with_digit__prefixed_with_member(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string value starting with a digit like "123test" is passed.

        Expected Outcome:
            The result should be prefixed with "MEMBER_" to make it a valid Python identifier.
        """
        # Arrange
        value = "123test"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "MEMBER_123TEST"

    def test_generate_member_name_for_string_enum__python_keyword__appends_underscore(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string value that is a Python keyword like "class" is passed.

        Expected Outcome:
            An underscore should be appended to avoid keyword conflicts.
        """
        # Arrange
        value = "class"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "CLASS_"

    def test_generate_member_name_for_string_enum__empty_string__returns_member_empty_string(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            An empty string is passed as the value.

        Expected Outcome:
            The method should return "MEMBER_EMPTY_STRING" as a fallback.
        """
        # Arrange
        value = ""

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "MEMBER_EMPTY_STRING"

    def test_generate_member_name_for_string_enum__special_characters__removes_invalid_chars(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string with special characters like "value!@#$" is passed.

        Expected Outcome:
            Special characters should be removed, returning "VALUE".
        """
        # Arrange
        value = "value!@#$"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "VALUE"

    def test_generate_member_name_for_string_enum__unicode_characters__generates_fallback(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string with unicode characters like "你好世界" is passed.

        Expected Outcome:
            Unicode characters should be handled and a fallback name generated.
        """
        # Arrange
        value = "你好世界"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "MEMBER_EMPTY_STRING"  # No alphanumeric chars remain after sanitization

    def test_generate_member_name_for_string_enum__non_string_input__raises_assertion_error(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A non-string value like an integer is passed.

        Expected Outcome:
            An AssertionError should be raised stating input must be a string.
        """
        # Arrange
        value = 123

        # Act & Assert
        with pytest.raises(AssertionError, match="Input value must be a string"):
            generator._generate_member_name_for_string_enum(value)  # type: ignore

    def test_generate_member_name_for_string_enum__mixed_case_alphanumeric__preserves_alphanumeric(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string with mixed case and numbers like "Value123Test" is passed.

        Expected Outcome:
            The string should be converted to uppercase, returning "VALUE123TEST".
        """
        # Arrange
        value = "Value123Test"

        # Act
        result = generator._generate_member_name_for_string_enum(value)

        # Assert
        assert result == "VALUE123TEST"


class TestGenerateMemberNameForIntegerEnum:
    @pytest.fixture
    def generator(self) -> EnumGenerator:
        """Provides an EnumGenerator instance for testing."""
        mock_renderer = Mock(spec=PythonConstructRenderer)
        return EnumGenerator(mock_renderer)

    def test_generate_member_name_for_integer_enum__positive_integer__returns_value_prefixed(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A positive integer value and fallback are passed.

        Expected Outcome:
            The method should return "VALUE_" prefixed name based on the integer.
        """
        # Arrange
        value = 42
        fallback = 42

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "VALUE_42"

    def test_generate_member_name_for_integer_enum__negative_integer__returns_value_neg_prefixed(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A negative integer value and fallback are passed.

        Expected Outcome:
            The method should sanitize the negative sign, resulting in a name starting with underscore.
        """
        # Arrange
        value = -5
        fallback = -5

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "_5"

    def test_generate_member_name_for_integer_enum__string_convertible_to_int__uses_string_for_naming(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string that represents an integer like "100" is passed.

        Expected Outcome:
            The string representation should be used for naming, returning "VALUE_100".
        """
        # Arrange
        value = "100"
        fallback = 100

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "VALUE_100"

    def test_generate_member_name_for_integer_enum__string_with_special_chars__sanitizes_and_prefixes(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string with special characters like "2-value" is passed.

        Expected Outcome:
            Special characters should be handled and result prefixed appropriately.
        """
        # Arrange
        value = "2-value"
        fallback = 2

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "VALUE_2_VALUE"

    def test_generate_member_name_for_integer_enum__string_becomes_empty_after_sanitization__uses_fallback(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string that becomes empty after sanitization like "!@#" is passed.

        Expected Outcome:
            The fallback integer value should be used for naming.
        """
        # Arrange
        value = "!@#"
        fallback = 5

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "VALUE_5"

    def test_generate_member_name_for_integer_enum__non_string_non_int_value__raises_assertion_error(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A value that is neither string nor int (like a list) is passed.

        Expected Outcome:
            An AssertionError should be raised stating the input type requirement.
        """
        # Arrange
        value: list[str] = []
        fallback = 0

        # Act & Assert
        with pytest.raises(AssertionError, match="Input value for integer enum naming must be str or int"):
            generator._generate_member_name_for_integer_enum(value, fallback)  # type: ignore

    def test_generate_member_name_for_integer_enum__non_int_fallback__raises_assertion_error(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A valid value but non-integer fallback is passed.

        Expected Outcome:
            An AssertionError should be raised stating fallback must be int.
        """
        # Arrange
        value = 5
        fallback = "not_int"

        # Act & Assert
        with pytest.raises(AssertionError, match="Fallback integer value must be an int"):
            generator._generate_member_name_for_integer_enum(value, fallback)  # type: ignore

    def test_generate_member_name_for_integer_enum__keyword_string__appends_underscore(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string that becomes a Python keyword after processing is passed.

        Expected Outcome:
            An underscore should be appended to avoid keyword conflicts.
        """
        # Arrange
        value = "class"
        fallback = 1

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "CLASS_"

    def test_generate_member_name_for_integer_enum__negative_fallback_when_empty_sanitized__uses_value_neg_prefix(
        self, generator: EnumGenerator
    ) -> None:
        """
        Scenario:
            A string that becomes empty after sanitization is passed with a negative fallback.

        Expected Outcome:
            The fallback logic should use "VALUE_NEG_" prefix for negative values.
        """
        # Arrange
        value = "!@#$"  # This becomes empty after sanitization (no letters, digits, or underscores)
        fallback = -7

        # Act
        result = generator._generate_member_name_for_integer_enum(value, fallback)

        # Assert
        assert result == "VALUE_NEG_7"


class TestGenerate:
    @pytest.fixture
    def mock_context(self) -> Mock:
        """Provides a mock RenderContext for testing."""
        context = Mock(spec=RenderContext)
        context.import_collector = Mock(spec=ImportCollector)
        context.import_collector.imports = {}
        return context

    @pytest.fixture
    def mock_renderer(self) -> Mock:
        """Provides a mock PythonConstructRenderer for testing."""
        renderer = Mock(spec=PythonConstructRenderer)
        renderer.render_enum.return_value = "mocked_enum_code"
        return renderer

    @pytest.fixture
    def generator(self, mock_renderer: Mock) -> EnumGenerator:
        """Provides an EnumGenerator instance with mocked renderer."""
        return EnumGenerator(mock_renderer)

    def test_generate__string_enum_schema__generates_string_enum_code(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            A valid string enum schema with enum values is passed to generate.

        Expected Outcome:
            The method should generate Python enum code and register imports properly.
        """
        # Arrange
        schema = IRSchema(
            name="StatusEnum", type="string", enum=["pending", "approved", "rejected"], description="Status enumeration"
        )
        base_name = "Status"

        # Mock the import collector to simulate successful import registration
        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act
        result = generator.generate(schema, base_name, mock_context)

        # Assert
        assert result == "mocked_enum_code"
        mock_renderer.render_enum.assert_called_once_with(
            enum_name="Status",
            base_type="str",
            values=[("PENDING", "pending"), ("APPROVED", "approved"), ("REJECTED", "rejected")],
            description="Status enumeration",
            context=mock_context,
        )

    def test_generate__integer_enum_schema__generates_integer_enum_code(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            A valid integer enum schema with numeric enum values is passed.

        Expected Outcome:
            The method should generate Python enum code with integer values.
        """
        # Arrange
        schema = IRSchema(name="ErrorCode", type="integer", enum=[10, 20, 30], description="Error code enumeration")
        base_name = "ErrorCode"

        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act
        result = generator.generate(schema, base_name, mock_context)

        # Assert
        assert result == "mocked_enum_code"
        mock_renderer.render_enum.assert_called_once_with(
            enum_name="ErrorCode",
            base_type="int",
            values=[("VALUE_10", 10), ("VALUE_20", 20), ("VALUE_30", 30)],
            description="Error code enumeration",
            context=mock_context,
        )

    def test_generate__enum_with_duplicate_member_names__handles_duplicates_with_counter(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            An enum schema with values that would generate duplicate member names is passed.

        Expected Outcome:
            Duplicate names should be resolved by appending a counter suffix.
        """
        # Arrange
        schema = IRSchema(
            name="DuplicateEnum",
            type="string",
            enum=["test", "test", "Test"],  # These would all become "TEST"
        )
        base_name = "DuplicateEnum"

        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act
        result = generator.generate(schema, base_name, mock_context)

        # Assert
        mock_renderer.render_enum.assert_called_once_with(
            enum_name="DuplicateEnum",
            base_type="str",
            values=[("TEST", "test"), ("TEST_1", "test"), ("TEST_2", "Test")],
            description=None,
            context=mock_context,
        )

    def test_generate__integer_enum_with_unconvertible_values__uses_fallback_and_logs_warning(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Scenario:
            An integer enum schema contains values that cannot be converted to integers.

        Expected Outcome:
            Unconvertible values should fallback to 0 and a warning should be logged.
        """
        # Arrange
        schema = IRSchema(
            name="MixedEnum",
            type="integer",
            enum=[1, "not_a_number", 3],
        )
        base_name = "MixedEnum"

        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act
        with caplog.at_level("WARNING"):
            result = generator.generate(schema, base_name, mock_context)

        # Assert
        assert "Could not convert enum value 'not_a_number' to int" in caplog.text
        mock_renderer.render_enum.assert_called_once_with(
            enum_name="MixedEnum",
            base_type="int",
            values=[("VALUE_1", 1), ("NOT_A_NUMBER", 0), ("VALUE_3", 3)],  # not_a_number becomes 0 with sanitized name
            description=None,
            context=mock_context,
        )

    def test_generate__none_schema__raises_assertion_error(self, generator: EnumGenerator, mock_context: Mock) -> None:
        """
        Scenario:
            None is passed as the schema parameter.

        Expected Outcome:
            An AssertionError should be raised with appropriate message.
        """
        # Arrange & Act & Assert
        with pytest.raises(AssertionError, match="Schema cannot be None for enum generation"):
            generator.generate(None, "TestEnum", mock_context)  # type: ignore

    def test_generate__schema_with_none_name__raises_assertion_error(
        self, generator: EnumGenerator, mock_context: Mock
    ) -> None:
        """
        Scenario:
            A schema with None name is passed.

        Expected Outcome:
            An AssertionError should be raised about schema name requirement.
        """
        # Arrange
        schema = IRSchema(name=None, type="string", enum=["a", "b"])

        # Act & Assert
        with pytest.raises(AssertionError, match="Schema name must be present for enum generation"):
            generator.generate(schema, "TestEnum", mock_context)

    def test_generate__empty_base_name__raises_assertion_error(
        self, generator: EnumGenerator, mock_context: Mock
    ) -> None:
        """
        Scenario:
            An empty string is passed as the base_name parameter.

        Expected Outcome:
            An AssertionError should be raised about base name requirement.
        """
        # Arrange
        schema = IRSchema(name="TestEnum", type="string", enum=["a", "b"])

        # Act & Assert
        with pytest.raises(AssertionError, match="Base name cannot be empty for enum generation"):
            generator.generate(schema, "", mock_context)

    def test_generate__none_context__raises_assertion_error(self, generator: EnumGenerator) -> None:
        """
        Scenario:
            None is passed as the context parameter.

        Expected Outcome:
            An AssertionError should be raised about RenderContext requirement.
        """
        # Arrange
        schema = IRSchema(name="TestEnum", type="string", enum=["a", "b"])

        # Act & Assert
        with pytest.raises(AssertionError, match="RenderContext cannot be None"):
            generator.generate(schema, "TestEnum", None)  # type: ignore

    def test_generate__schema_without_enum_values__raises_assertion_error(
        self, generator: EnumGenerator, mock_context: Mock
    ) -> None:
        """
        Scenario:
            A schema without enum values (empty or None) is passed.

        Expected Outcome:
            An AssertionError should be raised about enum values requirement.
        """
        # Arrange
        schema = IRSchema(name="TestEnum", type="string", enum=None)

        # Act & Assert
        with pytest.raises(AssertionError, match="Schema must have enum values for enum generation"):
            generator.generate(schema, "TestEnum", mock_context)

    def test_generate__schema_with_invalid_type__raises_assertion_error(
        self, generator: EnumGenerator, mock_context: Mock
    ) -> None:
        """
        Scenario:
            A schema with a type other than "string" or "integer" is passed.

        Expected Outcome:
            An AssertionError should be raised about valid enum types.
        """
        # Arrange
        schema = IRSchema(name="TestEnum", type="object", enum=["a", "b"])

        # Act & Assert
        with pytest.raises(AssertionError, match="Enum schema type must be 'string' or 'integer'"):
            generator.generate(schema, "TestEnum", mock_context)

    def test_generate__renderer_returns_empty_code__raises_assertion_error(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            The PythonConstructRenderer returns empty or whitespace-only code.

        Expected Outcome:
            An AssertionError should be raised about non-empty generated code.
        """
        # Arrange
        schema = IRSchema(name="TestEnum", type="string", enum=["a", "b"])
        mock_renderer.render_enum.return_value = "   "  # Whitespace only
        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act & Assert
        with pytest.raises(AssertionError, match="Generated enum code cannot be empty"):
            generator.generate(schema, "TestEnum", mock_context)

    def test_generate__imports_not_registered__raises_assertion_error(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            The PythonConstructRenderer fails to register required imports.

        Expected Outcome:
            An AssertionError should be raised about missing enum imports.
        """
        # Arrange
        schema = IRSchema(name="TestEnum", type="string", enum=["a", "b"])
        mock_renderer.render_enum.return_value = "valid_code"
        mock_context.import_collector.imports = {}  # No imports registered

        # Act & Assert
        with pytest.raises(AssertionError, match="Enum import was not added to context by renderer"):
            generator.generate(schema, "TestEnum", mock_context)

    def test_generate__complex_string_enum_values__sanitizes_all_member_names(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            A string enum with complex values requiring various sanitization rules is passed.

        Expected Outcome:
            All member names should be properly sanitized and unique.
        """
        # Arrange
        schema = IRSchema(
            name="ComplexEnum",
            type="string",
            enum=["active-user", "inactive user", "123invalid", "class", "", "special!@#"],
        )
        base_name = "ComplexEnum"

        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act
        result = generator.generate(schema, base_name, mock_context)

        # Assert
        expected_values = [
            ("ACTIVE_USER", "active-user"),
            ("INACTIVE_USER", "inactive user"),
            ("MEMBER_123INVALID", "123invalid"),
            ("CLASS_", "class"),
            ("MEMBER_EMPTY_STRING", ""),
            ("SPECIAL", "special!@#"),
        ]
        mock_renderer.render_enum.assert_called_once_with(
            enum_name="ComplexEnum", base_type="str", values=expected_values, description=None, context=mock_context
        )

    def test_generate__zero_and_negative_integer_values__handles_correctly(
        self, generator: EnumGenerator, mock_context: Mock, mock_renderer: Mock
    ) -> None:
        """
        Scenario:
            An integer enum with zero and negative values is passed.

        Expected Outcome:
            Zero and negative values should be handled with appropriate naming.
        """
        # Arrange
        schema = IRSchema(
            name="NumberEnum",
            type="integer",
            enum=[0, -1, -10, 5],
        )
        base_name = "NumberEnum"

        mock_context.import_collector.imports = {"enum": {"Enum"}}

        # Act
        result = generator.generate(schema, base_name, mock_context)

        # Assert
        expected_values = [
            ("VALUE_0", 0),
            ("_1", -1),
            ("_10", -10),
            ("VALUE_5", 5),
        ]
        mock_renderer.render_enum.assert_called_once_with(
            enum_name="NumberEnum", base_type="int", values=expected_values, description=None, context=mock_context
        )
