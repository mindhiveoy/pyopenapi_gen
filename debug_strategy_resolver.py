#!/usr/bin/env python3
"""Debug the new strategy resolver"""

import sys
import yaml

# Add src to path  
sys.path.insert(0, '/Users/villevenalainen/development/pyopenapi_gen/src')

from pyopenapi_gen.core.loader.loader import load_ir_from_spec
from pyopenapi_gen.types.strategies import ResponseStrategyResolver
from pyopenapi_gen.context.render_context import RenderContext

def debug_strategy_resolver():
    """Test the new unified strategy resolver"""
    
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
    
    # Create strategy resolver
    strategy_resolver = ResponseStrategyResolver(ir.schemas)
    
    # Test the health operation
    health_op = None
    for op in ir.operations:
        if op.operation_id == "getSystemHealth":
            health_op = op
            break
    
    if not health_op:
        print("Could not find health operation")
        return
        
    print(f"=== Testing Strategy Resolver for {health_op.operation_id} ===")
    
    strategy = strategy_resolver.resolve(health_op, render_context)
    
    print(f"Return type: {strategy.return_type}")
    print(f"Needs unwrapping: {strategy.needs_unwrapping}")
    print(f"Unwrap field: {strategy.unwrap_field}")
    print(f"Is streaming: {strategy.is_streaming}")
    print(f"Target schema: {strategy.target_schema.name if strategy.target_schema else None}")
    print(f"Wrapper schema: {strategy.wrapper_schema.name if strategy.wrapper_schema else None}")
    
    print("\n=== Testing a few more operations ===")
    
    test_operations = ["listDatasources", "addMessages", "authenticateUser"]
    for op_id in test_operations:
        op = next((o for o in ir.operations if o.operation_id == op_id), None)
        if op:
            strategy = strategy_resolver.resolve(op, render_context)
            print(f"\n{op_id}:")
            print(f"  Return type: {strategy.return_type}")
            print(f"  Needs unwrapping: {strategy.needs_unwrapping}")
            print(f"  Unwrap field: {strategy.unwrap_field}")

if __name__ == "__main__":
    debug_strategy_resolver()