#!/usr/bin/env python3
"""
Script to check the installed version of pyopenapi-gen and verify it has cycle detection.
Run this in your other project after installing the patched version.
"""

import importlib
import inspect
import sys

def check_pyopenapi_gen():
    """Check the installed version and features of pyopenapi-gen."""
    try:
        import pyopenapi_gen
        print(f"pyopenapi-gen version: {getattr(pyopenapi_gen, '__version__', 'Unknown')}")
        
        # Check for ClientGenerator verbose mode (progress tracking)
        from pyopenapi_gen.generator.client_generator import ClientGenerator
        client_gen_init = inspect.getsource(ClientGenerator.__init__)
        has_verbose = "verbose" in client_gen_init
        print(f"Has progress tracking: {has_verbose}")
        
        # Check for cycle detection
        try:
            from pyopenapi_gen.core.parsing.context import ParsingContext
            context_source = inspect.getsource(ParsingContext)
            has_cycle_detection = "cycle_detected" in context_source
            print(f"Has cycle detection: {has_cycle_detection}")
        except (ImportError, AttributeError):
            print("Could not verify cycle detection (old version)")
            has_cycle_detection = False
            
        # Check for ENV settings
        try:
            from pyopenapi_gen.core.parsing.schema_parser import DEBUG_CYCLES, MAX_CYCLES, ENV_MAX_DEPTH
            print(f"Configured for cycle detection: DEBUG_CYCLES={DEBUG_CYCLES}, MAX_CYCLES={MAX_CYCLES}, ENV_MAX_DEPTH={ENV_MAX_DEPTH}")
        except ImportError:
            print("Could not verify cycle detection environment settings (old version)")
            
        # Path check
        print(f"Package path: {pyopenapi_gen.__file__}")
            
        if not has_verbose or not has_cycle_detection:
            print("\nWARNING: You are not using the patched version with cycle detection!")
            print("Please run: pip install /path/to/pyopenapi_gen-0.4.2-py3-none-any.whl --force-reinstall")

    except ImportError:
        print("pyopenapi-gen is not installed.")
        return False
    
    return True

if __name__ == "__main__":
    check_pyopenapi_gen()