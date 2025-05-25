#!/usr/bin/env python3
"""Simple test to verify self-referencing type fix."""

import tempfile
import shutil
import json
from pathlib import Path
import sys
import os
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pyopenapi_gen.generator.client_generator import ClientGenerator

def test_self_ref():
    # Create minimal spec with self-reference
    spec_content = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "getTest",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TreeNode"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "TreeNode": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "parent": {
                            "$ref": "#/components/schemas/TreeNode",
                            "description": "Parent node"
                        },
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/TreeNode"},
                            "description": "Child nodes"
                        }
                    },
                    "required": ["id"]
                }
            }
        }
    }
    
    temp_dir = Path(tempfile.mkdtemp(prefix='pyopenapi_test_'))
    try:
        # Write spec to file
        spec_file = temp_dir / "spec.json"
        spec_file.write_text(json.dumps(spec_content, indent=2))
        
        # Generate client
        generator = ClientGenerator(verbose=False)
        generator.generate(
            spec_path=str(spec_file),
            project_root=temp_dir,
            output_package='test_client',
            force=True,
            no_postprocess=True
        )
        
        # Check generated code
        entry_file = temp_dir / 'test_client' / 'models' / 'tree_node.py'
        if entry_file.exists():
            content = entry_file.read_text()
            print("Generated TreeNode model:")
            print("=" * 50)
            print(content)
            print("=" * 50)
            
            # Check for forward references
            if '"Optional[TreeNode]"' in content:
                print("✓ Self-reference correctly quoted for Optional field")
            else:
                print("✗ Optional self-reference not quoted correctly")
                
            if '"List[TreeNode]"' in content:
                print("✓ Self-reference correctly quoted for List field")
            else:
                print("✗ List self-reference not quoted correctly")
        else:
            print("Entry file not found")
            print("Available files:")
            for f in (temp_dir / 'test_client' / 'models').glob('*'):
                print(f" - {f.name}")
    
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_self_ref()