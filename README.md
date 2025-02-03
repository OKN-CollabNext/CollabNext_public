# CollabNext

## Table of Contents
- [Quick Start](#quick-start)
  - [For Mac/Unix users](#for-macunix-users)
  - [For Windows users](#for-windows-users)
- [DIY Section](#diy-section)
- [Production Deployment](#production-deployment)
- [Contact Information](#contact-information)

## Quick Start

To quickly set up the CollabNext development environment, you can use the provided setup scripts. Choose the script based on your operating system:

### For Mac/Unix users:
1. Open a terminal.
2. Navigate to the project directory.
3. Run the following commands:
   ```bash
   chmod +x setup.sh  # Only needed the first time
   ./setup.sh
   ```

### For Windows users:
1. Open Command Prompt.
2. Navigate to the project directory.
3. Run the following command:
   ```batch
   setup.bat
   ```

These scripts will automatically set up the backend and frontend environments and start the development servers.

## DIY Section

If you prefer to set up the environment manually, follow these steps:

### Building React.js/Flask application locally:

1. **Change directory to backend**
   ```bash
   cd backend
   ```

2. **Python setup**
   - Create a virtual environment:
     ```bash
     python3 -m venv .venv
     ```
   - Activate the virtual environment:
     ```bash
     source .venv/bin/activate
     ```
   - If the above command doesn't work on Windows, try:
     ```batch
     cd .venv\Scripts
     activate
     cd ..\..
     ```

   - Install the required packages:
     ```bash
     pip install -r requirements.txt
     ```

3. **Run Flask app locally**
   - Execute the Python script containing your Flask application:
     ```bash
     python app.py
     ```

4. **Open a new terminal and change directory to frontend**
   ```bash
   cd frontend
   ```

5. **Install React app dependencies**
   - Run the following commands:
     ```bash
     npm install --legacy-peer-deps
     npm install @memgraph/orb
     ```

6. **Create `.env.local` file**
   - In the frontend folder, copy everything from `.env.example` and paste it into `.env.local`.

7. **Run React app locally**
   - Execute the start command:
     ```bash
     npm start
     ```

**Note:** If you encounter port issues on Mac, try:
- System Settings > General > AirDrop & Handoff > turn off AirPlay Receiver

## Production Deployment

For deploying the React SPA and Python backend together on Azure App Service, follow the guide provided in this [blog post](https://techcommunity.microsoft.com/t5/apps-on-azure-blog/deploying-react-spa-and-python-backend-together-on-the-same/ba-p/4095567).

## Contact Information

Contact Lew Lefton (collabnext.okn@gmail.com) for any more questions about this project. 
