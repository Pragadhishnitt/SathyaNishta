# Sathya Nishta

A Dockerized microservices architecture for intelligent investigation.

## 📁 Repository Structure & Ownership

| Path | Description | Owner |
|------|-------------|-------|
| **`/infra`** | Docker configs, Traefik, Neo4j setup | **Team A** |
| **`/orchestration`** | core workflow logic, supervisor, state management | **Team A** |
| **`/api`** | FastAPI backend service & routes | **Team A** |
| **`/agents`** | Domain-specific AI agents (Financial, Graph, etc.) | **Team B** |
| **`/frontend`** | Next.js User Interface | **Team B** |
| **`/contracts`** | Shared schemas, API specs, DB schemas | **Shared** |
| **`/shared`** | Shared utilities (logger, config, clients) | **Shared** |
| **`/scripts`** | Helper scripts for build & deployment | **Shared** |

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Supabase Account (or local postgres if configured)
- Neo4j AuraDB Account (or use local container)

### Setup
1. Copy `.env.example` to `.env` and fill in API keys.
   ```bash
   cp .env.example .env
   ```

2. Start the stack:
   ```bash
   docker-compose -f infra/docker-compose.yml up -d
   ```
   
3. Access services:
   - Frontend: `http://localhost`
   - API: `http://localhost/api/health`
   - Traefik Dashboard: `http://localhost:8080` (if enabled)

## 🛠 Team Responsibilities

### Team A
- **Infrastructure**: Maintain `infra/` folder, ensuring Docker builds are optimized and secure.
- **Orchestration**: Develop the central brain in `orchestration/`.
- **API Layer**: Manage `api/` routes and middleware.
- **Environment**: Keep `.env.example` up to date.

### Team B
- **Frontend**: Develop the UI in `frontend/` and ensure it connects correctly to the API.
- **Agents**: Implement specialized agent logic in `agents/` (Audio, Financial, Compliance, Graph).
- **Integration**: Ensure agents work correctly within the containerized environment.

## 📜 License
Proprietary
