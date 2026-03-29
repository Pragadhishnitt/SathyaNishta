# Sathya Nishta

🚀 **Intelligent Investigation Platform** - A comprehensive microservices architecture for AI-powered financial and compliance investigations.

[![CI Pipeline](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/ci.yml/badge.svg)](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/ci.yml)
[![Build Status](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/build-and-push.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [🏗️ Architecture Overview](#️-architecture-overview)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Environment Setup](#️-environment-setup)
- [🐳 Docker Development](#-docker-development)
- [🔧 Local Development](#-local-development)
- [🚢 CI/CD Pipeline](#-ci/cd-pipeline)
- [🌐 Deployment](#-deployment)
- [📊 Monitoring & Health](#-monitoring--health)
- [🧪 Testing](#-testing)
- [🔒 Security](#-security)
- [📚 API Documentation](#-api-documentation)
- [🤝 Contributing](#-contributing)
- [🐛 Troubleshooting](#-bug-troubleshooting)

---

## 🏗️ Architecture Overview

### **System Components**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   LLM Gateway   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Portkey)     │
│   Port: 3000    │    │   Port: 8000    │    │   Gemini 1.5    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Databases     │              │
         │              │   - Supabase    │              │
         │              │   - Neo4j       │              │
         │              │   - pgvector    │              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Traefik       │    │   AI Agents     │    │   Monitoring    │
│   (Gateway)     │    │   - Financial   │    │   - Health      │
│   Port: 8090    │    │   - Compliance  │    │   - Logs        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Technology Stack**
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11, LangGraph
- **AI/ML**: Gemini 1.5 Flash, Cohere, Portkey Gateway
- **Databases**: Supabase (PostgreSQL + pgvector), Neo4j
- **Infrastructure**: Docker, Docker Compose, Traefik
- **CI/CD**: GitHub Actions, Google Cloud Platform
- **Monitoring**: Health checks, logging, error tracking

---

## 🚀 Quick Start

### **Prerequisites**
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Git

### **1. Clone & Setup**
```bash
# Clone the repository
git clone https://github.com/Pragadhishnitt/SathyaNishta
cd SathyaNishta

# Copy environment template
cp .env.example .env

# Configure environment variables (see Environment Setup section)
nano .env
```

### **2. Start with Docker (Recommended)**
```bash
# Start all services
docker-compose up --build

# Access applications
# Frontend: http://localhost:8090
# API Docs: http://localhost:8000/docs
# Traefik Dashboard: http://localhost:8080
```

### **3. Verify Setup**
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:8090
```

---

## ⚙️ Environment Setup

### **Required Environment Variables**

#### **Core Application**
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Security
SECRET_KEY=your-32-character-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Frontend URL
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
```

#### **AI Services**
```bash
# Portkey Gateway (Primary)
PORTKEY_API_KEY=your-portkey-api-key
PORTKEY_CONFIG_ID=your-portkey-config-id

# Google Vertex AI
GOOGLE_API_KEY=your-google-api-key
GOOGLE_VERTEX_AI_API_KEY=your-vertex-ai-api-key

# Cohere (Alternative)
CO_API_KEY=your-cohere-api-key
COHERE_API_KEY=your-cohere-api-key

# Tavily (Web Search)
TAVILY_API_KEY=your-tavily-api-key
```

#### **External Services**
```bash
# Email (Optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# File Storage (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=your-s3-bucket

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

### **Environment File Template**
Copy `.env.example` and fill in your actual values:

```bash
# Production vs Development
NODE_ENV=development
DEBUG=true

# Database (Required for all environments)
DATABASE_URL=postgresql://...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...

# AI Services (Required)
PORTKEY_API_KEY=...
GOOGLE_API_KEY=...
```

---

## 🐳 Docker Development

### **Docker Compose Services**
```yaml
services:
  frontend:     # Next.js application
  backend:      # FastAPI application
  traefik:      # Reverse proxy & load balancer
  neo4j:        # Graph database
  postgres:     # Relational database (if not using Supabase)
  redis:        # Caching & session storage
```

### **Development Commands**
```bash
# Start all services
docker-compose up --build

# Start specific service
docker-compose up backend

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### **Docker Volumes**
- `./backend:/app` - Backend source code (development)
- `./frontend:/app` - Frontend source code (development)
- `neo4j_data:/data` - Neo4j database persistence
- `postgres_data:/var/lib/postgresql` - PostgreSQL persistence

---

## 🔧 Local Development

### **Backend Development**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run development server
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=app

# Code formatting
black .
isort .
flake8 .
```

### **Frontend Development**
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint

# Type checking
npx tsc --noEmit
```

### **Database Setup**
```bash
# Neo4j (if using local)
docker-compose up neo4j
# Access: http://localhost:7474 (neo4j/your-password)

# PostgreSQL (if using local)
docker-compose up postgres
# Connect: postgresql://postgres:password@localhost:5432/sathyanishta

# Run migrations
cd backend
alembic upgrade head
```

---

## 🚢 CI/CD Pipeline

### **Pipeline Overview**
```
Push to any branch → CI Pipeline (Tests, Security, Linting)
Merge to main → Build Docker Images → Deploy to Production
```

### **CI Pipeline** (All branches)
- **Backend Tests**: pytest with coverage
- **Frontend Tests**: Jest, ESLint, TypeScript
- **Security Scans**: Trivy, GitGuardian
- **Code Quality**: Black, isort, flake8
- **Docker Linting**: Hadolint checks

### **Build Pipeline** (main branch only)
- **Multi-platform Docker builds** (amd64, arm64)
- **Push to Google Artifact Registry**
- **Container security scanning**

### **Deploy Pipeline** (main branch only)
- **Deploy to GCP Compute Engine**
- **Health checks and smoke tests**
- **Automatic rollback on failure**

### **GitHub Secrets Required**
```bash
# GCP Configuration
GCP_PROJECT_ID=<your-gcp-project-id>
GCP_SA_KEY=<your-service-account-json-key>
GCP_REGION=<your-gcp-region>
GCP_ZONE=<your-gcp-zone>
VM_NAME=<your-vm-name>
STATIC_IP=<your-static-ip>

# Security
GITGUARDIAN_API_KEY=<your-gitguardian-api-key>

# AI Services
PORTKEY_API_KEY=<your-portkey-api-key>
PORTKEY_CONFIG_ID=<your-portkey-config-id>
```

---

## 📊 Monitoring & Health

### **Health Endpoints**
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database connectivity
curl http://localhost:8000/health/database

# External services
curl http://localhost:8000/health/external
```

### **Monitoring Tools**
- **Traefik Dashboard**: http://localhost:8080
- **Application Logs**: `docker-compose logs -f`
- **Neo4j Browser**: http://localhost:7474
- **Supabase Dashboard**: https://app.supabase.com

### **Performance Metrics**
- **Response Time**: API endpoint performance
- **Error Rates**: Failed requests and exceptions
- **Resource Usage**: CPU, memory, disk space
- **Database Performance**: Query optimization

---

## 🧪 Testing

### **Backend Testing**
```bash
cd backend

# Run all tests
pytest tests/ -v --cov=app

# Run specific test file
pytest tests/test_basic.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run integration tests
pytest tests/integration/ -v
```

### **Frontend Testing**
```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Type checking
npx tsc --noEmit
```

### **Test Categories**
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Full user journey testing
- **Security Tests**: Vulnerability scanning
- **Performance Tests**: Load and stress testing

---

## 🔒 Security

### **Security Features**
- **Authentication**: NextAuth.js with OAuth
- **Authorization**: Role-based access control
- **API Security**: Rate limiting, input validation
- **Secrets Management**: Environment variables, GitHub Secrets
- **Container Security**: Minimal base images, vulnerability scanning

### **Security Best Practices**
```bash
# Regular security updates
docker-compose pull
docker-compose up -d

# Scan for vulnerabilities
trivy image backend:latest
trivy image frontend:latest

# Check for exposed secrets
ggshield scan .

# Update dependencies
npm audit fix
pip install --upgrade
```

### **Security Headers**
- **CORS**: Cross-origin resource sharing
- **CSP**: Content security policy
- **HSTS**: HTTP strict transport security
- **X-Frame-Options**: Clickjacking protection

---

## 📚 API Documentation

### **API Endpoints**
```bash
# Interactive API docs
http://localhost:8000/docs

# OpenAPI specification
http://localhost:8000/openapi.json

# ReDoc documentation
http://localhost:8000/redoc
```

### **Key Endpoints**
```bash
# Authentication
POST /api/auth/login
POST /api/auth/logout
GET /api/auth/me

# Investigations
POST /api/investigate
GET /api/investigate/{id}
GET /api/investigate/history

# Financial Analysis
POST /api/financial/analyze
GET /api/financial/balance-sheet/{company}

# Compliance
POST /api/compliance/check
GET /api/compliance/report/{id}

# Health & Status
GET /health
GET /health/database
GET /health/external
```

### **API Usage Examples**
```bash
# Create investigation
curl -X POST http://localhost:8000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze financial statements for XYZ Corp", "type": "financial"}'

# Get investigation results
curl http://localhost:8000/api/investigate/12345

# Health check
curl http://localhost:8000/health
```

---

## 🤝 Contributing

### **Development Workflow**
1. **🍴 Fork** the repository
2. **🌿 Create** feature branch: `git checkout -b feature/amazing-feature`
3. **💻 Make** changes and test locally
4. **📝 Commit** changes: `git commit -m 'Add amazing feature'`
5. **📤 Push** to branch: `git push origin feature/amazing-feature`
6. **🔀 Create** Pull Request

### **Code Standards**
- **Python**: Black formatting, isort, flake8
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional commit messages
- **Tests**: Minimum 80% coverage
- **Documentation**: Update README and API docs

### **Pull Request Process**
1. **Tests pass** locally and in CI
2. **Code review** by team members
3. **Documentation** updated
4. **Merge** to main branch

---

## 🐛 Troubleshooting

### **Common Issues**

#### **Docker Issues**
```bash
# Container won't start
docker-compose logs <service-name>

# Port conflicts
docker-compose down
docker-compose up --force-recreate

# Volume issues
docker-compose down -v
docker volume prune
```

#### **Database Issues**
```bash
# Connection refused
# Check if database is running
docker-compose ps postgres
docker-compose ps neo4j

# Migration issues
cd backend
alembic current
alembic upgrade head
```

#### **Environment Issues**
```bash
# Missing environment variables
# Check .env file exists
cat .env

# Invalid API keys
# Test API connections
curl -H "Authorization: Bearer $API_KEY" https://api.example.com
```

#### **Frontend Issues**
```bash
# Build fails
# Clear cache
rm -rf .next
npm run build

# Module not found
# Check package.json dependencies
npm install
```

### **Getting Help**
- **Check logs**: `docker-compose logs -f`
- **Health checks**: `/health` endpoints
- **API docs**: `/docs` endpoint
- **GitHub Issues**: Report bugs and feature requests

### **Performance Issues**
```bash
# Check resource usage
docker stats

# Database performance
# Check slow queries
# Add indexes

# Frontend performance
# Use browser dev tools
# Optimize bundle size
```

---

## 📞 Support & Contact

### **Project Links**
- **🔗 Repository**: [Pragadhishnitt/SathyaNishta](https://github.com/Pragadhishnitt/SathyaNishta)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Next.js** - React framework for production
- **LangGraph** - Agent orchestration framework
- **Portkey** - AI gateway and observability
- **Supabase** - Backend-as-a-service platform
- **Neo4j** - Graph database technology

---

## 📈 Project Status

### **Current Version**: v0.2.0

### **Roadmap**
- [ ] Enhanced AI agent capabilities
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Multi-tenant support

### **Recent Updates**
- ✅ CI/CD pipeline implementation
- ✅ Security scanning integration
- ✅ Multi-platform Docker builds
- ✅ Automated deployment to production
- ✅ Comprehensive test coverage

---

**Built with ❤️ by the Sathya Nishta Team**
