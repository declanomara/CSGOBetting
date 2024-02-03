#!/bin/bash

# This is a simple scheduler script that runs a command roughly every 5 seconds
# It is not perfect, but it is simple and works well enough for most use cases

# The commands to run
COMMANDS=(
  "cd /home/declan/Documents/CSGOBetting/ && .venv/bin/python3 main.py csgobetting.db >> output.log 2>error.log",
  "cd /home/declan/Documents/CSGOBetting/ && .venv/bin/python3 automated_betting.py >> betting.log 2>error.log)",
  "echo 'Ran the commands at $(date)'"
)

# The time to wait between commands
SLEEP_TIME=5

# Run the commands
while true; do
  for COMMAND in "${COMMANDS[@]}"; do
    eval $COMMAND
  done
  sleep $SLEEP_TIME
done
```