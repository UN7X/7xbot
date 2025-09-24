#!/bin/bash

# 7xBot Startup Script
# Starts the bot with restart monitoring

echo "Starting 7xBot v2.0 (Cog System)..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please copy .env.example to .env and configure it."
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Please edit .env with your bot token before running again."
    exit 1
fi

# Start restart monitor in background
echo "Starting restart monitor..."
./restart_bot.sh &
MONITOR_PID=$!

echo "Monitor PID: $MONITOR_PID"

# Start the bot
echo "Starting bot..."
python3 bot_main.py

# Cleanup on exit 
echo "Bot stopped. Cleaning up monitor..."
kill $MONITOR_PID 2>/dev/null

echo "7xBot shutdown complete."