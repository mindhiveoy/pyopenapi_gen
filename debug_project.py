#!/usr/bin/env python3
"""
Debug script for tracking cycle detection and progress in pyopenapi-gen.
This script will run pyopenapi-gen with detailed logging and cycle detection.
"""

import argparse
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Debug pyopenapi-gen execution with cycle detection')
parser.add_argument('--spec', required=True, help='Path to the OpenAPI spec file')
parser.add_argument('--project-root', required=True, help='Path to the project root directory')
parser.add_argument('--output-package', required=True, help='Output package path (e.g., pyapis.my_api)')
parser.add_argument('--core-package', help='Core package path (e.g., pyapis.core)')
parser.add_argument('--force', action='store_true', help='Force overwrite existing files')
parser.add_argument('--no-postprocess', action='store_true', help="Skip post-processing (faster)")
parser.add_argument('--max-depth', type=int, default=100, help="Max recursion depth (default: 100)")
parser.add_argument('--timeout', type=int, default=300, help="Timeout in seconds (default: 300)")
parser.add_argument('--verbose', '-v', action='store_true', help="Enable verbose output")
args = parser.parse_args()

# Set up environment variables for cycle detection
os.environ['PYOPENAPI_DEBUG_CYCLES'] = '1'
os.environ['PYOPENAPI_MAX_CYCLES'] = '10'
os.environ['PYOPENAPI_MAX_DEPTH'] = str(args.max_depth)
os.environ['PYTHONUNBUFFERED'] = '1'  # Prevent Python from buffering output

# Create a command for running the generator
cmd = [
    sys.executable, '-m', 'pyopenapi_gen.cli', 'gen', args.spec,
    '--project-root', args.project_root,
    '--output-package', args.output_package
]

if args.core_package:
    cmd.extend(['--core-package', args.core_package])
if args.force:
    cmd.append('--force')
if args.no_postprocess:
    cmd.append('--no-postprocess')

print(f"Running command: {' '.join(cmd)}")
print(f"With environment variables: PYOPENAPI_DEBUG_CYCLES=1, PYOPENAPI_MAX_DEPTH={args.max_depth}")

# Create log files
log_dir = Path(tempfile.mkdtemp(prefix="pyopenapi_debug_"))
stdout_log = log_dir / "stdout.log"
stderr_log = log_dir / "stderr.log"
cycles_log = log_dir / "cycles.log"

print(f"Logs will be written to: {log_dir}")

# Start the process
start_time = time.time()
with open(stdout_log, 'w') as stdout_file, open(stderr_log, 'w') as stderr_file, open(cycles_log, 'w') as cycles_file:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    def handle_output(stream, file, is_stderr=False):
        for line in stream:
            # Write to file
            file.write(line)
            file.flush()
            
            # Write to console with appropriate color
            if "CYCLE DETECTED" in line:
                # Red for cycle detection messages
                print(f"\033[91m{line.strip()}\033[0m")
                cycles_file.write(line)
                cycles_file.flush()
            elif args.verbose or is_stderr or "ERROR" in line or "WARNING" in line:
                # Default color for normal output
                print(line.strip())
    
    # Start threads to handle stdout and stderr
    from threading import Thread
    stdout_thread = Thread(target=handle_output, args=(process.stdout, stdout_file), daemon=True)
    stderr_thread = Thread(target=handle_output, args=(process.stderr, stderr_file, True), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait for the process to complete or timeout
    try:
        return_code = process.wait(timeout=args.timeout)
        elapsed_time = time.time() - start_time
        print(f"\nProcess completed with return code {return_code} in {elapsed_time:.2f} seconds.")
    except subprocess.TimeoutExpired:
        print(f"\n\033[91mProcess timed out after {args.timeout} seconds! Killing...\033[0m")
        process.kill()
        return_code = -1
        elapsed_time = args.timeout
        
        # Try to get a Python traceback by sending SIGUSR1
        try:
            os.kill(process.pid, signal.SIGUSR1)
            time.sleep(1)  # Give it time to dump traceback
        except:
            pass

# Print summary
print(f"\nRun completed in {elapsed_time:.2f} seconds with return code {return_code}")
print(f"Logs are available at:")
print(f"  Stdout: {stdout_log}")
print(f"  Stderr: {stderr_log}")
print(f"  Cycles: {cycles_log}")

# Check for cycles
with open(cycles_log, 'r') as f:
    cycle_content = f.read()
    if cycle_content:
        print("\n\033[91mCycles detected during generation:\033[0m")
        print(cycle_content)
    else:
        print("\nNo cycles detected in the logs.")

# If it failed, suggest checking the logs
if return_code != 0:
    print("\n\033[91mGeneration failed!\033[0m Check the logs for details.")
    sys.exit(return_code)