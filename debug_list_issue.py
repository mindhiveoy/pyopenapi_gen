#!/usr/bin/env python3
"""Debug the list[Type].from_dict issue"""

import tempfile
from pathlib import Path
import subprocess
import sys

# Add src to path
sys.path.insert(0, '/Users/villevenalainen/development/pyopenapi_gen/src')

from pyopenapi_gen.generator.client_generator import ClientGenerator

def debug_list_issue():
    """Check what's generating list[Type].from_dict calls"""
    
    # Use business swagger
    spec_path = "/Users/villevenalainen/development/pyopenapi_gen/input/business_swagger.json"
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Generate client
        generator = ClientGenerator()
        generator.generate(
            spec_path=spec_path,
            project_root=tmp_path,
            output_package="test_client",
            core_package="test_client.core",
            force=True,
            no_postprocess=True,  # Skip post-processing to see raw generated code
        )
        
        # Check system.py which has list[DataItem] errors
        endpoint_file = tmp_path / "test_client" / "endpoints" / "system.py"
        if endpoint_file.exists():
            print("=== Generated system.py endpoint ===")
            content = endpoint_file.read_text()
            lines = content.split('\n')
            
            # Check line 53 (one of the problematic lines)
            print("\n--- Around line 53 ---")
            start = max(0, 53 - 10)
            end = min(len(lines), 53 + 10)
            
            for i in range(start, end):
                if i < len(lines):
                    marker = " >>> " if i == 52 else "     "  # Line 53 is index 52
                    print(f"{marker}{i+1:3d}: {lines[i]}")
        
        # Also check messages.py
        endpoint_file = tmp_path / "test_client" / "endpoints" / "messages.py"
        if endpoint_file.exists():
            print("\n=== Generated messages.py endpoint ===")
            content = endpoint_file.read_text()
            lines = content.split('\n')
            
            # Check line 77 (another problematic line)
            print("\n--- Around line 77 ---")
            start = max(0, 77 - 10)
            end = min(len(lines), 77 + 10)
            
            for i in range(start, end):
                if i < len(lines):
                    marker = " >>> " if i == 76 else "     "  # Line 77 is index 76
                    print(f"{marker}{i+1:3d}: {lines[i]}")

if __name__ == "__main__":
    debug_list_issue()