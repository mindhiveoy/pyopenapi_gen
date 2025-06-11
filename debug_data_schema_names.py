#!/usr/bin/env python3
"""Debug where Data_ schema names come from"""

import sys
import yaml

# Add src to path
sys.path.insert(0, '/Users/villevenalainen/development/pyopenapi_gen/src')

from pyopenapi_gen.core.loader.loader import load_ir_from_spec

def debug_data_schema_names():
    """Check what schemas are being created and their names"""
    
    # Load the spec
    spec_path = "/Users/villevenalainen/development/pyopenapi_gen/input/business_swagger.json"
    with open(spec_path) as f:
        spec_dict = yaml.safe_load(f.read())
    
    ir = load_ir_from_spec(spec_dict)
    
    print("=== All IR schemas ===")
    schema_names = list(ir.schemas.keys())
    schema_names.sort()
    
    for name in schema_names:
        if "Data" in name or "data" in name or "_" in name:
            schema = ir.schemas[name]
            print(f"\nSchema: {name}")
            print(f"  Type: {schema.type}")
            print(f"  Has properties: {hasattr(schema, 'properties') and bool(schema.properties)}")
            if hasattr(schema, 'properties') and schema.properties:
                print(f"  Properties: {list(schema.properties.keys())}")
            print(f"  Has name attr: {hasattr(schema, 'name')}")
            if hasattr(schema, 'name'):
                print(f"  Name attr: {schema.name}")
    
    print(f"\nTotal schemas: {len(ir.schemas)}")
    
    # Find the health operation and see what schema it references
    print("\n=== Health operation schema ===")
    for op in ir.operations:
        if op.operation_id == "getSystemHealth":
            print(f"Operation: {op.operation_id}")
            for response in op.responses:
                if response.status_code == "200":
                    print(f"Response content: {list(response.content.keys())}")
                    for content_type, schema in response.content.items():
                        print(f"  {content_type}: {schema}")
                        print(f"    Schema type: {schema.type}")
                        print(f"    Schema name: {getattr(schema, 'name', 'NO NAME')}")
                        if hasattr(schema, 'properties') and schema.properties:
                            print(f"    Properties: {list(schema.properties.keys())}")

if __name__ == "__main__":
    debug_data_schema_names()