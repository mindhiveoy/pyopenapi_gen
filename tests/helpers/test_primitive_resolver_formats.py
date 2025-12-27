"""Tests for PrimitiveTypeResolver format mappings."""

from pathlib import Path

import pytest

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.type_resolution.primitive_resolver import PrimitiveTypeResolver


class TestPrimitiveResolverFormats:
    """Tests for extended format mappings in PrimitiveTypeResolver."""

    @pytest.fixture
    def render_context(self, tmp_path: Path) -> RenderContext:
        """Create a RenderContext for testing."""
        project_root = tmp_path
        gen_pkg_root = project_root / "out_pkg"
        gen_pkg_root.mkdir(parents=True, exist_ok=True)

        context = RenderContext(
            package_root_for_generated_code=str(gen_pkg_root),
            overall_project_root=str(project_root),
            core_package_name="out_pkg.core",
        )
        return context

    @pytest.fixture
    def resolver(self, render_context: RenderContext) -> PrimitiveTypeResolver:
        """Create a PrimitiveTypeResolver instance."""
        return PrimitiveTypeResolver(context=render_context)

    # --- Basic primitive types ---

    def test_resolve__null_type__returns_none_string(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="null")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "None"

    def test_resolve__integer_type__returns_int(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="integer")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "int"

    def test_resolve__number_type__returns_float(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="number")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "float"

    def test_resolve__boolean_type__returns_bool(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="boolean")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "bool"

    def test_resolve__string_type_no_format__returns_str(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="string")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "str"

    # --- Date/time formats ---

    def test_resolve__string_date_time_format__returns_datetime_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="date-time")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "datetime"
        assert "datetime" in render_context.import_collector.imports.get("datetime", set())

    def test_resolve__string_date_format__returns_date_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="date")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "date"
        assert "date" in render_context.import_collector.imports.get("datetime", set())

    def test_resolve__string_time_format__returns_time_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="time")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "time"
        assert "time" in render_context.import_collector.imports.get("datetime", set())

    def test_resolve__string_duration_format__returns_timedelta_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="duration")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "timedelta"
        assert "timedelta" in render_context.import_collector.imports.get("datetime", set())

    # --- UUID format ---

    def test_resolve__string_uuid_format__returns_uuid_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="uuid")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "UUID"
        assert "UUID" in render_context.import_collector.imports.get("uuid", set())

    # --- Binary formats ---

    def test_resolve__string_binary_format__returns_bytes(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="string", format="binary")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "bytes"

    def test_resolve__string_byte_format__returns_bytes(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="string", format="byte")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "bytes"

    # --- IP address formats ---

    def test_resolve__string_ipv4_format__returns_ipv4address_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="ipv4")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "IPv4Address"
        assert "IPv4Address" in render_context.import_collector.imports.get("ipaddress", set())

    def test_resolve__string_ipv6_format__returns_ipv6address_and_adds_import(
        self, resolver: PrimitiveTypeResolver, render_context: RenderContext
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format="ipv6")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "IPv6Address"
        assert "IPv6Address" in render_context.import_collector.imports.get("ipaddress", set())

    # --- String-based formats (no special Python type) ---

    @pytest.mark.parametrize(
        "format_value",
        ["uri", "url", "email", "hostname", "password"],
    )
    def test_resolve__string_based_formats__returns_str(
        self, resolver: PrimitiveTypeResolver, format_value: str
    ) -> None:
        # Arrange
        schema = IRSchema(type="string", format=format_value)

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "str"

    # --- Integer formats ---

    @pytest.mark.parametrize(
        "format_value",
        ["int32", "int64", None],
    )
    def test_resolve__integer_with_formats__returns_int(
        self, resolver: PrimitiveTypeResolver, format_value: str | None
    ) -> None:
        # Arrange
        schema = IRSchema(type="integer", format=format_value)

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "int"

    # --- Number formats ---

    @pytest.mark.parametrize(
        "format_value",
        ["float", "double", None],
    )
    def test_resolve__number_with_formats__returns_float(
        self, resolver: PrimitiveTypeResolver, format_value: str | None
    ) -> None:
        # Arrange
        schema = IRSchema(type="number", format=format_value)

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "float"

    # --- Unknown format ---

    def test_resolve__string_unknown_format__returns_str(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="string", format="custom-format")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result == "str"

    # --- Non-primitive types ---

    def test_resolve__object_type__returns_none(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="object")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result is None

    def test_resolve__array_type__returns_none(self, resolver: PrimitiveTypeResolver) -> None:
        # Arrange
        schema = IRSchema(type="array")

        # Act
        result = resolver.resolve(schema)

        # Assert
        assert result is None
