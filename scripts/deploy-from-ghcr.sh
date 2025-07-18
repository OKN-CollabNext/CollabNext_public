#!/bin/bash
set -e

echo "🚀 Deploying CollabNext from GHCR..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm first: https://helm.sh/docs/intro/install/"
    exit 1
fi

echo "📦 Downloading deployment package from GHCR..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# Pull and extract the deployment package
docker run --rm -v $(pwd):/output ghcr.io/okn-collabnext/collabnext_public/deployment-package:latest cp -r /deployment /output/

if [ ! -d "deployment" ]; then
    echo "❌ Failed to download deployment package"
    exit 1
fi

cd deployment

# Get the chart file
CHART_FILE=$(ls *.tgz | head -1)
if [ -z "$CHART_FILE" ]; then
    echo "❌ No Helm chart found in deployment package"
    exit 1
fi

echo "📦 Installing chart: $CHART_FILE"

# Install the chart
helm install collabnext ./$CHART_FILE

echo "✅ CollabNext deployed successfully!"
echo ""
echo "🔍 To check the status:"
echo "   kubectl get pods"
echo ""
echo "🌐 To access the application:"
echo "   kubectl port-forward svc/collabnext-frontend 3000:80"
echo "   Then open http://localhost:3000 in your browser"
echo ""
echo "🗑️  To uninstall:"
echo "   helm uninstall collabnext"
echo ""
echo "🧹 Cleaning up temporary files..."
cd /
rm -rf $TEMP_DIR 