# Unified Artifact Deployment with Helm OCI

This document explains the unified deployment approach where **everything** (Docker images + Helm chart) is published as OCI artifacts to GitHub Container Registry.

## 🎯 Overview

Instead of managing separate Docker images and Helm charts, we now have a **unified artifact system** where:

- **Docker Images**: Backend, Frontend, Database
- **Helm Chart**: Complete application topology as OCI artifact
- **Deployment Manifest**: Single source of truth for deployment commands

## 🏗️ Architecture

```
GitHub Repository
├── Docker Images (OCI)
│   ├── ghcr.io/okn-collabnext/collabnext_public/backend:latest
│   ├── ghcr.io/okn-collabnext/collabnext_public/frontend:latest
│   └── ghcr.io/okn-collabnext/collabnext_public/database:latest
├── Helm Chart (OCI)
│   └── ghcr.io/okn-collabnext/collabnext_public/helm-chart:latest
└── Deployment Manifest (JSON)
    └── deployment-manifest.json
```

## 🚀 Benefits

### **1. Unified Platform**
- Everything in one registry (GitHub Container Registry)
- Consistent versioning across all artifacts
- Single source of truth for deployments

### **2. GitOps Ready**
- Helm charts as OCI artifacts work with ArgoCD, Flux, etc.
- Version-controlled application topology
- Immutable artifact references

### **3. Simplified Deployment**
- One command to deploy entire application
- No need to manage separate image tags
- Consistent across environments

### **4. Enterprise Features**
- OCI artifacts support signing and verification
- Better security and compliance
- Works with enterprise registries

## 📦 Available Workflows

### **1. Build All Artifacts** (Default - Runs on PR Merge)
```yaml
.github/workflows/build-all-artifacts.yml
```
- **Triggers**: ✅ PR merge to main (automatic), 🔧 Manual dispatch
- **Output**: All Docker images + Helm chart + deployment manifest
- **Use Case**: Complete application deployment (default behavior)

### **2. Build Images Only** (Manual Only)
```yaml
.github/workflows/build-and-push-images.yml
```
- **Triggers**: 🔧 Manual dispatch only
- **Output**: Docker images only
- **Use Case**: When you only want to rebuild images without Helm chart

### **3. Build Helm Chart Only** (Manual Only)
```yaml
.github/workflows/build-and-push-helm-chart.yml
```
- **Triggers**: 🔧 Manual dispatch only
- **Output**: Helm chart only
- **Use Case**: When only infrastructure/topology changes

### **4. Test Docker Builds** (Manual Only)
```yaml
.github/workflows/test-docker-builds.yml
```
- **Triggers**: 🔧 Manual dispatch only
- **Output**: Build tests (no pushing)
- **Use Case**: Testing Docker builds without publishing

## 🎯 Deployment Commands

### **Local Development**
```bash
# Deploy to local Kubernetes
helm install collabnext-local oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version latest -f values-local.yaml
```

### **Production**
```bash
# Deploy to production
helm install collabnext-prod oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version latest -f values.yaml
```

### **Upgrade Existing**
```bash
# Upgrade existing deployment
helm upgrade collabnext oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version latest
```

### **Specific Version**
```bash
# Deploy specific version
helm install collabnext oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version main-abc1234
```

## 📋 Deployment Manifest

The workflow generates a `deployment-manifest.json` that contains:

```json
{
  "application": "collabnext",
  "version": "main-abc1234",
  "build": {
    "commit": "abc1234...",
    "branch": "main",
    "triggered_by": "username",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "artifacts": {
    "helm_chart": {
      "repository": "ghcr.io/okn-collabnext/collabnext_public/helm-chart",
      "version": "main-abc1234",
      "latest": "ghcr.io/okn-collabnext/collabnext_public/helm-chart:latest"
    },
    "images": {
      "backend": "ghcr.io/okn-collabnext/collabnext_public/backend:latest",
      "frontend": "ghcr.io/okn-collabnext/collabnext_public/frontend:latest",
      "database": "ghcr.io/okn-collabnext/collabnext_public/database:latest"
    }
  },
  "deployment": {
    "local": {
      "command": "helm install collabnext-local oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version main-abc1234 -f values-local.yaml",
      "description": "Deploy to local Kubernetes cluster"
    },
    "production": {
      "command": "helm install collabnext-prod oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version main-abc1234 -f values.yaml",
      "description": "Deploy to production environment"
    }
  }
}
```

## 🔄 Workflow Integration

### **GitOps Tools**
- **ArgoCD**: Use OCI Helm charts directly
- **Flux**: Supports OCI Helm repositories
- **Jenkins X**: Native OCI support
- **Tekton**: Pipeline integration

### **CI/CD Platforms**
- **GitHub Actions**: Native integration
- **GitLab CI**: OCI registry support
- **Azure DevOps**: Container registry integration
- **AWS CodePipeline**: ECR integration

## 🛠️ Advanced Usage

### **Helm Repository Setup**
```bash
# Add OCI repository
helm repo add collabnext oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart

# List available versions
helm search repo collabnext --versions

# Install specific version
helm install my-app collabnext/collabnext-alpha --version 1.0.0
```

### **Artifact Verification**
```bash
# Verify OCI artifact
helm show chart oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart:latest

# Show values
helm show values oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart:latest
```

### **Rollback Strategy**
```bash
# List deployment history
helm history collabnext

# Rollback to previous version
helm rollback collabnext 1

# Rollback to specific version
helm upgrade collabnext oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart --version previous-version
```

## 🔍 Monitoring

### **GitHub Packages**
- View all artifacts at: `github.com/okn-collabnext/packages`
- Download statistics
- Vulnerability reports

### **GitHub Actions**
- Workflow status and logs
- Artifact downloads
- Security scan results

### **Kubernetes**
```bash
# Check deployment status
kubectl get pods -l app.kubernetes.io/instance=collabnext

# View logs
kubectl logs -l app.kubernetes.io/instance=collabnext

# Check Helm release
helm list
helm status collabnext
```

## 🚨 Troubleshooting

### **OCI Registry Issues**
```bash
# Check registry access
helm registry login ghcr.io

# Verify chart exists
helm show chart oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart:latest
```

### **Deployment Issues**
```bash
# Check Helm chart values
helm get values collabnext

# Debug deployment
helm install --dry-run --debug collabnext oci://ghcr.io/okn-collabnext/collabnext_public/helm-chart

# Check Kubernetes events
kubectl get events --sort-by='.lastTimestamp'
```

### **Image Pull Issues**
```bash
# Check image availability
docker pull ghcr.io/okn-collabnext/collabnext_public/backend:latest

# Verify image tags
docker images ghcr.io/okn-collabnext/collabnext_public/*
```

## 🎉 Summary

This unified approach provides:

- **🎯 Single Source of Truth**: Everything in one registry
- **🚀 Simplified Deployment**: One command deploys everything
- **🔒 Better Security**: OCI artifacts with signing support
- **📈 Scalability**: Works with enterprise GitOps tools
- **🔄 Consistency**: Same artifacts across all environments
- **⚡ Smart Automation**: Build All Artifacts runs by default, others on-demand

The result is a **production-ready, enterprise-grade deployment system** that's simple to use and maintain! 🎉 