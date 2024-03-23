#!/bin/bash

# Start Python scripts in the background
pkill -f 'python app.py' &
pkill -f 'python components.py' &
pkill -f 'python machines.py' &
pkill -f 'python services.py' &
pkill -f 'python results.py' &
pkill -f 'python thresholds.py' &
pkill -f 'python getResults.py' &
pkill -f 'python getStatus.py' &
pkill -f 'python notifications.py' &
pkill -f 'python getNames.py' &
pkill -f 'python users.py' &

# Wait for all background jobs to finish
wait
