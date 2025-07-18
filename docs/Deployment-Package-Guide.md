# CollabNext Deployment Package Guide

## Overview

The CollabNext deployment package is a simple, self-contained archive that contains everything needed to deploy CollabNext to any Kubernetes cluster. This approach avoids the complexity of Helm repositories and OCI registries while providing a reliable distribution method.

## How It Works

1. **Automated Package Creation**: Every time code is pushed to the main branch, a GitHub Actions workflow automatically:
   - Packages the Helm chart with all dependencies
   - Creates a deployment script and documentation
   - Bundles everything into a single `.tar.gz` file
   - Uploads it as a GitHub Actions artifact

2. **Single Download**: Users can download one file that contains:
   - The complete Helm chart (with all dependencies resolved)
   - An automated deployment script
   - Documentation and usage instructions
   - Version information

3. **Simple Deployment**: Users just need to:
   - Download the package
   - Extract it
   - Run the deployment script

## Accessing the Package

### Option 1: GitHub Container Registry (Recommended)

The deployment package is available as an OCI artifact in GitHub Container Registry:

```bash
# One-liner to download and deploy
curl -s https://raw.githubusercontent.com/OKN-CollabNext/CollabNext_public/main/scripts/deploy-from-ghcr.sh | bash
```

Or manually:

```bash
# Pull and extract the latest deployment package
docker run --rm -v $(pwd):/output ghcr.io/okn-collabnext/collabnext_public/deployment-package:latest cp -r /deployment /output/

# Deploy
cd deployment
./deploy.sh
```

### Option 2: GitHub Actions Artifacts

1. Go to the [GitHub Actions page](https://github.com/OKN-CollabNext/CollabNext_public/actions)
2. Click on the latest "Create Deployment Package" workflow run
3. Scroll down to the "Artifacts" section
4. Download the `collabnext-deployment` artifact

### Option 3: Direct Download

The package is also available as a direct download from the latest workflow run:
```
https://github.com/OKN-CollabNext/CollabNext_public/actions/runs/[RUN_ID]/artifacts
```

## Using the Package

1. **Download and Extract**:
   ```bash
   # Download the package (from GitHub Actions artifacts)
   tar -xzf collabnext-deployment-YYYYMMDD.tar.gz
   cd collabnext-deployment
   ```

2. **Deploy**:
   ```bash
   # Run the automated deployment script
   ./deploy.sh
   ```

3. **Access**:
   ```bash
   # Port forward to access the application
   kubectl port-forward svc/collabnext-frontend 3000:80
   ```
   Then open http://localhost:3000 in your browser

## Package Contents

The deployment package contains:

- `collabnext-alpha-*.tgz` - The complete Helm chart with all dependencies
- `deploy.sh` - Automated deployment script with error checking
- `README.md` - Complete usage instructions
- `version.txt` - Version information and included images

## Benefits of This Approach

1. **Simplicity**: One command to download and deploy
2. **Reliability**: Avoids the "Invalid Semantic Version" and other Helm packaging issues
3. **Self-Contained**: Everything needed is in one OCI artifact
4. **Versioned**: Each package is tied to a specific commit/date
5. **Accessible**: Anyone can pull from GHCR without special permissions
6. **Debuggable**: Easy to see what's included and troubleshoot issues
7. **Standardized**: Uses industry-standard OCI artifacts
8. **Cached**: Docker layers are cached for faster downloads

## For Developers

To create a new deployment package:

1. **Automatic**: Push to the main branch - the workflow runs automatically
2. **Manual**: Go to Actions → "Create Deployment Package" → "Run workflow"

The package will be available as an artifact within a few minutes.

## Troubleshooting

- **Package not found**: Check that the workflow completed successfully
- **Deployment fails**: Check the `deploy.sh` script output for specific error messages
- **Images not found**: Ensure the Docker images were built and pushed successfully

## Next Steps

This approach provides a solid foundation for distributing CollabNext. Future enhancements could include:

- Multiple package formats (zip, tar.gz)
- Platform-specific packages
- Automated testing of the package
- Integration with release workflows 