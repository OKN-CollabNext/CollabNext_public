# CI/CD Setup for CollabNext

This document explains the automated CI/CD pipeline for building and deploying CollabNext Docker images.

## Overview

The CI/CD system automatically builds and publishes Docker images for all 3 components when PRs are merged to the main branch:

- **Backend**: Flask API server (`ghcr.io/your-org/collabnext_public/backend`)
- **Frontend**: React application (`ghcr.io/your-org/collabnext_public/frontend`)  
- **Database**: PostgreSQL with custom functions (`ghcr.io/your-org/collabnext_public/database`)

## Triggers

### Automatic Triggers
- ✅ **PR Merged to Main**: When a pull request is merged (not just closed) to the main branch
- ✅ **Daily Schedule**: Packages are automatically made public (for OSS compliance)

### Manual Triggers
- 🔧 **Manual Dispatch**: You can manually trigger the workflow from GitHub Actions tab

## Workflow Jobs

### 1. Build and Push (`build-and-push`)
- **Parallel Builds**: All 3 images build simultaneously using matrix strategy
- **Multi-Architecture**: Builds for both `linux/amd64` and `linux/arm64`
- **Registry**: Pushes to GitHub Container Registry (`ghcr.io`)
- **Caching**: Uses GitHub Actions cache for faster subsequent builds

### 2. Update Helm Values (`update-helm-values`)
- **Auto-Update**: Updates Helm chart values with new image tags
- **Commit Back**: Commits updated tags back to repository
- **Versioning**: Uses `branch-shortsha` format (e.g., `main-abc1234`)

### 3. Security Scanning (`security-scan`)
- **Vulnerability Scanning**: Runs Trivy security scanner on all images
- **GitHub Security**: Results uploaded to GitHub Security tab
- **Continuous Monitoring**: Scans run after every build

### 4. Make Packages Public (`make-packages-public`)
- **OSS Compliance**: Ensures all packages are publicly accessible
- **Automatic**: Runs after successful builds and daily
- **API-Driven**: Uses GitHub API to update package visibility

## Image Tagging Strategy

Each image gets multiple tags for different use cases:

```bash
# Latest (main branch only)
ghcr.io/your-org/collabnext_public/backend:latest

# Branch + SHA (for tracking)
ghcr.io/your-org/collabnext_public/backend:main-abc1234

# Semantic versioning (if using git tags)
ghcr.io/your-org/collabnext_public/backend:v1.2.3
ghcr.io/your-org/collabnext_public/backend:1.2
```

## Setup Requirements

### Repository Settings
1. **Branch Protection**: Ensure main branch has protection rules
2. **Actions Permissions**: Enable GitHub Actions in repository settings
3. **Package Permissions**: Enable "Write" permissions for `GITHUB_TOKEN`

### No Secrets Required! 🎉
- Uses built-in `GITHUB_TOKEN` (no manual setup needed)
- Automatically inherits repository permissions
- Works out-of-the-box for public repositories

## Using the Images

### Local Development
```bash
# Pull the latest images
docker pull ghcr.io/your-org/collabnext_public/backend:latest
docker pull ghcr.io/your-org/collabnext_public/frontend:latest
docker pull ghcr.io/your-org/collabnext_public/database:latest
```

### Kubernetes Deployment
The Helm values are automatically updated, so just deploy:
```bash
helm upgrade collabnext-local ./helm/collabnext_alpha -f values-local.yaml
```

### Production Deployment
```bash
helm upgrade collabnext-prod ./helm/collabnext_alpha -f values.yaml
```

## Monitoring

### GitHub Actions
- **Workflow Status**: Check Actions tab for build status
- **Build Logs**: View detailed logs for each job
- **Artifacts**: Download security scan results

### GitHub Packages
- **Package Registry**: View published images at `github.com/orgs/your-org/packages`
- **Download Stats**: Monitor image pull statistics
- **Vulnerability Reports**: Security scan results

### GitHub Security
- **Security Tab**: View vulnerability scan results
- **Dependabot**: Automated dependency updates
- **Code Scanning**: Security analysis results

## Troubleshooting

### Build Failures
1. **Check Logs**: View GitHub Actions logs for specific errors
2. **Dockerfile Issues**: Verify Dockerfiles build locally
3. **Dependencies**: Ensure all COPY commands reference existing files

### Permission Issues
```bash
# If packages aren't public, manually run:
gh workflow run make-packages-public.yml
```

### Image Not Updating
1. **Check Tags**: Verify new tags are created
2. **Helm Values**: Ensure values files are updated
3. **Cache Issues**: Try clearing GitHub Actions cache

## Local Testing

Test the CI/CD workflow locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act

# Test the workflow
act pull_request -e .github/workflows/test-event.json

# Test specific job
act -j build-and-push
```

## Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
2. **Make Changes**: Develop your feature
3. **Create PR**: Open pull request to main branch
4. **Review & Merge**: After approval, merge PR
5. **Automatic Build**: CI/CD automatically builds and deploys
6. **Verify**: Check GitHub Packages for new images

---

For questions or issues with the CI/CD pipeline, please create an issue in the repository. 