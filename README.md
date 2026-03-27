# Sathya Nishta

A Dockerized microservices architecture for intelligent investigation.

## 📁 Repository Structure & Ownership

The project follows a monorepo structure with clear ownership boundaries.

| Path | Description | Owner |
|------|-------------|-------|
| **`/infra`** | Docker configs, Traefik, Neo4j setup | **Team A (Infra)** |
| **`/backend`** | Python Monolith (FastAPI + Orchestration) | **Team A (Backend)** |
| **`/backend/app/orchestration`** | Core workflow, LangGraph, Supervisor | **Team A** |
| **`/backend/app/api`** | FastAPI routes, Middleware | **Team A** |
| **`/backend/app/agents`** | Domain-specific AI agents | **Team B** |
| **`/backend/app/contracts`** | Shared Pydantic models & Specs | **Shared** |
| **`/frontend`** | Next.js User Interface | **Team B (Frontend)** |
| **`/scripts`** | Helper scripts for build & deployment | **Shared** |

## 🚀 Architecture

- **Orchestration**: Docker Compose
- **Gateway**: Traefik (Edge Proxy, Rate Limiting, SSL)
- **Backend**: FastAPI + LangGraph (Supervisor Architecture)
- **Frontend**: Next.js (App Router)
- **LLM Gateway**: Portkey (Cloud) -> Gemini 1.5 Flash
- **Database**:
    - **Relational**: Supabase (Cloud - PostgreSQL)
    - **Graph**: Neo4j AuraDB (Cloud) or Local Docker
    - **Vector**: pgvector (via Supabase)

## 🛠 Team Responsibilities

### Team A (Infrastructure & Core Backend)
1.  **Infrastructure**: Maintain `/infra` (Docker, Traefik, Neo4j).
2.  **Orchestration**: Implement LangGraph supervisor in `/backend/app/orchestration`.
3.  **API**: expose endpoints in `/backend/app/api`.
4.  **Database**: Manage Supabase migrations and Neo4j schema.

### Team B (Agents & Frontend)
1.  **Agents**: Implement domain logic in `/backend/app/agents` (Financial, Compliance, etc.).
2.  **Frontend**: Build the investigation UI in `/frontend`.
3.  **Integration**: Connect UI to API and ensure Agents return correct schemas.

## ⚡ Getting Started

1.  **Environment Setup**:
    ```bash
    cp .env.example .env
    # Fill in PORTKEY_API_KEY, SUPABASE_URL, NEO4J_URI, etc.
    ```

2.  **Run with Docker**:
    ```bash
    docker-compose -f infra/docker-compose.yml up --build
    ```

3.  **Access**:
    - Frontend: `http://127.0.0.1:3000`
    - API Docs: `http://127.0.0.1:8000/docs`
    - Traefik Dashboard: `http://127.0.0.1:8080`
