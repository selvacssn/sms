#!/bin/bash

# Run the worker script as 5 processes
for i in {1..5}
do
   python worker.py &
done

# Wait for all background processes to finish
wait
