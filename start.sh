#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Alignify Application...${NC}"

# First, check if Python and Node.js are installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 could not be found. Please install Python 3 and try again."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "Node.js could not be found. Please install Node.js and try again."
    exit 1
fi

# Start the backend server in the background
echo -e "${GREEN}Starting backend server...${NC}"
cd backend || exit
python3 app.py &
BACKEND_PID=$!
cd ..

# Give the backend server a moment to start
sleep 2

# Start the frontend development server
echo -e "${GREEN}Starting frontend server...${NC}"
cd frontend || exit
npm start &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

# Function to handle script termination
cleanup() {
    echo -e "${BLUE}Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap CTRL+C and call cleanup
trap cleanup INT

# Keep the script running
while true; do
    sleep 1
done 