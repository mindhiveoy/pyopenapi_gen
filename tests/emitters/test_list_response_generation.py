from pathlib import Path

from pyopenapi_gen import IRSchema, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer  # For consistent naming
from pyopenapi_gen.emitters.models_emitter import ModelsEmitter


def test_models_emitter__list_response_pattern__generates_proper_models_and_imports(tmp_path: Path) -> None:
    """
    Scenario:
        ModelsEmitter processes a common list response pattern with MyItem,
        PaginationMeta, and MyItemListResponse schemas where the list response
        contains an array of items and pagination metadata.

    Expected Outcome:
        The emitter should generate individual model files with proper imports,
        a correctly structured __init__.py, and no spurious files like 'data.py'.
    """
    # 1. Define IRSchema objects manually
    # Analogous to #/components/schemas/MyItem
    my_item_schema = IRSchema(
        name="MyItem",
        type="object",
        properties={
            "id": IRSchema(name=None, type="string", description="Item ID"),
            "name": IRSchema(name=None, type="string", description="Item Name"),
        },
        required=["id", "name"],
        description="A simple item.",
    )

    # Analogous to #/components/schemas/PaginationMeta
    pagination_meta_schema = IRSchema(
        name="PaginationMeta",
        type="object",
        properties={
            "totalItems": IRSchema(name=None, type="integer", description="Total items available"),
            "totalPages": IRSchema(name=None, type="integer", description="Total pages available"),
        },
        required=["totalItems", "totalPages"],
        description="Metadata for pagination.",
    )

    # Analogous to #/components/schemas/MyItemListResponse
    my_item_list_response_schema = IRSchema(
        name="MyItemListResponse",
        type="object",
        properties={
            "data": IRSchema(
                name=None,  # This field itself is unnamed in the parent, its type is important
                type="array",
                items=IRSchema(
                    name="MyItem", type="object"
                ),  # Corrected: No 'ref', type is 'object' as MyItem is an object model
                description="List of items.",
            ),
            "meta": IRSchema(
                name="PaginationMeta",
                type="object",  # Corrected: No 'ref', type is 'object'. Name matches the schema key for lookup.
            ),
        },
        required=["data", "meta"],
        description="Response wrapper for a list of MyItem.",
    )

    # 2. Create IRSpec
    schemas_dict: dict[str, IRSchema] = {
        "MyItem": my_item_schema,
        "PaginationMeta": pagination_meta_schema,
        "MyItemListResponse": my_item_list_response_schema,
    }
    spec = IRSpec(
        title="List Response Test API",
        version="v1",
        schemas=schemas_dict,
        operations=[],  # Not needed for model testing
        servers=[],  # Not needed for model testing
    )

    # 3. Set up output directory and RenderContext
    out_dir: Path = tmp_path / "out"
    render_context = RenderContext(
        overall_project_root=str(tmp_path),
        package_root_for_generated_code=str(out_dir),
        core_package_name="test_client.core",  # Example, not critical for this test
    )

    # 4. Instantiate ModelsEmitter and emit
    # Ensure that the schemas passed to ModelsEmitter are copies if modification is expected downstream,
    # or ensure ModelsEmitter handles them read-only if they are shared.
    # For this test, direct use is fine as IRSpec.schemas should provide the canonical versions.
    emitter = ModelsEmitter(context=render_context, parsed_schemas=spec.schemas)
    generated_files_map = emitter.emit(spec, str(out_dir))

    models_output_dir: Path = out_dir / "models"

    # 5. Assertions
    # Check that the correct number of model files were reported as generated
    # We expect 3 models + 1 __init__.py
    assert "models" in generated_files_map
    # The file paths in generated_files_map['models'] might be absolute.
    # We'll check specific files by constructing paths relative to models_output_dir.

    # 5.1. Check MyItem.py
    my_item_file = models_output_dir / f"{NameSanitizer.sanitize_module_name('MyItem')}.py"
    assert my_item_file.exists(), f"{my_item_file} was not generated."
    my_item_content = my_item_file.read_text()
    assert "class MyItem:" in my_item_content
    assert f"{NameSanitizer.sanitize_method_name('id')}: str" in my_item_content
    assert f"{NameSanitizer.sanitize_method_name('name')}: str" in my_item_content

    # 5.2. Check PaginationMeta.py
    pagination_meta_file = models_output_dir / f"{NameSanitizer.sanitize_module_name('PaginationMeta')}.py"
    assert pagination_meta_file.exists(), f"{pagination_meta_file} was not generated."
    pagination_meta_content = pagination_meta_file.read_text()
    assert "class PaginationMeta:" in pagination_meta_content
    assert f"{NameSanitizer.sanitize_method_name('totalItems')}: int" in pagination_meta_content
    assert f"{NameSanitizer.sanitize_method_name('totalPages')}: int" in pagination_meta_content

    # 5.3. Check MyItemListResponse.py
    my_item_list_response_file = models_output_dir / f"{NameSanitizer.sanitize_module_name('MyItemListResponse')}.py"
    assert my_item_list_response_file.exists(), f"{my_item_list_response_file} was not generated."
    my_item_list_response_content = my_item_list_response_file.read_text()
    assert "class MyItemListResponse:" in my_item_list_response_content
    assert "from typing import List" in my_item_list_response_content
    assert f"from .{NameSanitizer.sanitize_module_name('MyItem')} import MyItem" in my_item_list_response_content
    assert (
        f"from .{NameSanitizer.sanitize_module_name('PaginationMeta')} import PaginationMeta"
        in my_item_list_response_content
    )
    assert f"{NameSanitizer.sanitize_method_name('data')}: List[MyItem]" in my_item_list_response_content
    assert f"{NameSanitizer.sanitize_method_name('meta')}: PaginationMeta" in my_item_list_response_content

    # 5.4. Check __init__.py
    init_file = models_output_dir / "__init__.py"
    assert init_file.exists(), f"{init_file} was not generated."
    init_content = init_file.read_text()
    assert "from typing import List" in init_content
    assert f"from .{NameSanitizer.sanitize_module_name('MyItem')} import MyItem" in init_content
    assert f"from .{NameSanitizer.sanitize_module_name('PaginationMeta')} import PaginationMeta" in init_content
    assert f"from .{NameSanitizer.sanitize_module_name('MyItemListResponse')} import MyItemListResponse" in init_content
    assert "__all__: List[str] = [" in init_content
    assert "'MyItem'," in init_content
    assert "'MyItemListResponse'," in init_content
    assert "'PaginationMeta'," in init_content

    # 5.5. Assert no 'data.py' (or similar anomoly) is generated
    anomalous_data_file = models_output_dir / "data.py"
    assert not anomalous_data_file.exists(), f"Anomalous file {anomalous_data_file} was generated."

    # Check for any other .py files that shouldn't be there
    generated_py_files = {f.name for f in models_output_dir.glob("*.py")}
    expected_py_files = {
        f"{NameSanitizer.sanitize_module_name('MyItem')}.py",
        f"{NameSanitizer.sanitize_module_name('PaginationMeta')}.py",
        f"{NameSanitizer.sanitize_module_name('MyItemListResponse')}.py",
        "__init__.py",
    }
    assert (
        generated_py_files == expected_py_files
    ), f"Unexpected files in models directory. Expected: {expected_py_files}, Got: {generated_py_files}"
