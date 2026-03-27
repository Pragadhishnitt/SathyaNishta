# Sathya Nishta — Team Sprint Plan
### ET AI Hackathon 2026 · PS #6 · Market ChatGPT Next Gen

---

## Product Context

**What we are building**: An extension to ET's existing Market ChatGPT that adds a **Sathyanishta Mode** — a deep fraud investigation tool, surfaced exactly the way Gemini surfaces Deep Research: as a toggleable chip on the input bar. Standard mode = Market ChatGPT as-is. Sathyanishta Mode = autonomous multi-agent fraud investigation with a full live evidence panel, fraud risk score, and downloadable report.

**PS #6 evaluation alignment**:

| Judging Axis | How We Hit It |
|---|---|
| Deeper data integration | Supabase (filings, financials), Neo4j (transaction graph), Gemini Audio (earnings calls), pgvector (SEBI regulation RAG) |
| Multi-step analysis | LangGraph Supervisor routes across 4 specialist agents with a Reflection gate before final synthesis |
| Portfolio-aware answers | Query parser extracts company, investigation type, and user intent — Supervisor builds a structured investigation plan per query |
| Source-cited responses | Every finding in the final report carries a `source` field (regulation ID, filing reference, graph cycle path); Reflection agent rejects unsourced claims |

---

## Team Structure

| Team | Owns | Members |
|---|---|---|
| **A — Core Platform** | Edge layer (Traefik), AI gateway (Portkey), LangGraph orchestration (Supervisor + Reflection), data layer (Supabase + Neo4j), Final Synthesis, Audit Trail, FastAPI + SSE API | A1 (Orchestration) · A2 (Infra & Data) |
| **B — Intelligence & Surface** | Financial Agent, Graph Agent, Audio Agent, Compliance Agent, Frontend (ET Market ChatGPT UI + Sathyanishta Mode panel + report view) | B1 (Agent lead) · B2 (Frontend lead) |

**Why this split holds**

```
Seam 1 — Platform vs Intelligence
  Team A owns the graph. It only cares that agents accept InvestigationState
  and return InvestigationState. It never touches agent internals.

Seam 2 — Backend vs Frontend
  Team B's frontend builds against a frozen OpenAPI spec + mock SSE stream
  defined in Sprint 0. Zero dependency on Team A's backend being live.
```

---

## Scope

### Must-Have → Sprints 1 & 2
- One complete investigation flow: Circular Trading Detection
- Supervisor orchestrates ≥ 3 agents with visible routing
- Fraud Risk Score (0–10, weighted, with source-cited evidence)
- ET Market ChatGPT UI with Sathyanishta Mode toggle (chip on input bar)
- Live agent activity panel via SSE streaming
- Demo video

### Nice-to-Have → Sprint 3
- Audio Agent (earnings call tone + deception markers via Gemini native audio)
- Reflection Agent (hallucination rejection, score adjustment)
- Compare Mode (parallel investigations, side-by-side scores)
- Semantic caching via Portkey (90%+ hit rate on repeated queries)

### Skip (Post-Hackathon)
- Kubernetes / production scaling
- User auth & payments
- Real BSE/NSE data APIs (use curated mock + seeded DB for demo)

---

## Sprint 0 — Contracts & Environment
**All 4 members · Synchronous · Before parallel work begins**

Sprint 0 produces the two frozen artifacts that let Teams A and B work in parallel with zero blocking: the `InvestigationState` contract and the OpenAPI + mock SSE spec. Neither team changes these after Sprint 0 without joint sign-off.

---

### All Members: Environment Bootstrap

```bash
git clone <repo> && cd sathya-nishta
cp .env.example .env

# Free-tier API keys required:
# GEMINI_API_KEY    → Google AI Studio (gemini-1.5-flash: 15 RPM, 1M tokens/day)
# PORTKEY_API_KEY   → portkey.ai (semantic cache layer over Gemini)
# SUPABASE_URL      → supabase.com (500MB DB, 2GB bandwidth/month)
# SUPABASE_KEY      → supabase.com
# NEO4J_URI         → neo4j.com AuraDB Free (50k nodes, 175k rels)
# NEO4J_PASSWORD    → neo4j.com

pip install -r requirements.txt   # fastapi, langgraph, langchain-google-genai,
                                  # neo4j, supabase, pandas, pymupdf, portkey-ai
npm install                       # next/vite, tailwind, lucide-react, recharts, d3
```

Monorepo structure agreed and committed before anyone writes code:

```
/
├── contracts/          ← frozen after Sprint 0, owned by both teams
│   ├── state.py        ← InvestigationState (Pydantic)
│   ├── state.ts        ← mirrored TypeScript types for frontend
│   └── openapi.yaml    ← API contract + SSE event schema
├── infra/              ← Team A
│   ├── docker-compose.yml
│   └── traefik/
├── orchestration/      ← Team A
│   ├── supervisor.py
│   ├── reflection.py
│   ├── synthesis.py
│   └── graph.py
├── agents/             ← Team B
│   ├── financial/
│   ├── graph/
│   ├── audio/
│   └── compliance/
└── frontend/           ← Team B
```

---

### A1 + A2: Freeze the InvestigationState Contract

```python
# contracts/state.py
from typing import TypedDict, List, Dict, Annotated, Literal
import operator

class AgentFinding(TypedDict):
    risk_score: float           # 0–10
    findings:   List[str]       # human-readable flags
    evidence:   Dict[str, str]  # { metric_name: value_with_source }

class InvestigationState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────
    investigation_id: str
    company_name:     str
    query:            str
    mode:             Literal["standard", "sathyanishta"]

    # ── Agent findings (Team B writes, Team A reads) ────────────────
    financial_findings:  AgentFinding
    graph_findings:      AgentFinding
    audio_findings:      AgentFinding
    compliance_findings: AgentFinding

    # ── Reflection gate (Team A writes, Team B reads for UI) ────────
    reflection_passed:   bool
    reflection_notes:    str

    # ── Orchestration (Team A owns) ─────────────────────────────────
    messages:            Annotated[List[str], operator.add]
    next_agent:          str
    iteration_count:     int
    investigation_complete: bool

    # ── Final output (Team A synthesizes, Team B renders) ───────────
    fraud_risk_score: float     # 0–10 weighted
    verdict:          str       # SAFE | CAUTION | HIGH_RISK | CRITICAL
    evidence:         List[Dict]
    audit_trail:      List[Dict]
```

---

### A1 + A2: Freeze the OpenAPI + SSE Contract

```yaml
# contracts/openapi.yaml

POST /api/investigate
  body:
    query:  string           # "Investigate Adani for circular trading"
    mode:   standard | sathyanishta
  response (202):
    investigation_id: uuid
    stream_url: /api/investigate/{id}/stream

GET /api/investigate/{id}/stream
  # Server-Sent Events — one event per agent transition
  events:
    agent_start:   { agent: string, timestamp: string }
    agent_update:  { agent: string, message: string }
    agent_done:    { agent: string, risk_score: float, findings: string[] }
    reflection:    { passed: bool, notes: string }
    synthesis:     { fraud_risk_score: float, verdict: string, evidence: object[] }
    complete:      { investigation_id: string }

GET /api/investigate/{id}
  response:
    investigation_id, company_name, fraud_risk_score, verdict,
    evidence, agent_log, audit_trail, created_at
```

---

### B2: Commit Mock SSE Stream for Immediate Frontend Development

```typescript
// contracts/mockStream.ts
// Team B2 imports this in Sprint 1 so the UI works without backend

export const MOCK_SSE_EVENTS = [
  { event: "agent_start",  data: { agent: "financial",  timestamp: "T+0s" } },
  { event: "agent_update", data: { agent: "financial",  message: "Parsing balance sheet Q3 2024..." } },
  { event: "agent_done",   data: { agent: "financial",  risk_score: 7.2,
      findings: ["Cash/EBITDA ratio 0.20 — flag: healthy range 0.6–0.8",
                 "Related party transactions 50% of revenue — SEBI LODR limit: 10%"] } },
  { event: "agent_start",  data: { agent: "graph",      timestamp: "T+8s" } },
  { event: "agent_update", data: { agent: "graph",      message: "Tracing circular transaction network in Neo4j..." } },
  { event: "agent_done",   data: { agent: "graph",      risk_score: 9.1,
      findings: ["3-node loop: Adani → Mauritius Shell A → Cayman Shell B → Adani",
                 "Total circular flow: ₹1,440 Cr in Q3 2024",
                 "Shared director on Adani + Shell A boards"] } },
  { event: "agent_start",  data: { agent: "compliance", timestamp: "T+14s" } },
  { event: "agent_done",   data: { agent: "compliance", risk_score: 8.0,
      findings: ["SEBI LODR Reg 23 breach — RPT 50% > 10% threshold",
                 "Companies Act §188 — circular transactions undisclosed"] } },
  { event: "reflection",   data: { passed: true, notes: "All findings cross-verified against source data" } },
  { event: "synthesis",    data: { fraud_risk_score: 8.7, verdict: "CRITICAL",
      evidence: [
        { source: "Financial", finding: "Cash/EBITDA 0.20", severity: "HIGH" },
        { source: "Graph",     finding: "3 circular loops, ₹1440 Cr", severity: "CRITICAL" },
        { source: "Compliance",finding: "SEBI LODR Reg 23 breach",   severity: "HIGH" }
      ] } },
  { event: "complete",     data: { investigation_id: "mock-001" } }
];
```

**Sprint 0 exits when:**
- ✅ All 4 members have local env running (`docker-compose up` succeeds)
- ✅ `contracts/state.py` + `contracts/openapi.yaml` committed and frozen
- ✅ Mock SSE stream committed (B2 unblocked)
- ✅ Monorepo structure agreed, Portkey account live, Supabase project live, Neo4j instance live

---

## Sprint 1 — Foundation
**Teams A and B work fully in parallel after Sprint 0**

### Team A — Sprint 1

#### A2: Infrastructure Skeleton

```yaml
# infra/docker-compose.yml
version: "3.9"
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports: ["80:80", "8080:8080"]
    volumes: ["/var/run/docker.sock:/var/run/docker.sock"]

  api:
    build: ./backend
    labels:
      - "traefik.http.routers.api.rule=PathPrefix(`/api`)"
      - "traefik.http.middlewares.ratelimit.ratelimit.average=100"  # 100 req/min
      - "traefik.http.middlewares.ratelimit.ratelimit.burst=20"
    environment:
      - PORTKEY_API_KEY=${PORTKEY_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - NEO4J_URI=${NEO4J_URI}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}

  frontend:
    build: ./frontend
    labels:
      - "traefik.http.routers.frontend.rule=PathPrefix(`/`)"
```

Portkey is cloud-only (no local sidecar). All Gemini calls route through Portkey's cloud endpoint with semantic cache enabled from day one.

```python
# backend/app/gateway/llm.py
from portkey_ai import Portkey
import os

portkey = Portkey(api_key=os.getenv("PORTKEY_API_KEY"))

def get_llm():
    """All agents call this. Portkey adds semantic cache + rate limit handling."""
    return portkey.chat.completions.with_options(
        provider="google",
        model="gemini-1.5-flash",
        cache={ "mode": "semantic", "max_age": 86400 }  # 24h — ~90% hit on repeated queries
    )

def llm_invoke(prompt: str) -> str:
    response = get_llm().create(messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content
```

**A2 Sprint 1 checkpoint**: `docker-compose up` brings up Traefik + API + frontend. Rate limiting at 100 req/min confirmed. Portkey routes to Gemini with cache on. Supabase tables migrated. Neo4j schema + mock data seeded.

---

#### A2: Supabase Migrations + Neo4j Seed

```sql
-- Supabase migrations

CREATE TABLE investigations (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name     TEXT NOT NULL,
    query            TEXT NOT NULL,
    mode             TEXT DEFAULT 'standard',
    status           TEXT DEFAULT 'running',
    fraud_risk_score DECIMAL(3,1),
    verdict          TEXT,
    created_at       TIMESTAMP DEFAULT NOW(),
    completed_at     TIMESTAMP,
    full_state       JSONB
);

CREATE TABLE agent_findings (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID REFERENCES investigations(id) ON DELETE CASCADE,
    agent_name       TEXT NOT NULL,
    risk_score       DECIMAL(3,1),
    findings         JSONB,
    evidence         JSONB,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_trail (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID REFERENCES investigations(id) ON DELETE CASCADE,
    timestamp        TIMESTAMP DEFAULT NOW(),
    actor            TEXT,    -- agent name | supervisor | reflection | synthesis
    action           TEXT,
    payload          JSONB
);

-- pgvector for Compliance Agent RAG (Team B Sprint 3)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE regulation_embeddings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    regulation  TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(768),
    source      TEXT          -- "SEBI_LODR" | "Companies_Act" | "IndAS"
);
```

```cypher
// Neo4j seed — 2 companies for demo

// Constraints
CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT person_din   IF NOT EXISTS FOR (p:Person)  REQUIRE p.din  IS UNIQUE;

// Company 1: Adani Green Energy — circular trading network
CREATE (adani:Company   { name: 'Adani Green Energy', cin: 'L40101GJ2015PLC082007', sector: 'Energy' })
CREATE (shell_a:Company { name: 'Mauritius Shell A',  cin: 'MU001', flag: 'shell', incorporated: '2023-06-15' })
CREATE (shell_b:Company { name: 'Cayman Shell B',     cin: 'CY002', flag: 'shell', incorporated: '2023-07-20' })

CREATE (adani)  -[:TRANSACTION { amount: 500, date: '2024-Q3', type: 'related_party' }]-> (shell_a)
CREATE (shell_a)-[:TRANSACTION { amount: 480, date: '2024-Q3', type: 'loan'          }]-> (shell_b)
CREATE (shell_b)-[:TRANSACTION { amount: 460, date: '2024-Q3', type: 'investment'    }]-> (adani)

CREATE (gautam:Person   { name: 'Gautam Adani', din: 'DIN00006273' })
CREATE (shared:Person   { name: 'Director X',   din: 'DIN00012345' })
CREATE (gautam)-[:DIRECTOR_OF]->(adani)
CREATE (shared)-[:DIRECTOR_OF]->(adani)
CREATE (shared)-[:DIRECTOR_OF]->(shell_a)    // shared director = red flag

// Company 2: Infosys — clean control case
CREATE (infy:Company   { name: 'Infosys', cin: 'L85110KA1981PLC013115', sector: 'IT' })
CREATE (nandan:Person  { name: 'Nandan Nilekani', din: 'DIN00041245' })
CREATE (nandan)-[:DIRECTOR_OF]->(infy)
// No circular transactions
```

---

#### A1: LangGraph Supervisor Skeleton

Build the full routing graph with placeholder agent nodes. Must be end-to-end runnable so Team A can test orchestration independently of Team B's agent logic.

```python
# orchestration/supervisor.py
from langgraph.graph import StateGraph, END
from contracts.state import InvestigationState
from app.gateway.llm import llm_invoke
import json

STANDARD_AGENTS    = ["financial", "graph", "compliance"]
SATHYANISHTA_AGENTS = ["financial", "graph", "compliance", "audio", "reflection"]

def supervisor_node(state: InvestigationState) -> InvestigationState:
    completed = [m for m in state.get("messages", []) if "Agent:" in m]
    agents    = SATHYANISHTA_AGENTS if state.get("mode") == "sathyanishta" else STANDARD_AGENTS

    prompt = f"""
    You are the fraud investigation supervisor for Sathya Nishta (ET Markets).

    Company:         {state['company_name']}
    Mode:            {state.get('mode', 'standard')}
    Query:           {state['query']}
    Completed steps: {json.dumps(completed)}
    Available agents: {agents}

    Routing rules:
    - Always run financial first.
    - Run graph after financial.
    - Run compliance after graph.
    - In sathyanishta mode: run audio after compliance, reflection last.
    - Once all required agents are done, return END.

    Respond ONLY in JSON (no markdown):
    {{"next_agent": "financial|graph|compliance|audio|reflection|END", "reasoning": "one sentence"}}
    """

    parsed = json.loads(llm_invoke(prompt))
    state["next_agent"]    = parsed["next_agent"]
    state["messages"]      = state.get("messages", []) + [
        f"Supervisor → {parsed['next_agent']}: {parsed['reasoning']}"
    ]
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def make_placeholder(name: str):
    def node(state: InvestigationState) -> InvestigationState:
        state["messages"] = state.get("messages", []) + [f"{name} Agent: placeholder"]
        return state
    node.__name__ = name
    return node


# Build graph
g = StateGraph(InvestigationState)
g.add_node("supervisor",  supervisor_node)
for agent in ["financial", "graph", "compliance", "audio", "reflection"]:
    g.add_node(agent, make_placeholder(agent))
g.add_node("synthesis", make_placeholder("synthesis"))

g.add_conditional_edges("supervisor", lambda s: s["next_agent"], {
    "financial":  "financial",
    "graph":      "graph",
    "compliance": "compliance",
    "audio":      "audio",
    "reflection": "reflection",
    "END":        "synthesis",
})
for agent in ["financial", "graph", "compliance", "audio", "reflection"]:
    g.add_edge(agent, "supervisor")
g.add_edge("synthesis", END)
g.set_entry_point("supervisor")

investigation_graph = g.compile()
```

#### A1 + A2: FastAPI with Mock SSE (enables B2 to connect immediately)

```python
# backend/app/routes/investigate.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio, json, uuid

router = APIRouter()

class InvestigationRequest(BaseModel):
    query: str
    mode:  str = "standard"

@router.post("/investigate", status_code=202)
async def start_investigation(req: InvestigationRequest):
    inv_id = str(uuid.uuid4())
    return { "investigation_id": inv_id,
             "stream_url": f"/api/investigate/{inv_id}/stream" }

@router.get("/investigate/{inv_id}/stream")
async def stream_investigation(inv_id: str):
    # Sprint 1: mock events so B2 can wire the UI against real SSE transport
    mock = [
        ("agent_start",  {"agent": "financial"}),
        ("agent_done",   {"agent": "financial",  "risk_score": 7.2, "findings": ["Cash/EBITDA 0.20"]}),
        ("agent_start",  {"agent": "graph"}),
        ("agent_done",   {"agent": "graph",       "risk_score": 9.1, "findings": ["3 circular loops"]}),
        ("agent_start",  {"agent": "compliance"}),
        ("agent_done",   {"agent": "compliance",  "risk_score": 8.0, "findings": ["SEBI breach"]}),
        ("synthesis",    {"fraud_risk_score": 8.7, "verdict": "CRITICAL", "evidence": []}),
        ("complete",     {"investigation_id": inv_id}),
    ]
    async def gen():
        for event, data in mock:
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(1.5)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})
```

**Team A Sprint 1 exits with:**
- ✅ `docker-compose up` works; Traefik, API, frontend all running
- ✅ Portkey routes to Gemini; cache confirmed active
- ✅ Supabase tables migrated; Neo4j seeded with Adani + Infosys
- ✅ LangGraph supervisor routes through placeholder agents end-to-end
- ✅ FastAPI running with mock SSE at `/api/investigate/{id}/stream`

---

### Team B — Sprint 1

#### B2: ET Market ChatGPT UI + Sathyanishta Mode

The UI is the face of the product. Build it fully in Sprint 1 against the mock SSE stream — no waiting on Team A's backend.

**Design principles**: Dark theme, sidebar nav, chat-first — identical visual grammar to ET Market ChatGPT. Sathyanishta Mode is a chip/button on the input bar, exactly like Gemini's Deep Research toggle. When active, it opens an investigation panel inline in the chat window.

```typescript
// frontend/src/App.tsx
import { useState } from "react";
import { SidebarNav }         from "./components/SidebarNav";
import { ChatInput }          from "./components/ChatInput";
import { ChatMessage }        from "./components/ChatMessage";
import { InvestigationPanel } from "./components/InvestigationPanel";

type Mode = "standard" | "sathyanishta";

export default function App() {
  const [mode, setMode]           = useState<Mode>("standard");
  const [messages, setMessages]   = useState<Message[]>([]);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [synthesis,  setSynthesis]    = useState<SynthesisResult | null>(null);
  const [isLoading,  setIsLoading]    = useState(false);

  const handleSubmit = async (query: string) => {
    setMessages(prev => [...prev, { role: "user", content: query }]);
    setAgentEvents([]);
    setSynthesis(null);
    setIsLoading(true);

    const res = await fetch("/api/investigate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, mode }),
    });
    const { stream_url } = await res.json();

    const es = new EventSource(stream_url);
    es.addEventListener("agent_start", e => {
      const d = JSON.parse(e.data);
      setAgentEvents(prev => [...prev, { ...d, status: "running" }]);
    });
    es.addEventListener("agent_done", e => {
      const d = JSON.parse(e.data);
      setAgentEvents(prev => prev.map(a =>
        a.agent === d.agent ? { ...a, ...d, status: "complete" } : a
      ));
    });
    es.addEventListener("synthesis", e => setSynthesis(JSON.parse(e.data)));
    es.addEventListener("complete",  () => { setIsLoading(false); es.close(); });
  };

  return (
    <div className="flex h-screen bg-[#0f0f0f] text-white">
      <SidebarNav />
      <main className="flex flex-col flex-1 overflow-hidden">

        {/* Top bar */}
        <header className="flex items-center gap-3 px-6 py-3 border-b border-white/10">
          <span className="font-semibold">Sathya Nishta</span>
          <span className="text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded-full">
            ET Markets · Market ChatGPT Next Gen
          </span>
        </header>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-6 py-8 max-w-3xl mx-auto w-full space-y-6">
          {messages.length === 0 && <WelcomeScreen mode={mode} />}
          {messages.map((m, i) => <ChatMessage key={i} message={m} />)}

          {/* Sathyanishta Mode — investigation panel appears inline */}
          {mode === "sathyanishta" && (agentEvents.length > 0 || synthesis) && (
            <InvestigationPanel
              agentEvents={agentEvents}
              synthesis={synthesis}
              isLoading={isLoading}
            />
          )}
        </div>

        <ChatInput
          mode={mode}
          onModeToggle={() => setMode(m => m === "standard" ? "sathyanishta" : "standard")}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
```

```typescript
// frontend/src/components/ChatInput.tsx
// Sathyanishta Mode chip lives here — same position as Gemini's Deep Research

export function ChatInput({ mode, onModeToggle, onSubmit, isLoading }) {
  const [text, setText] = useState("");

  const submit = () => { if (text.trim()) { onSubmit(text); setText(""); } };

  return (
    <div className="px-6 pb-6 max-w-3xl mx-auto w-full">
      <div className="rounded-2xl border border-white/10 bg-white/5 focus-within:border-white/25 transition-colors">

        {/* Mode toggle row */}
        <div className="flex items-center gap-2 px-4 pt-3">
          <button onClick={onModeToggle}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium
                        border transition-all ${
              mode === "sathyanishta"
                ? "bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/25"
                : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20 hover:text-white"
            }`}>
            <span>🔍</span>
            Sathyanishta Mode
          </button>
          {mode === "sathyanishta" && (
            <span className="text-xs text-indigo-400">
              Deep fraud investigation · 4 agents · Full report
            </span>
          )}
        </div>

        {/* Text input */}
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
          placeholder={
            mode === "sathyanishta"
              ? "Investigate [Company] for circular trading, RPT anomalies, SEBI violations..."
              : "Ask about stocks, markets, companies, technicals..."
          }
          className="w-full bg-transparent px-4 pt-2 pb-2 text-sm placeholder:text-gray-500
                     resize-none focus:outline-none"
          rows={2}
        />

        <div className="flex justify-end px-4 pb-3">
          <button onClick={submit} disabled={isLoading || !text.trim()}
            className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600
                       hover:bg-indigo-500 disabled:opacity-40 transition-colors">
            {isLoading
              ? "Investigating..."
              : mode === "sathyanishta" ? "Investigate →" : "Send →"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

```typescript
// frontend/src/components/InvestigationPanel.tsx
// The live deep-research panel — renders inside the chat window in Sathyanishta Mode

const AGENT_META: Record<string, { label: string; icon: string }> = {
  financial:  { label: "Financial Agent",  icon: "📊" },
  graph:      { label: "Graph Agent",      icon: "🔗" },
  compliance: { label: "Compliance Agent", icon: "⚖️" },
  audio:      { label: "Audio Agent",      icon: "🎤" },
  reflection: { label: "Reflection Agent", icon: "🔍" },
};

export function InvestigationPanel({ agentEvents, synthesis, isLoading }) {
  return (
    <div className="rounded-2xl border border-indigo-500/20 bg-indigo-950/20 p-6 space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
          Sathyanishta Mode · Fraud Investigation
        </span>
        {isLoading && (
          <span className="flex items-center gap-1.5 text-xs text-indigo-300 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
            Agents running...
          </span>
        )}
      </div>

      {/* Agent cards — one per agent, updates live */}
      <div className="space-y-2">
        {agentEvents.map(evt => {
          const meta = AGENT_META[evt.agent] ?? { label: evt.agent, icon: "🤖" };
          return (
            <div key={evt.agent}
              className={`flex items-start gap-3 p-3 rounded-xl border transition-all ${
                evt.status === "running"  ? "border-indigo-400/40 bg-indigo-900/20" :
                evt.status === "complete" ? "border-green-500/30  bg-green-950/20"  :
                                           "border-white/5       bg-white/2"
              }`}>
              <span className="text-lg">{meta.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium">{meta.label}</span>
                  {evt.status === "running"  && <span className="text-xs text-indigo-400">Investigating...</span>}
                  {evt.status === "complete" && <span className="text-xs text-green-400">✓ Done</span>}
                </div>
                {evt.findings?.map((f: string, i: number) => (
                  <p key={i} className="text-xs text-gray-400 mt-0.5">⚠ {f}</p>
                ))}
              </div>
              {evt.risk_score != null && (
                <span className={`text-sm font-bold shrink-0 ${
                  evt.risk_score >= 7 ? "text-red-400" :
                  evt.risk_score >= 4 ? "text-yellow-400" : "text-green-400"
                }`}>{evt.risk_score}/10</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Final fraud score card — appears after synthesis event */}
      {synthesis && <FraudScoreCard synthesis={synthesis} />}
    </div>
  );
}

function FraudScoreCard({ synthesis }) {
  const { fraud_risk_score: score, verdict, evidence } = synthesis;
  const color = score >= 8 ? "red" : score >= 6 ? "orange" : score >= 4 ? "yellow" : "green";
  const label = { CRITICAL: "Do NOT invest", HIGH_RISK: "High risk", CAUTION: "Caution", SAFE: "Low risk" };

  return (
    <div className={`rounded-xl p-5 border border-${color}-500/30 bg-${color}-950/20`}>
      <div className="flex items-end gap-4 mb-4">
        <span className={`text-7xl font-black text-${color}-400 leading-none`}>
          {score.toFixed(1)}
        </span>
        <div>
          <div className={`text-xl font-bold text-${color}-300`}>{verdict}</div>
          <div className="text-sm text-gray-400">{label[verdict as keyof typeof label]}</div>
        </div>
        <span className="ml-auto text-xs text-gray-500 self-end">/ 10</span>
      </div>

      {evidence?.length > 0 && (
        <div className="space-y-1.5 pt-3 border-t border-white/10">
          <p className="text-xs text-gray-500 font-medium mb-2">Source-cited evidence</p>
          {evidence.map((e: any, i: number) => (
            <div key={i} className="flex gap-2 text-xs text-gray-300">
              <span className="text-gray-500 shrink-0 w-20">{e.source}</span>
              <span>{e.finding}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

#### B1: All 4 Agent Skeletons

All 4 agents are contract-compliant and return valid mock `AgentFinding` output in Sprint 1. Real logic drops in Sprint 2 (Financial + Graph) and Sprint 3 (Audio + Compliance).

```python
# agents/financial/agent.py  — Sprint 1 skeleton
from contracts.state import InvestigationState, AgentFinding

def financial_agent_node(state: InvestigationState) -> InvestigationState:
    # Sprint 1: returns valid mock finding
    state["financial_findings"] = AgentFinding(
        risk_score=7.2,
        findings=["STUB: Cash/EBITDA anomaly detected", "STUB: RPT above threshold"],
        evidence={"cash_flow_ratio": "0.20 (source: mock)", "rpt_pct": "50% (source: mock)"}
    )
    state["messages"] = state.get("messages", []) + ["Financial Agent: stub complete"]
    return state

# Same pattern for graph, audio, compliance — each returns a valid AgentFinding stub
```

**Team B Sprint 1 exits with:**
- ✅ Full UI shell running at `127.0.0.1:3000`
- ✅ ET Market ChatGPT dark-theme layout: sidebar nav, chat window, input bar
- ✅ Sathyanishta Mode chip live — switches placeholder text, opens investigation panel
- ✅ SSE stream connects to mock backend; agent cards render live in sequence
- ✅ Fraud score card renders on synthesis event
- ✅ All 4 agent skeletons return valid contract-compliant mock output
- ✅ Frontend builds with no errors

---

**Sprint 1 Integration Check** (A1 + B1 together, end of Sprint 1):
Plug B1's agent skeletons into A1's LangGraph graph. Confirm state flows correctly through all nodes and synthesis exits cleanly. Fix any type mismatches against `contracts/state.py` before Sprint 2.

---

## Sprint 2 — Full Integration · Must-Have Complete
**Goal: Every Must-Have requirement done. Demo runnable by end of this sprint.**

---

### Team A — Sprint 2

#### A1: Real Synthesis Node

```python
# orchestration/synthesis.py
from contracts.state import InvestigationState
from app.db.audit import log_audit
import datetime

WEIGHTS = { "financial": 0.25, "graph": 0.40, "compliance": 0.25, "audio": 0.10 }

def synthesis_node(state: InvestigationState) -> InvestigationState:
    scores = {
        k: state.get(f"{k}_findings", {}).get("risk_score", 0) * w
        for k, w in WEIGHTS.items()
    }
    total = round(sum(scores.values()), 1)

    verdict = (
        "CRITICAL"  if total >= 8.0 else
        "HIGH_RISK" if total >= 6.0 else
        "CAUTION"   if total >= 4.0 else
        "SAFE"
    )

    evidence = []
    for source in ["financial", "graph", "compliance", "audio"]:
        for finding in state.get(f"{source}_findings", {}).get("findings", []):
            evidence.append({
                "source": source.capitalize(),
                "finding": finding,
                "severity": "CRITICAL" if total >= 8 else "HIGH" if total >= 6 else "MEDIUM"
            })

    state["fraud_risk_score"] = total
    state["verdict"]          = verdict
    state["evidence"]         = evidence
    state["investigation_complete"] = True

    log_audit(state["investigation_id"], actor="synthesis",
              action="final_score_generated",
              payload={"score": total, "verdict": verdict, "component_scores": scores})
    return state
```

#### A1: Replace Mock SSE with Live LangGraph Stream

```python
# backend/app/routes/investigate.py  (Sprint 2 — live)
from langgraph.graph import Graph
from orchestration.graph import investigation_graph
from app.db.supabase_client import save_investigation, update_investigation
import asyncio, json, uuid

QUEUES: dict[str, asyncio.Queue] = {}

def get_queue(inv_id: str) -> asyncio.Queue:
    if inv_id not in QUEUES:
        QUEUES[inv_id] = asyncio.Queue()
    return QUEUES[inv_id]

@router.post("/investigate", status_code=202)
async def start_investigation(req: InvestigationRequest):
    inv_id  = str(uuid.uuid4())
    company = extract_company_name(req.query)   # regex or LLM parse

    initial_state = {
        "investigation_id": inv_id,
        "company_name":     company,
        "query":            req.query,
        "mode":             req.mode,
        "messages":         [],
        "iteration_count":  0,
        "investigation_complete": False,
    }
    save_investigation({ "id": inv_id, "company_name": company,
                         "query": req.query, "mode": req.mode, "status": "running" })
    asyncio.create_task(run_graph(inv_id, initial_state))

    return { "investigation_id": inv_id,
             "stream_url": f"/api/investigate/{inv_id}/stream" }


async def run_graph(inv_id: str, state: dict):
    q = get_queue(inv_id)

    # LangGraph streams node-level updates
    async for event in investigation_graph.astream(state, stream_mode="updates"):
        node = list(event.keys())[0]
        data = list(event.values())[0]

        if node in ("financial", "graph", "compliance", "audio", "reflection"):
            findings = data.get(f"{node}_findings", {})
            await q.put({ "event": "agent_done",
                          "data":  { "agent": node,
                                     "risk_score": findings.get("risk_score"),
                                     "findings":   findings.get("findings", []) } })
        elif node == "synthesis":
            await q.put({ "event": "synthesis",
                          "data":  { "fraud_risk_score": data.get("fraud_risk_score"),
                                     "verdict":          data.get("verdict"),
                                     "evidence":         data.get("evidence", []) } })

    update_investigation(inv_id, { "status": "complete" })
    await q.put({ "event": "complete", "data": { "investigation_id": inv_id } })


@router.get("/investigate/{inv_id}/stream")
async def stream_investigation(inv_id: str):
    q = get_queue(inv_id)
    async def gen():
        while True:
            item = await q.get()
            yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"
            if item["event"] == "complete":
                break
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
```

#### A2: Compliance Agent

Pure rule-checking against known SEBI thresholds — no ML needed. A2 builds this one since it's close to the data layer.

```python
# agents/compliance/agent.py
from contracts.state import InvestigationState

SEBI_RULES = {
    "LODR_Reg_23": { "name": "SEBI LODR Regulation 23",   "rpt_threshold_pct": 10 },
    "CA_188":      { "name": "Companies Act Section 188",  "circular_tx": True    },
    "PFUTP_3":     { "name": "SEBI PFUTP Regulation 3",   "manipulation": True   },
}

def compliance_agent_node(state: InvestigationState) -> InvestigationState:
    financial  = state.get("financial_findings",  {})
    graph      = state.get("graph_findings",      {})
    violations = []
    score      = 0.0

    # Pull RPT % from financial evidence string
    rpt_str = financial.get("evidence", {}).get("rpt_pct", "0%").replace("%", "")
    rpt_pct = float(rpt_str) if rpt_str.replace(".", "").isdigit() else 0.0

    if rpt_pct > SEBI_RULES["LODR_Reg_23"]["rpt_threshold_pct"]:
        violations.append(
            f"{SEBI_RULES['LODR_Reg_23']['name']} — RPT {rpt_pct:.1f}% exceeds 10% threshold "
            f"(source: SEBI LODR 2015, Reg 23)"
        )
        score += 3.5

    if graph.get("cycle_count", 0) > 0 or any("loop" in f.lower() for f in graph.get("findings", [])):
        violations.append(
            f"{SEBI_RULES['CA_188']['name']} — circular transactions detected without disclosure "
            f"(source: Companies Act 2013, §188)"
        )
        score += 5.0

    if graph.get("fraud_likelihood") in ("HIGH", "CRITICAL"):
        violations.append(
            f"{SEBI_RULES['PFUTP_3']['name']} — potential market manipulation via circular trading "
            f"(source: SEBI PFUTP Regulations 2003, Reg 3)"
        )
        score += 3.0

    state["compliance_findings"] = {
        "risk_score": min(round(score, 1), 10),
        "findings":   violations,
        "evidence":   { "violation_count": str(len(violations)),
                        "highest_severity": "CRITICAL" if score >= 7 else "HIGH" }
    }
    state["messages"] = state.get("messages", []) + [
        f"Compliance Agent: {len(violations)} violations — score {min(score, 10):.1f}/10"
    ]
    return state
```

**Team A Sprint 2 exits with:**
- ✅ Full LangGraph: Supervisor → Financial → Graph → Compliance → Synthesis (all real)
- ✅ Live SSE stream emitting real agent events from LangGraph `astream`
- ✅ Compliance Agent running with source-cited findings
- ✅ Synthesis produces weighted fraud score + source-cited evidence list
- ✅ Supabase writes investigation + agent_findings + audit_trail per event
- ✅ `GET /api/investigate/{id}` returns full result

---

### Team B — Sprint 2

#### B1: Financial Agent — Real Logic

```python
# agents/financial/agent.py  (Sprint 2 — real)
from contracts.state import InvestigationState
from app.gateway.llm import llm_invoke
from app.db.supabase_client import fetch_financials
import json

def financial_agent_node(state: InvestigationState) -> InvestigationState:
    company = state["company_name"]

    # Pull from Supabase; fallback to curated mock
    fin = fetch_financials(company) or MOCK_FINANCIALS.get(company, MOCK_FINANCIALS["_default"])

    cash_flow_ratio = fin["cash_flow"] / fin["ebitda"] if fin["ebitda"] else 0
    rpt_pct         = (fin["rpt"] / fin["revenue"]) * 100 if fin["revenue"] else 0

    prompt = f"""
    You are a forensic accountant analyzing {company} for ET Markets' fraud detection system.

    Financial data:
    - Cash Flow / EBITDA: {cash_flow_ratio:.2f}  (healthy range: 0.6–0.8; source: balance sheet Q3 2024)
    - Related Party Transactions: {rpt_pct:.1f}% of revenue  (SEBI LODR limit: 10%; source: annual report)
    - Revenue CAGR (3yr): {fin.get('revenue_cagr', 'N/A')}%
    - Debt / Equity: {fin.get('debt_equity', 'N/A')}

    Detect fraud indicators. Each finding must cite its data source in parentheses.
    Respond ONLY in JSON (no markdown):
    {{
      "risk_score": <0-10>,
      "findings": ["<finding with (source)>"],
      "evidence": {{"cash_flow_ratio": "{cash_flow_ratio:.2f} (source: Q3 2024 BS)",
                   "rpt_pct": "{rpt_pct:.1f}% (source: Annual Report 2024)"}}
    }}
    """

    raw      = llm_invoke(prompt)
    findings = json.loads(raw)

    state["financial_findings"] = findings
    state["messages"] = state.get("messages", []) + [
        f"Financial Agent: {len(findings['findings'])} flags — score {findings['risk_score']}/10"
    ]
    return state


MOCK_FINANCIALS = {
    "Adani Green Energy": {
        "revenue": 1000, "ebitda": 200, "cash_flow": 40,
        "rpt": 500, "revenue_cagr": 5.0, "debt_equity": 8.2
    },
    "Infosys": {
        "revenue": 10000, "ebitda": 2500, "cash_flow": 2000,
        "rpt": 100, "revenue_cagr": 12.0, "debt_equity": 0.3
    },
    "_default": {
        "revenue": 500, "ebitda": 80, "cash_flow": 30,
        "rpt": 60, "revenue_cagr": 4.0, "debt_equity": 3.0
    }
}
```

---

#### B1: Graph Agent — Real Neo4j Queries

```python
# agents/graph/agent.py  (Sprint 2 — real)
from contracts.state import InvestigationState
from app.gateway.llm import llm_invoke
from neo4j import GraphDatabase
import json, os

driver = GraphDatabase.driver(os.getenv("NEO4J_URI"),
                              auth=("neo4j", os.getenv("NEO4J_PASSWORD")))

CYCLE_QUERY = """
MATCH path = (start:Company {name: $company})-[:TRANSACTION*2..4]->(start)
WITH path,
     [r IN relationships(path) | r.amount] AS amounts,
     [n IN nodes(path)         | n.name]   AS entities
RETURN entities, amounts,
       reduce(total=0, a IN amounts | total+a) AS total_flow
"""

SHARED_DIRECTOR_QUERY = """
MATCH (p:Person)-[:DIRECTOR_OF]->(c1:Company {name: $company})
MATCH (p)-[:DIRECTOR_OF]->(c2:Company)
WHERE c1 <> c2
RETURN p.name AS director, c2.name AS also_directs
"""

def graph_agent_node(state: InvestigationState) -> InvestigationState:
    company = state["company_name"]

    with driver.session() as s:
        cycles   = [dict(r) for r in s.run(CYCLE_QUERY,           company=company)]
        directors = [dict(r) for r in s.run(SHARED_DIRECTOR_QUERY, company=company)]

    findings_list = (
        [f"Circular loop: {' → '.join(c['entities'])} (₹{c['total_flow']} Cr; source: Neo4j graph)"
         for c in cycles]
        + [f"Shared director: {r['director']} also sits on {r['also_directs']} board (source: MCA data)"
           for r in directors]
    )

    prompt = f"""
    Analyze circular trading network for {company} (ET Markets investigation).

    Cycles found:    {json.dumps(cycles)}
    Shared directors: {json.dumps(directors)}

    Return ONLY JSON:
    {{
      "risk_score": <0-10>,
      "cycle_count": <int>,
      "fraud_likelihood": "LOW|MEDIUM|HIGH|CRITICAL",
      "findings": ["<finding with (source)>"]
    }}
    """

    parsed = json.loads(llm_invoke(prompt))
    parsed["findings"] = findings_list + parsed.get("findings", [])

    state["graph_findings"] = {
        "risk_score":       parsed["risk_score"],
        "cycle_count":      parsed.get("cycle_count", len(cycles)),
        "fraud_likelihood": parsed["fraud_likelihood"],
        "findings":         parsed["findings"],
        "evidence":         { "cycle_count": str(len(cycles)),
                              "shared_directors": str(len(directors)) }
    }
    state["messages"] = state.get("messages", []) + [
        f"Graph Agent: {len(cycles)} cycles — {parsed['fraud_likelihood']}"
    ]
    return state
```

---

#### B2: Connect UI to Live Backend

```typescript
// frontend/src/hooks/useInvestigation.ts
// Sprint 2: replaces mock stream with real SSE connection

export function useInvestigation() {
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [synthesis,   setSynthesis]   = useState<SynthesisResult | null>(null);
  const [isLoading,   setIsLoading]   = useState(false);

  const investigate = async (query: string, mode: string) => {
    setAgentEvents([]);
    setSynthesis(null);
    setIsLoading(true);

    const res = await fetch("/api/investigate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, mode }),
    });
    const { stream_url } = await res.json();

    const es = new EventSource(stream_url);
    es.addEventListener("agent_start", e =>
      setAgentEvents(prev => [...prev, { ...JSON.parse(e.data), status: "running" }])
    );
    es.addEventListener("agent_done", e => {
      const d = JSON.parse(e.data);
      setAgentEvents(prev => prev.map(a =>
        a.agent === d.agent ? { ...a, ...d, status: "complete" } : a
      ));
    });
    es.addEventListener("synthesis", e => setSynthesis(JSON.parse(e.data)));
    es.addEventListener("complete",  () => { setIsLoading(false); es.close(); });
    es.onerror = () => { setIsLoading(false); es.close(); };
  };

  return { investigate, agentEvents, synthesis, isLoading };
}
```

**Sprint 2 End-to-End Test** — run both before calling this sprint done:

```
Test 1 — Fraudulent (Adani Green Energy):
POST /api/investigate { "query": "Investigate Adani for circular trading", "mode": "sathyanishta" }
Expected:
  → Financial Agent: score ~7, RPT + cash flow flags
  → Graph Agent: 3 cycles, ₹1440 Cr, CRITICAL
  → Compliance Agent: 2 SEBI violations
  → Synthesis: 8.7/10 CRITICAL
  → UI: all agent cards complete + fraud score card renders

Test 2 — Clean (Infosys):
POST /api/investigate { "query": "Investigate Infosys", "mode": "sathyanishta" }
Expected:
  → Financial Agent: score ~1.5 (healthy ratios)
  → Graph Agent: 0 cycles
  → Compliance Agent: 0 violations
  → Synthesis: ~0.8/10 SAFE
```

**Sprint 2 exits when both tests pass and the UI shows live agent events for both.**

---

## Sprint 3 — Nice-to-Have + Demo

**Goal: All four Nice-to-Have features live. Demo video recorded and submitted.**

---

### Team A — Sprint 3

#### A1: Reflection Agent

```python
# orchestration/reflection.py
from contracts.state import InvestigationState
from app.gateway.llm import llm_invoke
from app.db.audit import log_audit
import json

def reflection_node(state: InvestigationState) -> InvestigationState:
    """
    Reviews all agent findings for internal contradictions, unsourced claims,
    and score inflation before Final Synthesis is allowed to run.
    """
    all_findings = {
        "financial":  state.get("financial_findings",  {}),
        "graph":      state.get("graph_findings",      {}),
        "compliance": state.get("compliance_findings", {}),
        "audio":      state.get("audio_findings",      {}),
    }

    prompt = f"""
    You are the senior audit reviewer for Sathya Nishta (ET Markets fraud investigation).

    Review all findings for {state['company_name']} and check for:
    1. Internal contradictions — e.g., "cash flow is low" vs "cash flow is healthy"
    2. Unsourced claims — each finding must cite a source in parentheses
    3. Score inflation — a 9/10 score based on a single weak signal must be adjusted

    Findings:
    {json.dumps(all_findings, indent=2)}

    Return ONLY JSON:
    {{
      "passed": true/false,
      "rejected_findings": ["<exact finding string to remove if any>"],
      "adjusted_score_delta": <float — e.g. -0.5 if score should drop>,
      "reflection_notes": "<one sentence summary>"
    }}
    """

    result = json.loads(llm_invoke(prompt))

    state["reflection_passed"] = result["passed"]
    state["reflection_notes"]  = result["reflection_notes"]

    if result["adjusted_score_delta"] != 0 and state.get("fraud_risk_score"):
        adj = max(0, min(10, state["fraud_risk_score"] + result["adjusted_score_delta"]))
        state["fraud_risk_score"] = round(adj, 1)

    state["messages"] = state.get("messages", []) + [
        f"Reflection Agent: {'✅ Passed' if result['passed'] else '⚠️ Adjusted'} — {result['reflection_notes']}"
    ]

    log_audit(state["investigation_id"], actor="reflection",
              action="findings_reviewed",
              payload={"passed": result["passed"], "delta": result["adjusted_score_delta"]})
    return state
```

Wire Reflection into the LangGraph graph so it fires after all agents complete (in Sathyanishta Mode only) before Synthesis:

```python
# orchestration/graph.py — Sprint 3 update
# Supervisor routes to "reflection" before "END" in sathyanishta mode
# Reflection → Supervisor → Supervisor sees all agents done + reflection done → END → Synthesis
```

#### A2: Portkey Semantic Cache Verification

```python
# Confirm cache is working — run in Sprint 3 before demo
# Should see ~90% hit rate after the first investigation of each company

import portkey_ai
client = portkey_ai.Portkey(api_key=os.getenv("PORTKEY_API_KEY"))

analytics = client.analytics.get()
print(f"Cache hit rate: {analytics.cache_hit_rate:.0%}")
# Target: >80% for repeated demo queries
```

---

### Team B — Sprint 3

#### B1: Audio Agent — Earnings Call Analysis

```python
# agents/audio/agent.py
from contracts.state import InvestigationState
from app.gateway.llm import llm_invoke
import json

# Sprint 3: curated mock transcripts — post-hackathon: pull from BSE/NSE
MOCK_TRANSCRIPTS = {
    "Adani Green Energy": """
        Q3 2024 Earnings Call:
        Analyst: "Can you clarify the ₹500 Cr transfer to the Mauritius entity?"
        CFO: "That's... a routine treasury operation. We'll provide more details offline."
        Analyst: "The cash conversion ratio is 0.20 — significantly below peers."
        CFO: "We're confident in our long-term fundamentals."
        Analyst: "Who are the beneficial owners of Shell A?"
        CFO: "That's commercially sensitive information at this stage."
    """,
    "Infosys": """
        Q3 2024 Earnings Call:
        CFO: "Revenue grew 12% YoY. Cash conversion is 80% of EBITDA."
        Analyst: "How are you deploying the ₹2,000 Cr cash?"
        CFO: "₹1,200 Cr returned to shareholders via dividends and buybacks."
        Analyst: "Any related party concerns?"
        CFO: "None. All RPTs are below 1% of revenue and fully disclosed."
    """
}

DECEPTION_MARKERS = [
    "deflects direct question", "uses filler language (um, uh)",
    "promises offline follow-up instead of answering",
    "refuses to name beneficial owners",
    "inconsistency between stated and financial performance"
]

def audio_agent_node(state: InvestigationState) -> InvestigationState:
    company    = state["company_name"]
    transcript = MOCK_TRANSCRIPTS.get(company, "No transcript available.")

    prompt = f"""
    Analyze this earnings call transcript for {company} as part of an ET Markets
    fraud investigation. Check for deception markers: {DECEPTION_MARKERS}

    Transcript:
    {transcript}

    Return ONLY JSON:
    {{
      "risk_score": <0-10>,
      "sentiment": "TRANSPARENT|NEUTRAL|EVASIVE|DECEPTIVE",
      "findings": ["<specific observation with (source: Q3 2024 earnings call)>"],
      "key_phrases": ["<suspicious phrase quoted from transcript>"]
    }}
    """

    parsed = json.loads(llm_invoke(prompt))
    state["audio_findings"] = {
        "risk_score": parsed["risk_score"],
        "findings":   parsed["findings"],
        "evidence":   { "sentiment": parsed["sentiment"],
                        "marker_count": str(len(parsed.get("key_phrases", []))) }
    }
    state["messages"] = state.get("messages", []) + [
        f"Audio Agent: {parsed['sentiment']} — score {parsed['risk_score']}/10"
    ]
    return state
```

---

#### B1: Compare Mode

```python
# backend/app/routes/compare.py
from fastapi import APIRouter
from pydantic import BaseModel
import asyncio

router = APIRouter()

class CompareRequest(BaseModel):
    company_a: str
    company_b: str

@router.post("/compare")
async def compare_companies(req: CompareRequest):
    """Runs two Sathyanishta investigations in parallel."""
    result_a, result_b = await asyncio.gather(
        run_single_investigation(req.company_a, mode="sathyanishta"),
        run_single_investigation(req.company_b, mode="sathyanishta"),
    )
    safer = req.company_b if result_b["fraud_risk_score"] < result_a["fraud_risk_score"] else req.company_a
    return {
        "company_a":   { "name": req.company_a, **result_a },
        "company_b":   { "name": req.company_b, **result_b },
        "safer_choice": safer,
        "score_gap":   abs(result_a["fraud_risk_score"] - result_b["fraud_risk_score"])
    }
```

```typescript
// frontend/src/components/ComparePanel.tsx
export function ComparePanel({ resultA, resultB }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FraudScoreCard synthesis={resultA} company={resultA.name} />
        <FraudScoreCard synthesis={resultB} company={resultB.name} />
      </div>
      <div className="text-center text-sm text-gray-400 pt-2 border-t border-white/10">
        Safer investment:
        <span className="text-white font-semibold ml-1">
          {resultA.fraud_risk_score < resultB.fraud_risk_score ? resultA.name : resultB.name}
        </span>
        <span className="text-gray-500 ml-2">
          (score gap: {Math.abs(resultA.fraud_risk_score - resultB.fraud_risk_score).toFixed(1)} pts)
        </span>
      </div>
    </div>
  );
}
```

---

#### B2: Report Download + Final Polish

```typescript
// frontend/src/components/ReportDownload.tsx
export function ReportDownload({ investigation }) {
  const download = () => {
    const report = {
      title:         `Sathya Nishta Investigation — ${investigation.company_name}`,
      generated_by:  "ET Markets · Sathyanishta Mode",
      date:          new Date().toLocaleDateString("en-IN"),
      fraud_score:   investigation.fraud_risk_score,
      verdict:       investigation.verdict,
      source_evidence: investigation.evidence,
      audit_trail:   investigation.audit_trail,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const a    = Object.assign(document.createElement("a"), {
      href:     URL.createObjectURL(blob),
      download: `sathyanishta_${investigation.company_name.replace(/\s+/g, "_")}.json`,
    });
    a.click();
  };

  return (
    <button onClick={download}
      className="flex items-center gap-2 px-4 py-2 text-xs border border-white/10
                 rounded-lg hover:bg-white/5 text-gray-300 transition-colors">
      ↓ Download Full Report
    </button>
  );
}
```

---

### Sprint 3: Demo Video Script

```
[0:00–0:12]  Hook
  Screen: ET Market ChatGPT
  VO: "India has 14 crore demat account holders.
       Most are flying blind. ET Markets has the data.
       We built the intelligence layer."

[0:12–0:32]  Standard Mode — the baseline
  Type: "Tell me about Adani Green Energy"
  Response: Standard market summary (price, sector, revenue)
  VO: "Market ChatGPT gives you information.
       Information isn't investigation."

[0:32–1:40]  Sathyanishta Mode — the upgrade
  Click the Sathyanishta Mode chip (like Gemini Deep Research)
  Input: "Investigate Adani for circular trading"
  Hit Investigate →

  Live agent panel fires:
    📊 Financial Agent  — Cash/EBITDA 0.20, RPT 50% of revenue
    🔗 Graph Agent      — 3-node circular loop, ₹1440 Cr, shared directors
    ⚖️ Compliance Agent — SEBI LODR Reg 23 + Companies Act §188 breached
    🎤 Audio Agent      — CFO evasive on beneficial owners, 3 deception markers
    🔍 Reflection Agent — ✅ All findings source-cited and cross-verified

  Final score: 8.7 / 10  ·  CRITICAL — Do NOT invest
  Source-cited evidence list visible below score

[1:40–2:00]  Compare Mode
  "Compare Adani vs Infosys"
  Side-by-side: 8.7 (CRITICAL) vs 0.8 (SAFE)
  VO: "Protect your portfolio in under 2 minutes."

[2:00–2:20]  Positioning
  VO: "We didn't add a feature to Market ChatGPT.
       We rebuilt it with autonomous fraud intelligence.
       Deeper data. Multi-step analysis. Source-cited answers."

[2:20–2:30]  Impact
  ₹99/month vs ₹5,00,000 traditional audit
  2 minutes vs weeks of manual research
  "Sathya Nishta. Market ChatGPT, upgraded."
```

**Sprint 3 exits with:**
- ✅ Audio Agent live (earnings call tone + deception markers)
- ✅ Reflection Agent live in Sathyanishta Mode (findings validated, score adjusted)
- ✅ Compare Mode live (side-by-side fraud scores)
- ✅ Semantic cache confirmed >80% hit rate on repeated queries
- ✅ Report download from investigation panel
- ✅ Demo video recorded, uploaded (YouTube unlisted)
- ✅ README complete with architecture diagram, setup instructions, impact model
- ✅ GitHub repo public with clean commit history

---

## Final Submission Checklist

```
Technical
✅ docker-compose up works on a clean clone (test before submitting)
✅ .env.example documents all required keys with instructions
✅ API returns results in <2 minutes for a full sathyanishta investigation
✅ Frontend deployed and publicly accessible (Vercel)
✅ Backend deployed (Railway free tier)

Hackathon Deliverables
✅ GitHub repo — public, clean history, README with setup + architecture
✅ 3-minute pitch video — problem → demo → impact (YouTube unlisted)
✅ Architecture document — agent roles, LangGraph flow, error handling, DB design
✅ Impact model — time (2 min vs weeks), cost (₹99 vs ₹5L), accuracy assumption

PS #6 Alignment (explicitly call out in README)
✅ "Market ChatGPT Next Gen" — extend, not replace; Sathyanishta Mode as a tool
✅ Deeper data integration — Supabase, Neo4j, pgvector, Gemini Audio
✅ Multi-step analysis — LangGraph Supervisor → 4 agents → Reflection → Synthesis
✅ Portfolio-aware answers — investigation plan built per query intent
✅ Source-cited responses — every finding carries (source: ...) provenance
```

---

## Risk Register

| Risk | Mitigation |
|---|---|
| LangGraph astream too complex for deadline | Fall back to synchronous `.invoke()` + polling `GET /investigate/{id}` every 2s |
| Neo4j seed too slow | Use JSON fixture files; same UI visualization, no database |
| Gemini rate limits hit during demo | Portkey semantic cache absorbs 90%+ hits; run max 1 live investigation at a time |
| SSE not supported by hosting tier | Switch to polling endpoint — UI already has the hook |
| Audio agent too slow for demo | Pre-compute transcript findings; store in Supabase; return as instant result |
| Reflection causes infinite retry loop | Hard cap: `iteration_count > 8` → skip reflection and proceed to synthesis |
