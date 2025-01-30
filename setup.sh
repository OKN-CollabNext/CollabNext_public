#!/bin/bash

echo "Setting up CollabNext development environment..."

# Backend setup
echo "Setting up backend..."
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start backend server in background
python app.py &
BACKEND_PID=$!

# Frontend setup
echo "Setting up frontend..."
cd ../frontend

# Install dependencies
npm install --legacy-peer-deps
npm install @memgraph/orb

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    cp .env.example .env.local
    echo "Created .env.local from .env.example"
fi

# Start frontend
echo "Starting frontend application..."
npm start

# Cleanup when script is terminated
trap "kill $BACKEND_PID" EXIT