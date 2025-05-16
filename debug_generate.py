#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time
import logging
import traceback

# Set timeout in seconds
TIMEOUT = 180  # Extended timeout for more debug info

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_with_timeout():
    """Run the generator with a timeout"""
    logger.info(f"Running generator with {TIMEOUT} second timeout...")

    # Set environment variables to increase verbosity
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'  # Prevent Python from buffering output
    env['LOGLEVEL'] = 'DEBUG'      # Set logging level to DEBUG

    # Add environment variable for cycle detection
    env['PYOPENAPI_DEBUG_CYCLES'] = '1'  # Enable cycle detection logging
    env['PYOPENAPI_MAX_CYCLES'] = '10'   # Stop after detecting 10 cycles

    cmd = f"cd /Users/villevenalainen/development/mainio.app/packages/pyapis && python -m pyapis.commands.openapi_generator business --no-enhanced-client"
    logger.info(f"Running command: {cmd}")

    # Run the pyapis generator with subprocess
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True,
        env=env,
        bufsize=1  # Line buffered
    )

    # Start timer
    start_time = time.time()
    output_lines = []
    error_lines = []
    cycle_lines = []  # Track cycle detection messages

    # Function to read from streams without blocking
    def read_stream(stream, lines):
        line = stream.readline()
        if line:
            lines.append(line.rstrip())

            # Check for cycle detection messages and highlight them
            if "CYCLE DETECTED" in line:
                cycle_lines.append(line.rstrip())
                print(f"\033[91m{line.rstrip()}\033[0m")  # Print in red
            else:
                print(line.rstrip())
            return True
        return False

    # Check for timeout and capture output in real-time
    while process.poll() is None:
        # Read stdout and stderr without blocking
        stdout_ready = read_stream(process.stdout, output_lines)
        stderr_ready = read_stream(process.stderr, error_lines)

        # If neither stdout nor stderr have data, sleep briefly
        if not stdout_ready and not stderr_ready:
            time.sleep(0.1)

        # Check for timeout
        elapsed = time.time() - start_time
        if elapsed > TIMEOUT:
            logger.warning(f"Process timed out after {TIMEOUT} seconds! Killing...")
            # Dump Python stack trace before killing the process
            try:
                logger.warning("Attempting to get Python stack trace...")
                os.kill(process.pid, signal.SIGUSR1)  # Send SIGUSR1 to trigger traceback dump
                time.sleep(1)  # Give it a moment to dump
            except Exception as e:
                logger.error(f"Failed to get stack trace: {e}")

            process.kill()
            break

    # Get any remaining output
    remaining_out, remaining_err = process.communicate()

    if remaining_out:
        for line in remaining_out.splitlines():
            output_lines.append(line)
            if "CYCLE DETECTED" in line:
                cycle_lines.append(line)
                print(f"\033[91m{line}\033[0m")  # Print in red
            else:
                print(line)

    if remaining_err:
        for line in remaining_err.splitlines():
            error_lines.append(line)
            if "CYCLE DETECTED" in line:
                cycle_lines.append(line)
                print(f"\033[91mERROR: {line}\033[0m", file=sys.stderr)  # Red error
            else:
                print(f"ERROR: {line}", file=sys.stderr)

    # Write output to files for analysis
    with open("generator_stdout.log", "w") as f:
        f.write("\n".join(output_lines))

    with open("generator_stderr.log", "w") as f:
        f.write("\n".join(error_lines))

    # Write detected cycles to a separate file for easy analysis
    if cycle_lines:
        with open("generator_cycles.log", "w") as f:
            f.write("\n".join(cycle_lines))
        logger.info(f"Detected {len(cycle_lines)} cycle-related log lines, saved to generator_cycles.log")

    logger.info(f"Stdout saved to generator_stdout.log ({len(output_lines)} lines)")
    logger.info(f"Stderr saved to generator_stderr.log ({len(error_lines)} lines)")

    # Print summary of detected cycles
    if cycle_lines:
        logger.warning("CYCLE DETECTION SUMMARY:")
        unique_cycles = set()
        for line in cycle_lines:
            if "CYCLE DETECTED" in line and "->" in line:
                # Extract cycle path
                path_start = line.find("CYCLE DETECTED") + len("CYCLE DETECTED")
                path = line[path_start:].strip()
                if path and "->" in path:
                    unique_cycles.add(path)

        for i, cycle in enumerate(unique_cycles, 1):
            logger.warning(f"Cycle {i}: {cycle}")

    return process.returncode

def run_with_profiling():
    """Run the generator with profiling enabled"""
    import cProfile
    import pstats
    import io

    logger.info("Running generator with profiling...")

    pr = cProfile.Profile()
    pr.enable()
    try:
        returncode = run_with_timeout()
    finally:
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(30)  # Top 30 time-consuming functions
        print(s.getvalue())

        # Save profile stats to file
        with open("generator_profile.txt", "w") as f:
            f.write(s.getvalue())
        logger.info("Profile stats saved to generator_profile.txt")

    return returncode

if __name__ == "__main__":
    try:
        # Check for profiling flag
        if "--profile" in sys.argv:
            returncode = run_with_profiling()
        else:
            returncode = run_with_timeout()

        logger.info(f"Process completed with return code: {returncode}")
        sys.exit(returncode)
    except Exception as e:
        logger.error(f"Error in debug_generate.py: {e}")
        traceback.print_exc()
        sys.exit(1)