#!/bin/bash

# Start Python scripts in the background
pm2 start app.py &
pm2 start components.py &
pm2 start machines.py &
pm2 start services.py &
pm2 start results.py &
pm2 start thresholds.py &
pm2 start getResults.py &
pm2 start getStatus.py &
pm2 start notifications.py &
pm2 start getNames.py &
pm2 start users.py &

# Wait for all background jobs to finish
wait
