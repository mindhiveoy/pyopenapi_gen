#!/usr/bin/env python3
"""Debug after unified service fix"""

import tempfile
from pathlib import Path
import subprocess
import sys

# Add src to path
sys.path.insert(0, '/Users/villevenalainen/development/pyopenapi_gen/src')

from pyopenapi_gen.generator.client_generator import ClientGenerator

def debug_after_fix():
    """Check what's generated now"""
    
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
        
        # Check agents.py which has multiple failures
        endpoint_file = tmp_path / "test_client" / "endpoints" / "agents.py"
        if endpoint_file.exists():
            print("=== Generated agents.py endpoint ===")
            content = endpoint_file.read_text()
            lines = content.split('\n')
            
            # Check line 190 (one of the problematic lines)
            print("\n--- Around line 190 ---")
            start = max(0, 190 - 5)
            end = min(len(lines), 190 + 5)
            
            for i in range(start, end):
                if i < len(lines):
                    marker = " >>> " if i == 189 else "     "  # Line 190 is index 189
                    print(f"{marker}{i+1:3d}: {lines[i]}")
        
        else:
            print("agents.py not found!")

if __name__ == "__main__":
    debug_after_fix()