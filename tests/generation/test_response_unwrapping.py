# Pytest tests for response unwrapping generation

import pytest  # noqa: I001
import tempfile
import subprocess
import os
from pathlib import Path
from typing import Iterator
import logging
import re

from pyopenapi_gen.generator.client_generator import ClientGenerator


# Path to the test spec
TEST_SPEC_FILE = Path(__file__).parent.parent / "specs" / "response_unwrapping_spec.yaml"


def run_mypy_on_generated_code(generated_dir: Path, project_root: Path) -> None:
    """
    Runs mypy on the generated code.
    Assumes 'core' might be a sub-package of the generated client or a shared package.
    """
    env = os.environ.copy()
    pyopenapi_gen_src_dir = Path(__file__).parent.parent.parent / "src"

    python_path_parts = [
        str(generated_dir.parent.resolve()),
        str(project_root.resolve()),
        str(pyopenapi_gen_src_dir.resolve()),
        env.get("PYTHONPATH", ""),
    ]
    env["PYTHONPATH"] = os.pathsep.join(filter(None, python_path_parts))

    mypy_target = str(generated_dir)
    cmd = ["mypy", mypy_target, "--strict"]

    result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=project_root)
    assert result.returncode == 0, f"Mypy errors found:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


@pytest.fixture
def generate_client_from_spec() -> Iterator[Path]:
    """
    Pytest fixture to generate client code from the test spec.
    Yields the path to the generated client's root directory.
    """
    # # Setup logging for endpoint_utils
    # util_logger = logging.getLogger("pyopenapi_gen.helpers.endpoint_utils")
    # util_logger.setLevel(logging.INFO)
    # if not util_logger.handlers:
    #     util_handler = logging.StreamHandler()
    #     util_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    #     util_handler.setFormatter(util_formatter)
    #     util_logger.addHandler(util_handler)
    #
    # # Setup logging for endpoint_visitor
    # visitor_logger = logging.getLogger("pyopenapi_gen.visit.endpoint_visitor")
    # visitor_logger.setLevel(logging.INFO)
    # if not visitor_logger.handlers:
    #     visitor_handler = logging.StreamHandler()
    #     visitor_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    #     visitor_handler.setFormatter(visitor_formatter)
    #     visitor_logger.addHandler(visitor_handler)
    #
    # # Setup logging for render_context
    # context_logger = logging.getLogger("pyopenapi_gen.context.render_context")
    # context_logger.setLevel(logging.DEBUG) # Set to DEBUG
    # if not context_logger.handlers:
    #     context_handler = logging.StreamHandler()
    #     context_formatter = logging.Formatter('%(levelname)s:%(name)s:%(lineno)d:%(message)s')
    #     context_handler.setFormatter(context_formatter)
    #     context_logger.addHandler(context_handler)
    #
    # # Setup logging for import_collector
    # collector_logger = logging.getLogger("pyopenapi_gen.context.import_collector")
    # collector_logger.setLevel(logging.DEBUG) # Set to DEBUG
    # if not collector_logger.handlers:
    #     collector_handler = logging.StreamHandler()
    #     collector_formatter = logging.Formatter('%(levelname)s:%(name)s:%(lineno)d:%(message)s')
    #     collector_handler.setFormatter(collector_formatter)
    #     collector_logger.addHandler(collector_handler)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        project_root = Path(temp_dir_name)
        output_package_name = "generated_client_pkg"
        output_package_dir = project_root / output_package_name

        generator = ClientGenerator()
        try:
            generator.generate(
                spec_path=str(TEST_SPEC_FILE),
                project_root=project_root,
                output_package=output_package_name,
                force=True,
                no_postprocess=False,
            )
            yield output_package_dir
        except Exception as e:
            pytest.fail(f"Client generation failed: {e}")


# Test Case 1: Simple Object Unwrapping
def test_simple_object_unwrapping(generate_client_from_spec: Path) -> None:
    generated_client_dir = generate_client_from_spec
    endpoint_file = generated_client_dir / "endpoints" / "default.py"

    if not endpoint_file.exists():
        py_files = list((generated_client_dir / "endpoints").glob("*.py"))
        non_init_py_files = [f for f in py_files if f.name != "__init__.py"]
        if not non_init_py_files:
            pytest.fail("No endpoint files generated in endpoints directory.")
        if len(non_init_py_files) == 1:
            endpoint_file = non_init_py_files[0]
        else:
            pytest.fail(
                f"Expected a single endpoint file or default.py, found: {non_init_py_files}. Check generator's default tagging."
            )

    assert endpoint_file.exists(), f"Endpoint file {endpoint_file} not found."
    content = endpoint_file.read_text()

    # Find the method block
    method_match = re.search(r"(async def get_simple_unwrapped_data.*?)(?:\nasync def|\n\Z)", content, re.DOTALL)
    assert method_match, "Could not find get_simple_unwrapped_data method block"
    method_content = method_match.group(1)

    assert ") -> MyDataItem:" in method_content
    # Use regex to find the unwrapping pattern, ignoring whitespace/quotes
    assert re.search(
        r"response\.json\(\)\s*\.\s*get\(\s*(?:'|\")data(?:'|\")\s*\)", method_content
    ), "response.json().get('data') pattern not found in method"
    assert "cast(MyDataItem" in method_content  # Check cast is still there


# Test Case 2: List of Objects Unwrapping
def test_list_object_unwrapping(generate_client_from_spec: Path) -> None:
    generated_client_dir = generate_client_from_spec
    endpoint_file = generated_client_dir / "endpoints" / "default.py"
    assert endpoint_file.exists(), "Endpoint file default.py not found."
    content = endpoint_file.read_text()

    # Find the method block
    method_match = re.search(r"(async def get_list_unwrapped_data.*?)(?:\nasync def|\n\Z)", content, re.DOTALL)
    assert method_match, "Could not find get_list_unwrapped_data method block"
    method_content = method_match.group(1)

    assert ") -> List[MyDataItem]:" in method_content
    assert re.search(
        r"from\s+typing\s+import\s+([^\n,]*?,\s*)*?List", content
    ), "'from typing import ..., List, ...' not found"

    # Use regex to find the unwrapping pattern
    assert re.search(
        r"response\.json\(\)\s*\.\s*get\(\s*(?:'|\")data(?:'|\")\s*\)", method_content
    ), "response.json().get('data') pattern not found in method"
    assert "cast(List[MyDataItem]" in method_content  # Check cast is still there


# Test Case 3: No Unwrapping (Direct Object)
def test_no_unwrapping_direct_object(generate_client_from_spec: Path) -> None:
    generated_client_dir = generate_client_from_spec
    endpoint_file = generated_client_dir / "endpoints" / "default.py"
    assert endpoint_file.exists(), "Endpoint file default.py not found."
    content = endpoint_file.read_text()

    assert "async def get_direct_data(" in content
    assert ") -> MyDataItem:" in content
    assert "cast(MyDataItem, response.json())" in content
    assert "response.json().get('data')" not in content


# Test Case 4: No Unwrapping (Data With Meta) - Current strict logic
def test_no_unwrapping_data_with_meta(generate_client_from_spec: Path) -> None:
    generated_client_dir = generate_client_from_spec
    endpoint_file = generated_client_dir / "endpoints" / "default.py"
    assert endpoint_file.exists(), "Endpoint file default.py not found."
    content = endpoint_file.read_text()

    assert "async def get_data_with_meta(" in content
    assert ") -> DataWithMetaWrapper:" in content
    assert "cast(DataWithMetaWrapper, response.json())" in content
    assert "response.json().get('data')" not in content
