@echo off
echo Setting up CollabNext development environment...

:: Backend setup
echo Setting up backend...
cd backend

:: Create and activate virtual environment
python -m venv .venv
call .venv\Scripts\activate.bat

:: Install requirements
pip install -r requirements.txt

:: Start backend server in new window
start cmd /k "python app.py"

:: Frontend setup
echo Setting up frontend...
cd ../frontend

:: Install dependencies
call npm install --legacy-peer-deps
call npm install @memgraph/orb

:: Create .env.local if it doesn't exist
if not exist .env.local (
    copy .env.example .env.local
    echo Created .env.local from .env.example
)

:: Start frontend
echo Starting frontend application...
npm start