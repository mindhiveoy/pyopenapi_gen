"""
Regression tests for schema edge cases.

These tests ensure that problematic OpenAPI schema patterns are handled correctly
and do not regress in future versions.

Issues covered:
- Bug #1: Property named 'additionalProperties' with boolean enum {type: boolean, enum: [false]}
- Bug #2: Array items with only nullable: true and no type
"""

import ast
import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.emitters.core_emitter import CoreEmitter
from pyopenapi_gen.emitters.exceptions_emitter import ExceptionsEmitter
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


class TestPropertyNamedAdditionalProperties:
    """
    Regression tests for Bug #1: Property named 'additionalProperties'.

    When an object has a property literally named 'additionalProperties' (not the
    OpenAPI keyword, but an actual property name), pyopenapi-gen must:
    1. Parse it as a regular property, not confuse it with the keyword
    2. Generate proper type for the property based on its schema
    3. For {type: boolean, enum: [false]}, generate Literal[False] inline
    """

    @pytest.fixture
    def spec_with_additional_properties_property(self) -> dict:
        """Create a minimal OpenAPI spec with a property named 'additionalProperties'."""
        return {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ToolParametersTypeEnum": {
                        "type": "string",
                        "enum": ["object"],
                        "description": "Must be 'object' for function parameters",
                    },
                    "ToolParameters": {
                        "type": "object",
                        "properties": {
                            "type": {"$ref": "#/components/schemas/ToolParametersTypeEnum"},
                            "required": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of required parameter names",
                            },
                            # This is the critical property - literally named 'additionalProperties'
                            "additionalProperties": {"type": "boolean", "enum": [False]},
                        },
                        "required": ["type"],
                        "description": "JSON Schema for tool parameters",
                    },
                }
            },
        }

    def test_property_named_additional_properties__generates_valid_python(
        self, tmp_path: Path, spec_with_additional_properties_property: dict
    ) -> None:
        """
        Scenario:
            - An OpenAPI schema has a property literally named 'additionalProperties'
            - This property has schema {type: boolean, enum: [false]}
        Expected Outcome:
            - Generated Python code is syntactically valid
            - The ToolParameters dataclass has an additional_properties field
            - The field type is Literal[False] or bool (not a broken import)
        """
        # Arrange
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.safe_dump(spec_with_additional_properties_property))

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        core_dir = out_dir / "core"
        core_dir.mkdir()

        spec_dict = yaml.safe_load(spec_file.read_text())
        ir = load_ir_from_spec(spec_dict)

        # Create RenderContext
        render_context = RenderContext(
            core_package_name="out.core",
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(tmp_path),
            parsed_schemas=ir.schemas,
        )

        # Run emitters
        exceptions_emitter = ExceptionsEmitter(core_package_name="out.core", overall_project_root=str(tmp_path))
        _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

        core_emitter = CoreEmitter(core_package="out.core", exception_alias_names=exception_alias_names)
        core_emitter.emit(str(out_dir))

        models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
        models_emitter.emit(ir, str(out_dir))

        # Assert - Check that tool_parameters.py was generated
        models_dir = out_dir / "models"
        assert models_dir.exists(), "models directory not generated"

        tool_params_file = models_dir / "tool_parameters.py"
        assert tool_params_file.exists(), "tool_parameters.py not generated"

        # Read the generated file
        content = tool_params_file.read_text()

        # Assert - Should NOT have a broken import to a non-existent module
        assert (
            "from .additional_properties import" not in content
        ), "Generated code has broken import to non-existent additional_properties module"

        # Assert - Should have the field with a valid type
        assert "additional_properties" in content, "Field additional_properties not found in generated code"

        # The type should be either Literal[False], bool, or similar - NOT a broken class reference
        # We check that it doesn't reference a non-existent 'AdditionalProperties' class
        lines = content.split("\n")
        for line in lines:
            if "additional_properties:" in line and "AdditionalProperties" in line:
                # This is the bug - it's referencing a class that doesn't exist
                pytest.fail(f"Generated code references non-existent AdditionalProperties class: {line}")

    def test_property_named_additional_properties__passes_mypy(
        self, tmp_path: Path, spec_with_additional_properties_property: dict
    ) -> None:
        """
        Scenario:
            - Generate code from spec with 'additionalProperties' as a property name
        Expected Outcome:
            - Generated code passes mypy strict type checking
        """
        # Arrange
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.safe_dump(spec_with_additional_properties_property))

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        core_dir = out_dir / "core"
        core_dir.mkdir()

        spec_dict = yaml.safe_load(spec_file.read_text())
        ir = load_ir_from_spec(spec_dict)

        # Create RenderContext
        render_context = RenderContext(
            core_package_name="out.core",
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(tmp_path),
            parsed_schemas=ir.schemas,
        )

        # Run emitters
        exceptions_emitter = ExceptionsEmitter(core_package_name="out.core", overall_project_root=str(tmp_path))
        _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

        core_emitter = CoreEmitter(core_package="out.core", exception_alias_names=exception_alias_names)
        core_emitter.emit(str(out_dir))

        models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
        models_emitter.emit(ir, str(out_dir))

        # Run mypy only on the models directory to avoid module name conflicts with core
        # Use isolated environment to prevent conflict with any installed packages
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path)

        mypy_result = subprocess.run(
            ["mypy", "--strict", "--ignore-missing-imports", str(out_dir / "models")],
            capture_output=True,
            text=True,
            env=env,
            cwd=tmp_path,
        )

        # Assert
        assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"


class TestArrayItemsWithOnlyNullable:
    """
    Regression tests for Bug #2: Array items with only nullable: true.

    When an array's items schema has only 'nullable: true' without a 'type',
    pyopenapi-gen should handle this gracefully rather than generating
    empty dataclasses.
    """

    @pytest.fixture
    def spec_with_nullable_only_items(self) -> dict:
        """Create a minimal OpenAPI spec with array items that only have nullable: true."""
        return {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "CleaningFilters": {
                        "type": "object",
                        "properties": {
                            "ids": {
                                "type": "array",
                                # This is the problematic pattern - items with only nullable, no type
                                "items": {"nullable": True},
                            },
                            "classes": {
                                "type": "array",
                                "items": {"nullable": True},
                            },
                        },
                    },
                }
            },
        }

    def test_array_items_with_only_nullable__generates_any_type(
        self, tmp_path: Path, spec_with_nullable_only_items: dict
    ) -> None:
        """
        Scenario:
            - An array's items schema has only 'nullable: true' without a 'type'
        Expected Outcome:
            - Generated code uses List[Any] or similar for the array type
            - Does NOT generate empty *Item dataclasses
        """
        # Arrange
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.safe_dump(spec_with_nullable_only_items))

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        core_dir = out_dir / "core"
        core_dir.mkdir()

        spec_dict = yaml.safe_load(spec_file.read_text())
        ir = load_ir_from_spec(spec_dict)

        # Create RenderContext
        render_context = RenderContext(
            core_package_name="out.core",
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(tmp_path),
            parsed_schemas=ir.schemas,
        )

        # Run emitters
        exceptions_emitter = ExceptionsEmitter(core_package_name="out.core", overall_project_root=str(tmp_path))
        _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

        core_emitter = CoreEmitter(core_package="out.core", exception_alias_names=exception_alias_names)
        core_emitter.emit(str(out_dir))

        models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
        models_emitter.emit(ir, str(out_dir))

        # Assert - Check models directory
        models_dir = out_dir / "models"
        assert models_dir.exists(), "models directory not generated"

        # Check for empty *Item dataclasses (the bug)
        for model_file in models_dir.glob("*.py"):
            content = model_file.read_text()
            # Check for empty dataclass pattern (the bug symptom)
            if "@dataclass" in content and "pass" in content:
                # Count fields in the dataclass
                lines = content.split("\n")
                in_dataclass = False
                field_count = 0
                for line in lines:
                    if "@dataclass" in line:
                        in_dataclass = True
                        continue
                    if in_dataclass and line.strip().startswith("class "):
                        continue
                    if in_dataclass and line.strip() == "pass":
                        # This might be an empty dataclass - check if it's for item types
                        if "Item" in model_file.stem or "_item" in model_file.stem:
                            pytest.fail(
                                f"Empty *Item dataclass generated in {model_file.name}: "
                                "This indicates array items with only nullable:true are not handled correctly"
                            )
                    if in_dataclass and ":" in line and not line.strip().startswith("#"):
                        field_count += 1
                    if in_dataclass and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                        if not line.strip().startswith("class ") and not line.strip().startswith("@"):
                            in_dataclass = False

    def test_array_items_with_only_nullable__passes_mypy(
        self, tmp_path: Path, spec_with_nullable_only_items: dict
    ) -> None:
        """
        Scenario:
            - Generate code from spec with nullable-only array items
        Expected Outcome:
            - Generated code passes mypy strict type checking
        """
        # Arrange
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.safe_dump(spec_with_nullable_only_items))

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        core_dir = out_dir / "core"
        core_dir.mkdir()

        spec_dict = yaml.safe_load(spec_file.read_text())
        ir = load_ir_from_spec(spec_dict)

        # Create RenderContext
        render_context = RenderContext(
            core_package_name="out.core",
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(tmp_path),
            parsed_schemas=ir.schemas,
        )

        # Run emitters
        exceptions_emitter = ExceptionsEmitter(core_package_name="out.core", overall_project_root=str(tmp_path))
        _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

        core_emitter = CoreEmitter(core_package="out.core", exception_alias_names=exception_alias_names)
        core_emitter.emit(str(out_dir))

        models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
        models_emitter.emit(ir, str(out_dir))

        # Run mypy only on the models directory to avoid module name conflicts with core
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path)

        mypy_result = subprocess.run(
            ["mypy", "--strict", "--ignore-missing-imports", str(out_dir / "models")],
            capture_output=True,
            text=True,
            env=env,
            cwd=tmp_path,
        )

        # Assert
        assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"


class TestBooleanEnumHandling:
    """
    Tests for proper handling of boolean enums.

    Boolean enums like {type: boolean, enum: [false]} should be resolved
    to Literal[False] rather than creating separate enum classes.
    """

    @pytest.fixture
    def spec_with_boolean_enum(self) -> dict:
        """Create a minimal OpenAPI spec with a boolean enum property."""
        return {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ConfigSchema": {
                        "type": "object",
                        "properties": {
                            "allowExtensions": {"type": "boolean", "enum": [False]},
                            "strictMode": {"type": "boolean", "enum": [True]},
                            "mixedFlag": {"type": "boolean", "enum": [True, False]},
                        },
                    },
                }
            },
        }

    def test_boolean_enum__generates_literal_type(self, tmp_path: Path, spec_with_boolean_enum: dict) -> None:
        """
        Scenario:
            - A property has {type: boolean, enum: [false]}
        Expected Outcome:
            - Generated type is Literal[False] not a separate enum class
        """
        # Arrange
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.safe_dump(spec_with_boolean_enum))

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        core_dir = out_dir / "core"
        core_dir.mkdir()

        spec_dict = yaml.safe_load(spec_file.read_text())
        ir = load_ir_from_spec(spec_dict)

        # Create RenderContext
        render_context = RenderContext(
            core_package_name="out.core",
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(tmp_path),
            parsed_schemas=ir.schemas,
        )

        # Run emitters
        exceptions_emitter = ExceptionsEmitter(core_package_name="out.core", overall_project_root=str(tmp_path))
        _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

        core_emitter = CoreEmitter(core_package="out.core", exception_alias_names=exception_alias_names)
        core_emitter.emit(str(out_dir))

        models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
        models_emitter.emit(ir, str(out_dir))

        # Assert - Check that config_schema.py was generated
        models_dir = out_dir / "models"
        config_file = models_dir / "config_schema.py"
        assert config_file.exists(), "config_schema.py not generated"

        content = config_file.read_text()

        # Check that we don't have broken enum imports
        assert "from .allow_extensions import" not in content, "Broken enum import for allow_extensions"
        assert "from .strict_mode import" not in content, "Broken enum import for strict_mode"

        # The fields should be present
        assert "allow_extensions" in content, "allow_extensions field not found"
        assert "strict_mode" in content, "strict_mode field not found"

        # Run mypy only on the models directory to avoid module name conflicts with core
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path)

        mypy_result = subprocess.run(
            ["mypy", "--strict", "--ignore-missing-imports", str(out_dir / "models")],
            capture_output=True,
            text=True,
            env=env,
            cwd=tmp_path,
        )

        assert mypy_result.returncode == 0, f"mypy errors:\n{mypy_result.stdout}\n{mypy_result.stderr}"


class TestInlineSingleValueStringEnum:
    """
    Regression tests for inline single-value string enums.

    When an OpenAPI schema has an inline property with { type: "string", enum: ["object"] },
    pyopenapi-gen must either:
    A) Treat it as plain `str` and NOT create a separate file, or
    B) Create a proper enum/TypeAlias file with valid content.

    The bug: empty model files are generated (only whitespace) and consuming models
    import from these empty files, causing ImportError at runtime.
    """

    @pytest.fixture
    def spec_with_inline_single_value_enums(self) -> dict:
        """Create a spec with inline single-value string enums in multiple schemas."""
        return {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ToolParameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["object"],
                                "description": 'Must be "object" for function parameters',
                            },
                            "properties": {"type": "object"},
                        },
                        "required": ["type", "properties"],
                    },
                    "FunctionDefinition": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["function"],
                                "description": 'Must be "function"',
                            },
                            "name": {"type": "string"},
                        },
                        "required": ["type", "name"],
                    },
                    "GoogleCredential": {
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "enum": ["google"],
                                "description": "Discriminator literal",
                            },
                            "token": {"type": "string"},
                        },
                        "required": ["provider", "token"],
                    },
                }
            },
        }

    @pytest.fixture
    def generated_models_dir(self, tmp_path: Path, spec_with_inline_single_value_enums: dict) -> Path:
        """Run the full generation pipeline and return the models directory."""
        spec_file = tmp_path / "spec.yaml"
        spec_file.write_text(yaml.safe_dump(spec_with_inline_single_value_enums))

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        core_dir = out_dir / "core"
        core_dir.mkdir()

        spec_dict = yaml.safe_load(spec_file.read_text())
        ir = load_ir_from_spec(spec_dict)

        render_context = RenderContext(
            core_package_name="out.core",
            package_root_for_generated_code=str(out_dir),
            overall_project_root=str(tmp_path),
            parsed_schemas=ir.schemas,
        )

        exceptions_emitter = ExceptionsEmitter(core_package_name="out.core", overall_project_root=str(tmp_path))
        _, exception_alias_names = exceptions_emitter.emit(ir, str(core_dir))

        core_emitter = CoreEmitter(core_package="out.core", exception_alias_names=exception_alias_names)
        core_emitter.emit(str(out_dir))

        models_emitter = ModelsEmitter(context=render_context, parsed_schemas=ir.schemas)
        models_emitter.emit(ir, str(out_dir))

        models_dir = out_dir / "models"
        assert models_dir.exists(), "models directory not generated"
        return models_dir

    def test_inline_single_value_enum__no_empty_model_files(self, generated_models_dir: Path) -> None:
        """
        Scenario:
            - Multiple schemas have inline single-value string enums
        Expected Outcome:
            - No generated model file is empty (< 3 bytes)
            - Every generated .py file in models/ contains valid Python with at least
              one class, TypeAlias, or import statement
        """
        empty_files = []
        for py_file in generated_models_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text().strip()
            if len(content) < 3:
                empty_files.append(py_file.name)

        assert not empty_files, f"Empty model files generated (the inline single-value enum bug): {empty_files}"

    def test_inline_single_value_enum__all_imports_resolve(self, generated_models_dir: Path) -> None:
        """
        Scenario:
            - Multiple schemas have inline single-value string enums
        Expected Outcome:
            - Every `from .module import ClassName` in any model file references
              a module that actually defines that ClassName
        """
        # Collect all defined names per module
        defined_names: dict[str, set[str]] = {}
        for py_file in generated_models_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            module_stem = py_file.stem
            names: set[str] = set()

            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        names.add(node.name)
                    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                        names.add(node.target.id)
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                names.add(target.id)
            except SyntaxError:
                pass

            defined_names[module_stem] = names

        # Check all relative imports resolve
        broken_imports = []
        for py_file in generated_models_dir.glob("*.py"):
            content = py_file.read_text()
            for match in re.finditer(r"from \.(\w+) import (\w+)", content):
                module_name, class_name = match.groups()
                if module_name not in defined_names:
                    broken_imports.append(
                        f"{py_file.name}: imports '{class_name}' from '.{module_name}' "
                        f"but module '{module_name}.py' does not exist or is empty"
                    )
                elif class_name not in defined_names[module_name]:
                    broken_imports.append(
                        f"{py_file.name}: imports '{class_name}' from '.{module_name}' "
                        f"but '{class_name}' is not defined in '{module_name}.py'"
                    )

        assert not broken_imports, f"Broken imports found (the inline single-value enum bug):\n" + "\n".join(
            f"  - {b}" for b in broken_imports
        )
