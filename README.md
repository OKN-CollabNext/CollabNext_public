# CollabNext

A collaborative research discovery platform that enables multi-modal search across academic publications, institutions, and researchers using data from OpenAlex and SemOpenAlex.

## Table of Contents
- [Quick Start (Recommended)](#quick-start-recommended)
  - [Option 1: One-Command Deployment](#option-1-one-command-deployment)
  - [Option 2: Manual Container Deployment](#option-2-manual-container-deployment)
- [Local Development](#local-development)
  - [Container-based Development](#container-based-development)
  - [Legacy Local Development](#legacy-local-development)
- [Contact Information](#contact-information)

## Quick Start (Recommended)

The fastest way to run CollabNext is using our pre-built container images and Helm chart.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm 3](https://helm.sh/docs/intro/install/)
- A Kubernetes cluster (local: [Minikube](https://minikube.sigs.k8s.io/docs/start/), [Docker Desktop](https://docs.docker.com/desktop/kubernetes/), or cloud-based)

### Option 1: One-Command Deployment

Run this single command to deploy CollabNext to your Kubernetes cluster:

```bash
curl -s https://raw.githubusercontent.com/OKN-CollabNext/CollabNext_public/main/scripts/deploy-from-ghcr.sh | bash
```

This script will:
- Download the latest Helm chart
- Pull container images from GitHub Container Registry (GHCR)
- Deploy the complete application stack
- Show you how to access the application

### Option 2: Manual Container Deployment

1. **Download the Helm chart:**
   ```bash
   curl -L -o collabnext-alpha.tgz https://github.com/OKN-CollabNext/CollabNext_public/releases/latest/download/collabnext-alpha-0.1.0.tgz
   ```

2. **Install with Helm:**
   ```bash
   helm install collabnext ./collabnext-alpha.tgz
   ```

3. **Access the application:**
   ```bash
   # Get service information
   kubectl get services
   
   # If using NodePort (local development):
   kubectl get nodes -o wide  # Get node IP
   kubectl get svc collabnext-frontend -o jsonpath='{.spec.ports[0].nodePort}'  # Get port
   
   # If using port-forward:
   kubectl port-forward svc/collabnext-frontend 3000:80
   # Then visit: http://localhost:3000
   ```

**Container Images:** All images are available at [GitHub Container Registry](https://github.com/orgs/OKN-CollabNext/packages?repo_name=CollabNext_public)

## Local Development

### Container-based Development

For local development with containers (recommended for consistency):

1. **Start with Minikube:**
   ```bash
   minikube start --driver=docker --memory=2048 --cpus=2
   ```

2. **Deploy using local values:**
   ```bash
   # Download and extract the Helm chart
   curl -L -o collabnext-alpha.tgz https://github.com/OKN-CollabNext/CollabNext_public/releases/latest/download/collabnext-alpha-0.1.0.tgz
   tar -xzf collabnext-alpha.tgz
   
   # Install with local development values
   helm install collabnext-local ./collabnext-alpha -f ./collabnext-alpha/values-local.yaml
   ```

3. **Access the application:**
   ```bash
   # Get the NodePort
   kubectl get svc collabnext-local-frontend
   
   # Get Minikube IP
   minikube ip
   
   # Visit: http://<minikube-ip>:<nodeport>
   ```

### Legacy Local Development

> **Note:** This is the old way of running the application without containers. The container-based approach above is recommended for new setups.

<details>
<summary>Click to expand legacy setup instructions</summary>

If you prefer to set up the environment manually without containers, follow these steps:

#### Quick Start Scripts (Legacy)

For Mac/Unix users:
1. Open a terminal.
2. Navigate to the project directory.
3. Run the following commands:
   ```bash
   chmod +x setup.sh  # Only needed the first time
   ./setup.sh
   ```

For Windows users:
1. Open Command Prompt.
2. Navigate to the project directory.
3. Run the following command:
   ```batch
   setup.bat
   ```

These scripts will automatically set up the backend and frontend environments and start the development servers.

#### Manual Setup (Legacy)

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

</details>

## Contact Information

Contact Lew Lefton (collabnext.okn@gmail.com) for any more questions about this project.

---

## Contributing

This is an open-source project. Contributions are welcome! Please feel free to submit issues and pull requests.

## License

See [LICENSE](LICENSE) file for details.
