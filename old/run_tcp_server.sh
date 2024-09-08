#!/bin/bash

# Function to read the IP and port from config.ini
function get_port_info() {
    TCP_SERVER_PORT=$(grep "TCP_server_port" config.ini | cut -d'=' -f2 | tr -d ' ')
}

# Handle command-line argument to select the Python script
SCRIPT_PATH="start_code/tcp_server.py"  # Default path
if [ "$1" == "answer" ]; then
    SCRIPT_PATH="answer/tcp_server.py"
fi

# Cleanup function to release the port when interrupted
function cleanup() {
    echo "Interrupt signal received, releasing the port..."
    get_port_info
    fuser -k "$TCP_SERVER_PORT/tcp"  # Kill processes using the specified port
    sleep 1  # Ensure there is enough time to kill the process
    echo "Port $TCP_SERVER_PORT has been released"
    exit 0
}

# Catch SIGINT (Ctrl+C) signal and call the cleanup function
trap cleanup SIGINT

# Run the Python script
echo "Running Python script: $SCRIPT_PATH"
python "$SCRIPT_PATH" &

# Keep the script running and waiting for interruptions
wait
