#!/bin/bash

# Start Python scripts in the background
python app.py &
python components.py &
python machines.py &
python services.py &
python results.py &
python thresholds.py &
python getResults.py &
python getStatus.py &
python notifications.py &
python getNames.py &
python users.py &

# Wait for all background jobs to finish
wait
