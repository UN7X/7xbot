#!/bin/bash

# 7xBot Restart Script
# This script monitors for the restart flag and restarts the bot when needed

BOT_SCRIPT="bot_main.py"
RESTART_FLAG="restart_flag"
LOG_FILE="bot_restart.log"

echo "$(date): 7xBot Restart Monitor Started" >> "$LOG_FILE"

while true; do
    # Check if restart flag exists
    if [ -f "$RESTART_FLAG" ]; then
        echo "$(date): Restart flag detected, killing bot process..." >> "$LOG_FILE"
        
        # Remove restart flag
        rm "$RESTART_FLAG"
        
        # Kill existing Python processes running the bot
        pkill -f "$BOT_SCRIPT"
        
        # Wait a moment for processes to terminate
        sleep 3
        
        echo "$(date): Restarting bot..." >> "$LOG_FILE"
        
        # Restart the bot
        python3 "$BOT_SCRIPT" >> "$LOG_FILE" 2>&1 &
        
        echo "$(date): Bot restarted with PID $!" >> "$LOG_FILE"
    fi
    
    # Check every 5 seconds
    sleep 5
done