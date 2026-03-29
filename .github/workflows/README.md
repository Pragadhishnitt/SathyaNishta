# GitHub Actions Workflows

This directory contains the CI/CD pipeline for SathyaNishta application.

## Workflows Overview

### 1. CI Pipeline (`ci.yml`)
**Triggers**: Push to `main`/`develop` branches, Pull Requests to `main`

**Jobs**:
- **Backend Tests**: Python linting, formatting, unit tests with coverage
- **Frontend Tests**: TypeScript compilation, ESLint, build verification
- **Security Scan**: Trivy vulnerability scanner, GitGuardian secrets detection
- **Dockerfile Lint**: Hadolint for Docker file best practices

### 2. Build and Push (`build-and-push.yml`)
**Triggers**: Successful CI Pipeline completion, Push to `main`

**Jobs**:
- **Build Backend**: Multi-platform Docker build and push to Artifact Registry
- **Build Frontend**: Production Docker build and push to Artifact Registry
- **Security Scan**: Container image vulnerability scanning

### 3. Deploy (`deploy.yml`)
**Triggers**: Successful build completion

**Jobs**:
- **Deploy to Production**: SSH deployment to VM with health checks
- **Smoke Tests**: Post-deployment verification
- **Rollback**: Automatic rollback on health check failures

## Required GitHub Secrets

Add these secrets to your repository:

```
GCP_PROJECT_ID=dotted-carrier-483916-b5
GCP_SA_KEY=[Service account JSON key]
GCP_REGION=asia-south1
GCP_ZONE=asia-south1-a
VM_NAME=sathyanishta-1
STATIC_IP=34.100.219.13
GITGUARDIAN_API_KEY=[GitGuardian API key for secrets detection]
```

## Deployment Flow

1. **Code Push** → CI Pipeline runs tests
2. **Tests Pass** → Docker images built and pushed
3. **Images Ready** → Deployment to production VM
4. **Health Checks** → Application goes live
5. **Monitoring** → Ongoing health verification

## Security Features

- **Code Quality**: Black, flake8, isort, ESLint
- **Vulnerability Scanning**: Trivy for code and containers
- **Secrets Detection**: GitGuardian for exposed credentials
- **Container Security**: Multi-stage builds, minimal base images

## Monitoring and Alerts

- **Health Checks**: Backend (`/health`) and Frontend endpoints
- **Rollback**: Automatic on deployment failures
- **Notifications**: Success/failure alerts
- **Coverage Reports**: Backend test coverage tracking

## Environment Variables

Production environment is managed via `/opt/sathyanishta/config/.env.prod` on the VM and copied to `.env` during deployment.
