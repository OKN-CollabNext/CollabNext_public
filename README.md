# CollabNext_alpha

## Refer to below for steps to build the app

https://techcommunity.microsoft.com/t5/apps-on-azure-blog/deploying-react-spa-and-python-backend-together-on-the-same/ba-p/4095567


## Building React.js/Flask application locally:

1. Change directory to backend<br>
`cd backend`<br>

2. Python setup<br>
`python3 -m venv .venv`<br>
`source .venv/bin/activate`<br>

 If this command doesn't work on windows try going to the directory: <br>
 `cd .venv\Scripts` <br>
 `activate` <br>
 `cd ..` x2 <br>

`pip install -r requirements.txt`<br>

3. Run Flask app locally<br>
 To run the Flask application locally, you need to execute the Python script containing your Flask application 

   `python app.py`

4. Open new terminal and change directory to frontend<br>
`cd frontend`<br>

5. Install React app dependencies
`npm install --legacy-peer-deps`<br>
`npm install @memgraph/orb` <br>

Create `.env.local` file in the outermost folder level (in the collabnext_alpha folder), copy everthing in `.env.example` and paste in the`.env.local` file

6. Run React app locally<br>
 To run the React application locally, you need to execute the start command

   `npm start`


Note: If you are having some trouble with the ports on Mac, try:
System Settings > General > AirDrop & Handoff > turn off AirPlay Receiver
