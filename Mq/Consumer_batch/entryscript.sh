#!/bin/bash

# Array to store process PIDs
pids=()

# Run the worker script as 5 processes
for i in {1..5}
do
   python worker.py &
   pids+=($!)  # Store the PID of each background process
done

# Function to handle process exit
handle_exit() {
    exit_code=0
    # Wait for each process and capture its exit code
    for pid in "${pids[@]}"
    do
        wait $pid
        status=$?
        # If any process exits with non-zero, store it
        if [ $status -ne 0 ]; then
            exit_code=$status
        fi
    done
    # Exit with stored exit code
    exit $exit_code
}

# Set up trap to handle script termination
trap 'handle_exit' SIGTERM SIGINT

# Wait for all processes and handle their exit codes
handle_exit
