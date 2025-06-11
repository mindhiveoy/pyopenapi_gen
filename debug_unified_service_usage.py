#!/usr/bin/env python3
"""Debug unified service usage - signature vs handler"""

import tempfile
from pathlib import Path
import sys
import json

# Add src to path  
sys.path.insert(0, '/Users/villevenalainen/development/pyopenapi_gen/src')

from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.helpers.endpoint_utils import get_return_type_unified
from pyopenapi_gen.types.services.type_service import UnifiedTypeService
from pyopenapi_gen.context.render_context import RenderContext
import yaml

def debug_unified_service_usage():
    """Compare what signature generator vs response handler use"""
    
    # Load the spec
    spec_path = "/Users/villevenalainen/development/pyopenapi_gen/input/business_swagger.json"
    with open(spec_path) as f:
        spec_dict = yaml.safe_load(f.read())
    
    ir = load_ir_from_spec(spec_dict)
    
    # Create context
    render_context = RenderContext(
        core_package_name="test_client.core",
        package_root_for_generated_code="/tmp/test",
        overall_project_root="/tmp",
        parsed_schemas=ir.schemas,
    )
    
    # Find operations that mypy complained about
    problematic_ops = [
        "getSystemHealth",  # system.py:53
        # Let's find some from messages.py too
    ]
    
    # Look for operations that might return list[DataItem] 
    print("=== Checking all operations for list[DataItem] returns ===")
    list_operations = []
    
    for op in ir.operations:
        # Test signature generator approach
        signature_return_type = get_return_type_unified(op, render_context, ir.schemas)
        
        # Test response handler approach  
        type_service = UnifiedTypeService(ir.schemas)
        handler_return_type, needs_unwrap = type_service.resolve_operation_response_with_unwrap_info(op, render_context)
        
        # Check for list types
        if "list[" in signature_return_type.lower() or "list[" in handler_return_type.lower():
            list_operations.append({
                "operation_id": op.operation_id,
                "path": op.path,
                "signature_type": signature_return_type,
                "handler_type": handler_return_type,
                "needs_unwrap": needs_unwrap,
                "match": signature_return_type == handler_return_type
            })
    
    print(f"Found {len(list_operations)} operations with list return types:")
    for op_info in list_operations:
        print(f"\nOperation: {op_info['operation_id']}")
        print(f"Path: {op_info['path']}")
        print(f"Signature type: {op_info['signature_type']}")
        print(f"Handler type: {op_info['handler_type']}")
        print(f"Needs unwrap: {op_info['needs_unwrap']}")
        print(f"Match: {'✅' if op_info['match'] else '❌'}")
        
        if not op_info['match']:
            print("  ^^^ MISMATCH FOUND!")

if __name__ == "__main__":
    debug_unified_service_usage()