# Sathya Nishta — Contracts Package

**Version:** 1.0.0  
**Status:** FROZEN after Sprint 1  
**Last Updated:** 2024-02-04

---

## What Are Contracts?

Contracts are the **interface boundary** between Team A (Platform) and Team B (Intelligence + Surface). They define:

- Data structures (schemas, types)
- API endpoints and their behavior
- Database tables and relationships
- Agent tool signatures

Once frozen (end of Sprint 1), these files can **only be modified with approval from both team leads**. This prevents breaking changes and ensures parallel development works smoothly.

---

## Contract Files Overview

| File | Owner | Purpose | Used By |
|------|-------|---------|---------|
| `backend_schemas.py` | Team A | All Pydantic models for backend | Orchestration, API, Agents |
| `frontend_types.ts` | Team B | All TypeScript types for frontend | React components, API client |
| `frontend_api_client.ts` | Team B | Frontend HTTP client implementation | React hooks, API calls |
| `api_spec.yaml` | Team A | OpenAPI REST API specification | API docs, client generation |
| `database_schema.sql` | Team A | PostgreSQL + Neo4j schema definitions | Migrations, ORM setup |
| `agent_tools.md` | Team B | Agent tool function signatures | Agent implementations |
| `README.md` (this file) | Both | Documentation and rules | Onboarding, reference |

---

## File Details

### 1. `backend_schemas.py`

**Owner:** Team A  
**Language:** Python (Pydantic)

Defines all data models used in the backend:

- **API models:** `InvestigationRequest`, `InvestigationResponse`, `InvestigationReport`
- **Agent models:** `AgentTask`, `AgentOutput`, `Finding`
- **Orchestration models:** `InvestigationPlan`, `InvestigationState`
- **Reflection models:** `ReflectionVerdict`, `ReflectionFeedback`
- **Enums:** `InvestigationStatus`, `AgentType`, `AgentStatus`, `Severity`, `Verdict`
- **SSE events:** `SSEEvent`

**Usage:**
```python
from contracts.schemas import InvestigationRequest, AgentTask, Finding

request = InvestigationRequest(
    query="Investigate Adani for circular trading",
    context={"period": "Q3-2024"}
)
```

**Import in:**
- `orchestration/supervisor.py`
- `orchestration/reflection.py`
- `api/routes/investigate.py`
- `agents/*/agent.py`

---

### 2. `frontend_types.ts`

**Owner:** Team B  
**Language:** TypeScript

Mirrors `backend_schemas.py` for the frontend:

- All the same models, but in TypeScript
- Additional UI-specific types: `AgentCardState`, `InvestigationProgress`
- Helper functions: `getVerdictColor()`, `formatFraudScore()`
- Type guards: `isAgentEvent()`, `isInvestigationCompleteEvent()`

**Usage:**
```typescript
import { InvestigationReport, Verdict } from './types';

function displayReport(report: InvestigationReport) {
  const color = getVerdictColor(report.verdict);
  // ...
}
```

**Import in:**
- `frontend/src/components/*.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/app/investigate/[id]/page.tsx`

---

### 3. `frontend_api_client.ts`

**Owner:** Team B  
**Language:** TypeScript

Production-ready HTTP client for talking to the backend API:

- `startInvestigation()` → POST `/api/v1/investigate`
- `getReport()` → GET `/api/v1/investigate/:id`
- `createEventSource()` → SSE connection helper
- `startInvestigationWithStream()` → Combined start + stream
- Full error handling (429 rate limit, 401 auth, network errors)

**Usage:**
```typescript
import { apiClient } from './api';

const response = await apiClient.startInvestigation({
  query: "Investigate company X"
});

const eventSource = apiClient.createEventSource(response.investigation_id, {
  onAgentStarted: (data) => console.log("Agent started:", data.agent),
  onInvestigationComplete: (data) => console.log("Done:", data.fraud_risk_score)
});
```

**Import in:**
- `frontend/src/app/page.tsx` (dashboard)
- `frontend/src/app/investigate/[id]/page.tsx` (report view)

---

### 4. `api_spec.yaml`

**Owner:** Team A  
**Format:** OpenAPI 3.0.3

Full REST API specification with:

- All endpoints (`/health`, `/api/v1/investigate`, `/api/v1/investigate/:id`, `/api/v1/investigate/:id/stream`)
- Request/response schemas
- Error codes
- Authentication (API key)
- Rate limiting rules
- SSE event formats
- Example requests/responses

**Usage:**

1. **Generate API docs:**
   ```bash
   npx @redocly/cli build-docs api_spec.yaml -o docs/api.html
   ```

2. **Generate TypeScript client (auto):**
   ```bash
   npx openapi-typescript api_spec.yaml -o frontend/src/lib/api-types.ts
   ```

3. **Validate backend matches spec:**
   ```bash
   python scripts/validate_api_spec.py
   ```

**View online:** Paste into [Swagger Editor](https://editor.swagger.io/)

---

### 5. `database_schema.sql`

**Owner:** Team A  
**Format:** PostgreSQL SQL

Complete database schema for Supabase:

**Tables:**
- `investigations` — investigation lifecycle tracking
- `investigation_states` — agent checkpoints
- `audit_trail` — append-only audit log (RLS enforced)
- `regulatory_docs` — SEBI/IndAS documents (with pgvector embeddings)
- `financial_filings` — company balance sheets, cash flows (with embeddings)
- `audio_files` — earnings call metadata and storage keys

**Features:**
- pgvector indexes for semantic search
- Auto-updating `updated_at` triggers
- Helper functions: `get_approved_states()`, `check_state_barrier()`
- Append-only audit trail enforcement

**Neo4j schema (documented, not executable):**
- Node labels: `Company`, `Person`, `ShellEntity`, `BankAccount`
- Relationships: `DIRECTOR_OF`, `OWNS`, `TRANSACTS_WITH`, `RELATED_TO`
- Constraints and indexes

**Usage:**

Apply to Supabase:
```bash
# Local
psql -U postgres -d sathya_nishta -f database_schema.sql

# Cloud
supabase db push
```

Apply to Neo4j:
```bash
# Extract Cypher comments into separate file first
cypher-shell -u neo4j -p password -f neo4j_schema.cypher
```

---

### 6. `agent_tools.md`

**Owner:** Team B  
**Format:** Markdown (with Python signatures)

Specification of all tools that agents must implement:

**Financial Agent:**
- `analyze_balance_sheet()`
- `calculate_financial_ratios()`
- `detect_cash_flow_divergence()`
- `detect_related_party_transactions()`

**Graph Agent:**
- `generate_cypher_query()`
- `run_cypher_query()`
- `detect_circular_loops()`

**Audio Agent:**
- `load_audio_file()`
- `analyze_audio_tone()`
- `detect_deception_markers()`

**Compliance Agent:**
- `check_sebi_regulations()`
- `verify_indas_compliance()`
- `rag_legal_query()`

Each tool has:
- Exact input/output schema
- Type hints
- Example data
- Implementation checklist

**Usage:**

Team B implements these in `agents/*/tools.py`:
```python
# agents/financial/tools.py
def detect_cash_flow_divergence(params: dict) -> dict:
    """Implementation of the contract"""
    company_ticker = params["company_ticker"]
    period = params["period"]
    # ... fetch data, analyze, return dict matching contract
    return {
        "ebitda": 1200000000000,
        "ebitda_growth_percent": 15.5,
        "divergence_detected": True,
        # ... rest of fields
    }
```

---

## Contract Modification Rules

### ✅ Allowed Changes (No Approval Needed)

- Adding **optional** fields to existing models
- Adding new **helper functions** (e.g., new type guards in `types.ts`)
- Adding new **documentation** or examples
- Fixing **typos** or clarifying comments
- Adding new **tools** to agents (if not breaking existing calls)

### ❌ Breaking Changes (Requires Both Teams' Approval)

- Removing or renaming fields
- Changing field types (e.g., `float` → `int`)
- Changing required/optional status of fields
- Removing or renaming enums
- Changing API endpoint URLs
- Changing database table names or column types
- Removing or renaming agent tools

**Process for breaking changes:**
1. Open GitHub issue with `breaking-change` label
2. Both Team A and Team B leads must approve
3. Create new version (e.g., `contracts_v2/`)
4. Deprecate old version with migration timeline

---

## Validation & Testing

### Backend Schema Validation

```python
# scripts/validate_contracts.py
from contracts.schemas import InvestigationRequest
from pydantic import ValidationError

try:
    InvestigationRequest(query="Test", context={})
    print("✅ Schemas valid")
except ValidationError as e:
    print("❌ Schema error:", e)
```

### Frontend Type Checking

```bash
cd frontend
npm run type-check
```

### API Spec Validation

```bash
npx @redocly/cli lint api_spec.yaml
```

### Database Schema Check

```bash
# Check if current DB matches schema
python scripts/check_db_schema.py
```

---

## Sprint 1 Deliverable: Frozen Contracts

By **end of Sprint 1**, these files must be:

- [ ] Reviewed by both Team A and Team B leads
- [ ] All examples tested (request/response round-trips work)
- [ ] API spec validated with linter
- [ ] Database schema applied to test Supabase instance
- [ ] Committed to `main` branch with tag `v1.0.0-contracts-frozen`
- [ ] Documented in team wiki with "DO NOT MODIFY" warning

Once frozen, Sprints 2-5 proceed in parallel with zero cross-team blocking.

---

## Version History

| Version | Date | Changes | Approved By |
|---------|------|---------|-------------|
| 1.0.0 | 2024-02-04 | Initial contract definition | Team A Lead, Team B Lead |

---

## Questions?

**Team A (Platform):** Contact Team A lead for questions about:
- Backend schemas
- API spec
- Database schema

**Team B (Intelligence + Surface):** Contact Team B lead for questions about:
- Frontend types
- API client
- Agent tools

**Both Teams:** Contract modification proposals go through GitHub issues with `contracts` label.
