#!/usr/bin/env python3
"""Debug the function signature vs implementation mismatch"""

import tempfile
from pathlib import Path
import subprocess
import sys

# Add src to path
sys.path.insert(0, '/Users/villevenalainen/development/pyopenapi_gen/src')

from pyopenapi_gen.generator.client_generator import ClientGenerator

def debug_signature_issue():
    """Check function signatures vs implementations"""
    
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
        
        # Check system.py function signature
        endpoint_file = tmp_path / "test_client" / "endpoints" / "system.py"
        if endpoint_file.exists():
            print("=== Generated system.py function signature ===")
            content = endpoint_file.read_text()
            lines = content.split('\n')
            
            # Find the function that contains line 53
            for i, line in enumerate(lines):
                if 'def ' in line and 'async' in line:
                    # Show function signature and next few lines
                    print(f"Function definition at line {i+1}:")
                    for j in range(i, min(i+10, len(lines))):
                        print(f"  {j+1:3d}: {lines[j]}")
                    print()
                    
                    # If this function contains our problematic line (around 53), show more
                    if i < 53 < i + 50:  # rough estimate
                        print("*** This function contains the problematic return statement ***")
                        print()

if __name__ == "__main__":
    debug_signature_issue()