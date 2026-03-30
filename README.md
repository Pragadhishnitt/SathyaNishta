# SathyaNishta

🚀 **Intelligent Financial Investigation Platform** — A multi-agent AI system for deep-dive equity research, compliance analysis, and fraud risk scoring for Indian retail and institutional investors.

[![CI Pipeline](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/ci.yml/badge.svg)](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/ci.yml)
[![Build Status](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/Pragadhishnitt/SathyaNishta/actions/workflows/build-and-push.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **PS6 · AI for Indian Investor · Category 3 · Extending MarketChatGPT**  
> Built by **Team Pink Gambit** · Powered by **Economic Times**

---
### 🌟 Live Deployment
**The application is currently live and accessible at:**
👉 **[http://34.100.219.13/](http://34.100.219.13/)**

*(Fully deployed via automated CI/CD pipeline on Google Cloud Platform using Docker)*

---

## 📋 Table of Contents

- [📚 Documentation](#-documentation)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [🤖 Agent System](#-agent-system)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Environment Setup](#️-environment-setup)
- [🐳 Docker Development](#-docker-development)
- [🔧 Local Development](#-local-development)
- [🚢 CI/CD Pipeline](#-cicd-pipeline)
- [🌐 Deployment](#-deployment)
- [📊 Monitoring & Health](#-monitoring--health)
- [🧪 Testing](#-testing)
- [🔒 Security](#-security)
- [📚 API Documentation](#-api-documentation-1)
- [🤝 Contributing](#-contributing)
- [🐛 Troubleshooting](#-troubleshooting)

---

## 📚 Documentation

For extensive technical documentation, see the [`docs/`](./docs/) folder:

| Document | Description |
|---|---|
| [`docs/SathyaNishta.pdf`](./docs/SathyaNishta.pdf) | **SathyaNishta: Complete Platform Guide** · Core Logic · System Integration · Full investigation walkthrough |
| [`docs/SathyaNishta_Low_Level.pdf`](./docs/SathyaNishta.pdf) | **Indepth low-level technical design** · system logic · agent specifications |
| [`docs/Impact_Model.pdf`](./docs/Impact_Model.pdf) | Business case · market opportunity · time saved · revenue model |
| [`docs/agent_workflows.pdf`](./docs/agent_workflows.pdf) | Detailed walkthrough of agentic graph orchestration and state management |
| [`docs/High_Level_Architecture.png`](./docs/High_Level_Architecture.png) | Visual overview of the system components and data flow |
| [`docs/Agent_Workflow.png`](./docs/Agent_Workflow.png) | Diagram of the 7-node LangGraph agentic pipeline |
| [`docs/Sequence_Diagram.png`](./docs/Sequence_Diagram.png) | Interaction sequence for a full investigation cycle |

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   LLM Gateway   │
│   (Next.js 14)  │◄──►│   (FastAPI)     │◄──►│   (Portkey)     │
│   Port: 3000    │    │   Port: 8000    │    │   Gemini 1.5    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │                       │
         ▼                      ▼                       │
┌─────────────────┐    ┌─────────────────┐             │
│   Traefik       │    │   LangGraph     │◄────────────┘
│   Port: 8090    │    │   Orchestrator  │
└─────────────────┘    └────────┬────────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
    ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
    │  Supabase       │ │   Neo4j     │ │   Storage    │
    │  PostgreSQL     │ │   Graph DB  │ │   Buckets    │
    │  + pgvector     │ │             │ │              │
    └─────────────────┘ └─────────────┘ └──────────────┘
```

**Request path:**
`Next.js` → `Traefik :8090` → `FastAPI :8000` → `LangGraph` → `Agents [1–5]` → `Reflection` → `Synthesis` → `Supabase`

### Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11, LangGraph |
| AI/ML | Gemini 1.5 Flash (primary), Cohere Command R+ (NLP/fallback) |
| LLM Gateway | Portkey — unified observability, cost tracking, fallback routing |
| Web Search | Tavily real-time search |
| Databases | Supabase (PostgreSQL + pgvector), Neo4j |
| Infrastructure | Docker, Docker Compose, Traefik |
| CI/CD | GitHub Actions, Google Cloud Platform |

---

## 🤖 Agent System

SathyaNishta uses a **7-node LangGraph pipeline** with deterministic routing. No LLM decides which agent runs next — `AGENT_SEQUENCE` is a fixed dict.

```
Supervisor → Financial → News → Compliance → Audio → Graph → Reflection → Synthesis
```

| Agent | Data source | Output |
|---|---|---|
| **Supervisor** | `investigations` | Routes agents, no analysis |
| **Financial** | `financial_filings` | Revenue trends, debt ratios, P&L |
| **News** | `news_articles` | Sentiment score (−1 to +1), reputation flags |
| **Compliance** | `compliance_records` | Violation severity, fines, regulatory risk |
| **Audio** | `audio_transcripts` | Management tone, forward guidance |
| **Graph** | Neo4j | Entity centrality, hidden connections |
| **Reflection** | All 5 outputs | Confidence scores, contradiction flags |
| **Synthesis** | Validated findings | `fraud_risk_score` + verdict |

**Verdict scale:** `critical` · `high` · `medium` · `low` · `safe`

**Time per investigation:** ~35 seconds (vs 8–12 hours manually) — **99.9% reduction**

> See [`docs/diagrams/agent_network.md`](./docs/diagrams/agent_network.md) for the visual agent network diagram.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### 1. Clone & Setup
```bash
git clone https://github.com/Pragadhishnitt/SathyaNishta
cd SathyaNishta
cp .env.example .env
nano .env
```

### 2. Start with Docker (Recommended)
```bash
docker-compose up --build

# Frontend:          http://localhost:8090
# API Docs:          http://localhost:8000/docs
# Traefik Dashboard: http://localhost:8080
```

### 3. Verify Setup
```bash
curl http://localhost:8000/health
curl http://localhost:8090
```

---

## ⚙️ Environment Setup

### Core Application
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key

NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

SECRET_KEY=your-32-character-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
```

### AI Services
```bash
PORTKEY_API_KEY=your-portkey-api-key
PORTKEY_CONFIG_ID=your-portkey-config-id

GOOGLE_API_KEY=your-google-api-key
GOOGLE_VERTEX_AI_API_KEY=your-vertex-ai-api-key

CO_API_KEY=your-cohere-api-key
COHERE_API_KEY=your-cohere-api-key

TAVILY_API_KEY=your-tavily-api-key
```

### Optional Services
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

---

## ⚠️ Known Deployment Limitations

### Google OAuth on IP Addresses
In the currently deployed version, Google OAuth sign-in will not work properly because Google's OAuth consent policies do not permit pure IP addresses (e.g., `http://34.100.219.13`) as authorized JavaScript origins or redirect URIs. To use Google Auth, the application must be mapped to a valid domain name (e.g., `sathyanishta.com`) with a proper SSL certificate.

### Disclaimer: Use of Mock / Synthesized Data
**Please Note:** *We have used simulated compliance flags, historical stock data snapshots, and mocked graphs at many instances to prove the system works. Not every finding reciprocates real-time authoritative data; the architecture is specifically designed to show that it works effectively with any kind of data input (live APIs, internal databases, or unstructured documents).*

AWS_BUCKET_NAME=your-s3-bucket

SENTRY_DSN=your-sentry-dsn
```

---

## 🐳 Docker Development

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

**Services:**
```yaml
services:
  frontend:   # Next.js application
  backend:    # FastAPI application
  traefik:    # Reverse proxy & load balancer
  neo4j:      # Graph database
  postgres:   # Relational database (if not using Supabase)
  redis:      # Caching & session storage
```

**Volumes:**
- `./backend:/app` — backend source (development)
- `./frontend:/app` — frontend source (development)
- `neo4j_data:/data` — Neo4j persistence
- `postgres_data:/var/lib/postgresql` — PostgreSQL persistence

---

## 🔧 Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-test.txt

uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

pytest tests/ -v --cov=app
black . && isort . && flake8 .
```

### Frontend
```bash
cd frontend
npm install
npm run dev
npm test
npm run build
npm run lint
npx tsc --noEmit
```

### Database Setup
```bash
# Neo4j
docker-compose up neo4j
# Access: http://localhost:7474

# PostgreSQL
docker-compose up postgres

# Run migrations
cd backend && alembic upgrade head
```

---

## 🚢 CI/CD Pipeline

```
Push to any branch  →  CI Pipeline (tests, security, linting)
Merge to main       →  Build Docker images → Deploy to GCP
```

**CI Pipeline** (all branches): pytest, Jest, ESLint, TypeScript, Trivy, GitGuardian, Black, isort, Hadolint

**Build Pipeline** (main only): Multi-platform Docker builds (amd64/arm64), push to Google Artifact Registry, container security scanning

**Deploy Pipeline** (main only): Deploy to GCP Compute Engine, health checks, automatic rollback on failure

### GitHub Secrets Required
```bash
GCP_PROJECT_ID, GCP_SA_KEY, GCP_REGION, GCP_ZONE
VM_NAME, STATIC_IP
GITGUARDIAN_API_KEY
PORTKEY_API_KEY, PORTKEY_CONFIG_ID
```

---

## 🌐 Live Deployment

The application is hosted on a Google Cloud Platform Compute Engine instance (`sathyanishta-1`). It is continuously deployed via GitHub Actions using the `docker-compose.prod.yml` orchestration, routed through Traefik.

- **Main Web Application:** [http://34.100.219.13/](http://34.100.219.13/)
- **FastAPI Backend (via Traefik):** `http://34.100.219.13/api/...`

*Note: Infrastructure modifications and port assignments automatically sync to this instance upon successful merges to the `main` branch.*

---

## 📊 Monitoring & Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/database
curl http://localhost:8000/health/external
```

- **Traefik Dashboard**: http://localhost:8080
- **Neo4j Browser**: http://localhost:7474
- **Supabase Dashboard**: https://app.supabase.com
- **Application Logs**: `docker-compose logs -f`

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest tests/ -v --cov=app
pytest tests/ --cov=app --cov-report=html
pytest tests/integration/ -v

# Frontend
cd frontend
npm test
npm run test:coverage
npm run test:e2e
```

**Test categories:** Unit · Integration · E2E · Security · Performance

---

## 🔒 Security

- **Authentication**: NextAuth.js with OAuth
- **Authorization**: Role-based (is_premium flag on users table)
- **API Security**: Rate limiting via Traefik, input validation
- **Container Security**: Minimal base images, Trivy scanning

```bash
trivy image backend:latest
trivy image frontend:latest
ggshield scan .
npm audit fix
```

---

## 📚 API Documentation

```bash
# Interactive docs
http://localhost:8000/docs

# OpenAPI spec
http://localhost:8000/openapi.json

# ReDoc
http://localhost:8000/redoc
```

### Key Endpoints
```bash
POST   /api/auth/login
GET    /api/auth/me

POST   /api/investigate                  # Start investigation
GET    /api/investigate/{id}             # Get result
GET    /api/investigate/history          # User history

POST   /api/financial/analyze
GET    /api/financial/balance-sheet/{company}

POST   /api/compliance/check
GET    /api/compliance/report/{id}

GET    /health
GET    /health/database
GET    /health/external
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test locally
4. Commit: `git commit -m 'feat: add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request

**Code standards:** Black + isort + flake8 (Python) · ESLint + Prettier (TypeScript) · Minimum 80% test coverage · Update `docs/` when adding agents or DB changes

---

## 🐛 Troubleshooting

```bash
# Container won't start
docker-compose logs <service-name>

# Port conflicts
docker-compose down && docker-compose up --force-recreate

# Volume issues
docker-compose down -v && docker volume prune

# Database connection refused
docker-compose ps postgres
docker-compose ps neo4j

# Migration issues
cd backend && alembic current && alembic upgrade head

# Frontend build fails
rm -rf .next && npm run build

# Check all resource usage
docker stats
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

[FastAPI](https://fastapi.tiangolo.com) · [Next.js](https://nextjs.org) · [LangGraph](https://langchain-ai.github.io/langgraph/) · [Portkey](https://portkey.ai) · [Supabase](https://supabase.com) · [Neo4j](https://neo4j.com)

---

## 📈 Project Status

**Current version:** v0.2.0

**Roadmap:**
- [ ] Enhanced AI agent capabilities
- [ ] Real-time collaboration features
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Multi-tenant support

**Recent updates:**
- ✅ Multi-agent investigation pipeline (5 agents + Reflection + Synthesis)
- ✅ CI/CD pipeline implementation
- ✅ Security scanning integration
- ✅ Multi-platform Docker builds
- ✅ Automated deployment to GCP

---

**Built with ❤️ by Team Pink Gambit**