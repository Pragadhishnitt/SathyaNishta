"""LangGraph node functions — bridge between class-based agents and the graph.

Each node instantiates its real agent, runs the appropriate tools,
and transforms the output into an AgentFinding for the graph state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure the repo root is on sys.path so `contracts.state` resolves
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.state import AgentFinding, InvestigationState
from app.shared.logger import setup_logger
from app.shared.llm_portkey import chat_complete

_logger = setup_logger("agent_nodes")


# ── Helper: safe AgentFinding builder ───────────────────────────

def _build_finding(risk_score: float, findings: List[str], evidence: Dict[str, str]) -> AgentFinding:
    """Clamp risk_score to [0, 10] and return a valid AgentFinding."""
    return AgentFinding(
        risk_score=max(0.0, min(10.0, round(risk_score, 1))),
        findings=findings or ["No findings"],
        evidence=evidence or {},
    )


# ── Financial Agent Node ────────────────────────────────────────

def financial_node(state: InvestigationState) -> Dict[str, Any]:
    """Run real FinancialAgent — queries Supabase financial_filings + LLM analysis."""
    company = state.get("company_name", "Unknown")
    _logger.info(f"Financial Agent: starting analysis for {company}")

    try:
        from app.agents.financial.financial_agent import FinancialAgent
        agent = FinancialAgent()

        all_findings: List[str] = []
        all_anomalies: List[str] = []
        evidence: Dict[str, str] = {}
        health_scores: List[float] = []

        # Run all 4 financial tools
        tools = [
            ("analyze_balance_sheet", "Balance Sheet"),
            ("calculate_financial_ratios", "Financial Ratios"),
            ("detect_cash_flow_divergence", "Cash Flow"),
            ("detect_related_party_transactions", "Related Party Transactions"),
        ]

        for tool_name, label in tools:
            try:
                result = agent.process({
                    "tool": tool_name,
                    "params": {"company_name": company},
                })
                summary = result.get("summary", "")
                if summary:
                    all_findings.append(f"[{label}] {summary[:200]}")
                for anomaly in result.get("anomalies", []):
                    all_anomalies.append(f"[{label}] {anomaly}")
                health = result.get("health_indicator", "unknown")
                health_map = {"healthy": 2.0, "warning": 6.0, "critical": 9.0, "unknown": 5.0}
                health_scores.append(health_map.get(health, 5.0))
                evidence[f"{tool_name}_health"] = health
            except Exception as e:
                _logger.warning(f"Financial tool {tool_name} failed: {e}")
                all_findings.append(f"[{label}] Analysis unavailable: {str(e)[:80]}")

        risk_score = sum(health_scores) / len(health_scores) if health_scores else 5.0
        combined_findings = all_findings + all_anomalies

        finding = _build_finding(risk_score, combined_findings[:10], evidence)

    except Exception as e:
        _logger.error(f"Financial Agent failed: {e}")
        finding = _build_finding(5.0, [f"Financial analysis error: {str(e)[:100]}"], {})

    return {
        "financial_findings": finding,
        "messages": [f"Financial Agent: {len(finding['findings'])} findings — score {finding['risk_score']}/10"],
    }


# ── Graph Agent Node ───────────────────────────────────────────

def graph_node(state: InvestigationState) -> Dict[str, Any]:
    """Run real GraphAgent — queries Neo4j and returns graph payload for frontend."""
    company = state.get("company_name", "Unknown")
    _logger.info(f"Graph Agent: starting analysis for {company}")

    try:
        from app.agents.graph.graph_agent import GraphAgent
        agent = GraphAgent()

        # Detect circular loops
        result = agent.process({
            "tool": "detect_circular_loops",
            "params": {
                "entity_name": company,
                "max_hops": 5,
                "min_transaction_amount": 0,
            },
        })

        loops = result.get("loops_found", [])
        total_amount = result.get("total_circular_amount", 0)
        loop_count = result.get("total_loop_count", 0)

        findings: List[str] = []
        evidence: Dict[str, str] = {}

        graph_payload = {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}
        try:
            graph_payload = agent.get_graph_payload(company, max_hops=5)
            evidence["graph_node_count"] = str(graph_payload.get("node_count", 0))
            evidence["graph_edge_count"] = str(graph_payload.get("edge_count", 0))
        except Exception as e:
            _logger.warning(f"Graph payload extraction failed: {e}")

        if loop_count > 0:
            for loop in loops[:5]:
                path_str = " → ".join(loop.get("path", []))
                flow = loop.get("total_flow", 0)
                findings.append(
                    f"Circular loop: {path_str} (₹{flow} Cr; source: Neo4j graph)"
                )
                if loop.get("suspicious"):
                    findings.append(f"  ⚠ Suspicious: {loop.get('reason', 'unknown')}")

            evidence["cycle_count"] = str(loop_count)
            evidence["total_circular_flow"] = f"₹{total_amount} Cr"

            # Score based on loops found
            risk_score = min(10.0, 3.0 + loop_count * 2.0)
            fraud_likelihood = "CRITICAL" if risk_score >= 8 else "HIGH" if risk_score >= 6 else "MEDIUM"
        else:
            findings.append("No circular trading loops detected (source: Neo4j graph)")
            evidence["cycle_count"] = "0"
            risk_score = 1.0
            fraud_likelihood = "LOW"

        evidence["fraud_likelihood"] = fraud_likelihood
        finding = _build_finding(risk_score, findings, evidence)

    except Exception as e:
        _logger.error(f"Graph Agent failed: {e}")
        finding = _build_finding(2.0, [f"Graph analysis error: {str(e)[:100]}"], {})
        graph_payload = {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

    return {
        "graph_findings": finding,
        "graph_payload": graph_payload,
        "messages": [f"Graph Agent: {finding['evidence'].get('cycle_count', '?')} cycles — score {finding['risk_score']}/10"],
    }


# ── Compliance Agent Node ──────────────────────────────────────

def compliance_node(state: InvestigationState) -> Dict[str, Any]:
    """Run real ComplianceAgent — checks SEBI regulations via RAG + LLM."""
    company = state.get("company_name", "Unknown")
    _logger.info(f"Compliance Agent: starting analysis for {company}")

    try:
        from app.agents.compliance.compliance_agent import ComplianceAgent
        agent = ComplianceAgent()

        # Build a comprehensive query from prior findings
        financial = state.get("financial_findings", {})
        graph = state.get("graph_findings", {})
        prior_findings = (
            financial.get("findings", [])[:3] +
            graph.get("findings", [])[:3]
        )
        context = f"Company: {company}. Prior findings: {'; '.join(prior_findings)}"

        findings: List[str] = []
        evidence: Dict[str, str] = {}
        violation_count = 0

        # Check SEBI regulations
        try:
            sebi_result = agent.process({
                "tool": "check_sebi_regulations",
                "params": {
                    "company_name": company,
                    "findings_summary": context,
                },
            })
            violations = sebi_result.get("violations", [])
            for v in violations:
                reg_id = v.get("regulation_id", "")
                desc = v.get("violation_description", "")
                findings.append(f"{reg_id}: {desc} (source: SEBI LODR)")
                violation_count += 1
        except Exception as e:
            _logger.warning(f"SEBI check failed: {e}")

        # RAG legal query for relevant regulations
        try:
            rag_result = agent.process({
                "tool": "rag_legal_query",
                "params": {
                    "query": f"Fraud indicators circular trading related party transactions {company}",
                    "source_filter": ["SEBI", "COMPANIES_ACT"],
                    "top_k": 3,
                },
            })
            for doc in rag_result.get("results", [])[:3]:
                findings.append(
                    f"Relevant regulation: {doc.get('title', 'Unknown')} "
                    f"(source: {doc.get('source', 'regulatory DB')}, "
                    f"relevance: {doc.get('relevance_score', 0):.2f})"
                )
        except Exception as e:
            _logger.warning(f"RAG legal query failed: {e}")

        if not findings:
            findings.append("No regulatory violations detected")
            risk_score = 1.0
        else:
            risk_score = min(10.0, 2.0 + violation_count * 3.0)

        evidence["violation_count"] = str(violation_count)
        evidence["highest_severity"] = "CRITICAL" if risk_score >= 7 else "HIGH" if risk_score >= 4 else "LOW"

        finding = _build_finding(risk_score, findings, evidence)

    except Exception as e:
        _logger.error(f"Compliance Agent failed: {e}")
        finding = _build_finding(2.0, [f"Compliance analysis error: {str(e)[:100]}"], {})

    return {
        "compliance_findings": finding,
        "messages": [f"Compliance Agent: {finding['evidence'].get('violation_count', '?')} violations — score {finding['risk_score']}/10"],
    }


# ── Audio Agent Node ───────────────────────────────────────────

def audio_node(state: InvestigationState) -> Dict[str, Any]:
    """Run real AudioAgent — RAG retrieval + LLM analysis on earnings call transcripts."""
    company = state.get("company_name", "Unknown")
    _logger.info(f"Audio Agent: starting analysis for {company}")
    timeline_data: List[Dict[str, Any]] = []
    timeline_total_duration = 0.0

    try:
        from app.agents.audio.audio_agent_rag import AudioAgent
        agent = AudioAgent()

        findings: List[str] = []
        evidence: Dict[str, str] = {}
        scores: List[float] = []

        # Tone analysis
        try:
            tone_result = agent.process({
                "tool": "analyze_audio_tone",
                "params": {"company": company, "query": "earnings call tone and sentiment"},
            })
            if tone_result.get("status") == "success":
                analysis = tone_result.get("analysis", {})
                sentiment = analysis.get("sentiment", "unknown")
                summary = analysis.get("summary", "")
                if summary:
                    findings.append(f"Tone analysis: {summary[:150]} (source: earnings call transcript)")
                evidence["sentiment"] = sentiment
                sentiment_score = {"positive": 2.0, "neutral": 4.0, "negative": 7.0}.get(sentiment, 5.0)
                scores.append(sentiment_score)
            else:
                findings.append(f"No audio transcript data for {company}")
        except Exception as e:
            _logger.warning(f"Audio tone analysis failed: {e}")

        # Deception marker detection with timeline support
        try:
            deception_result = agent.detect_deception_markers_with_timestamps(company)
            if deception_result.get("status") == "success":
                likelihood = deception_result.get("overall_likelihood", "unknown")
                markers = deception_result.get("markers", [])
                for marker in markers[:5]:
                    findings.append(
                        f"Deception marker [{marker.get('marker_type', 'deception')}] at "
                        f"{marker.get('start_time_s', 0)}s: {marker.get('explanation', '')} "
                        f"(source: earnings call)"
                    )
                evidence["deception_likelihood"] = likelihood
                evidence["marker_count"] = str(len(markers))
                evidence["total_duration_s"] = str(deception_result.get("total_duration_s", 0))
                deception_score = {"low": 2.0, "medium": 5.0, "high": 8.0}.get(likelihood, 4.0)
                scores.append(deception_score)
                timeline_data = markers
                timeline_total_duration = float(deception_result.get("total_duration_s", 0) or 0)
        except Exception as e:
            _logger.warning(f"Deception detection failed: {e}")

        risk_score = sum(scores) / len(scores) if scores else 4.0
        if not findings:
            findings.append("No audio transcript data available for analysis")

        finding = _build_finding(risk_score, findings, evidence)

    except Exception as e:
        _logger.error(f"Audio Agent failed: {e}")
        finding = _build_finding(3.0, [f"Audio analysis error: {str(e)[:100]}"], {})

    return {
        "audio_findings": finding,
        "audio_timeline": timeline_data,
        "audio_timeline_total_duration_s": timeline_total_duration,
        "messages": [f"Audio Agent: {finding['evidence'].get('sentiment', 'N/A')} — score {finding['risk_score']}/10"],
    }


# ── News Agent Node ───────────────────────────────────────────

def news_node(state: InvestigationState) -> Dict[str, Any]:
    """Run NewsAgent — Tavily/DDG search + LLM risk analysis on recent news."""
    company = state.get("company_name", "Unknown")
    _logger.info(f"News Agent: starting analysis for {company}")

    try:
        from app.agents.news.news_agent import NewsAgent
        agent = NewsAgent()

        # Search for recent news
        articles = agent.search(company, max_results=5)
        # Analyze with LLM
        analysis = agent.analyze(company, articles)

        findings: List[str] = analysis.get("findings", [])
        evidence: Dict[str, str] = {
            "sentiment": analysis.get("sentiment", "unknown"),
            "article_count": str(len(articles)),
            "search_source": articles[0].get("source", "N/A") if articles else "N/A",
        }

        if analysis.get("crisis_detected"):
            crisis = analysis.get("crisis_summary", "Crisis detected")
            findings.insert(0, f"⚠ CRISIS: {crisis}")
            evidence["crisis_detected"] = "true"

        risk_score = analysis.get("risk_score", 3.0)

        # Add article titles as evidence
        for i, article in enumerate(articles[:3]):
            evidence[f"article_{i+1}"] = article.get("title", "")[:100]

        finding = _build_finding(risk_score, findings[:10], evidence)

    except Exception as e:
        _logger.error(f"News Agent failed: {e}")
        finding = _build_finding(2.0, [f"News analysis error: {str(e)[:100]}"], {})

    return {
        "news_findings": finding,
        "messages": [f"News Agent: {finding['evidence'].get('sentiment', 'N/A')} — score {finding['risk_score']}/10"],
    }


# ── Reflection Agent Node ─────────────────────────────────────

def reflection_node(state: InvestigationState) -> Dict[str, Any]:
    """Cross-validate all agent findings via LLM for contradictions and unsourced claims."""
    _logger.info("Reflection Agent: reviewing all findings")

    try:
        all_findings = {
            "financial": state.get("financial_findings", {}),
            "graph": state.get("graph_findings", {}),
            "compliance": state.get("compliance_findings", {}),
            "audio": state.get("audio_findings", {}),
        }

        company = state.get("company_name", "Unknown")
        prompt = f"""You are the senior audit reviewer for Sathya Nishta (ET Markets fraud investigation).

Review all findings for {company} and check for:
1. Internal contradictions — e.g., one agent says healthy, another says critical
2. Unsourced claims — each finding should cite a source
3. Score inflation — high scores must be backed by multiple signals

Findings:
{json.dumps(all_findings, indent=2, default=str)}

Return ONLY JSON (no markdown):
{{"passed": true/false, "adjusted_score_delta": <float, e.g. -0.5 if scores too high>, "reflection_notes": "<summary>"}}"""

        result = chat_complete(
            user_prompt=prompt,
            system_prompt="You are a financial audit reviewer. Output JSON only.",
            temperature=0.2,
        )
        content = result.get("content", "").strip()

        # Parse JSON from response
        if "```" in content:
            content = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)

        return {
            "reflection_passed": parsed.get("passed", True),
            "reflection_notes": parsed.get("reflection_notes", "Findings reviewed"),
            "reflection_findings": {
                "risk_score": 0.0,
                "findings": [parsed.get("reflection_notes", "Findings reviewed")],
                "evidence": {}
            },
            "messages": [
                f"Reflection Agent: {'✅ Passed' if parsed.get('passed') else '⚠️ Adjusted'} — {parsed.get('reflection_notes', '')}"
            ],
        }

    except Exception as e:
        _logger.error(f"Reflection Agent failed: {e}")
        return {
            "reflection_passed": True,
            "reflection_notes": f"Reflection skipped due to error: {str(e)[:80]}",
            "messages": ["Reflection Agent: skipped (error)"],
        }


# ── Synthesis Node ─────────────────────────────────────────────

def synthesis_node(state: InvestigationState) -> Dict[str, Any]:
    """Compute weighted fraud_risk_score + verdict from agent findings.
    
    Weights have been rebalanced to prioritize the News Agent (25%).
    Implements a 'High Signal Override': If multiple agents detect high risk,
    the final verdict is escalated regardless of the weighted average.
    """
    weights = {
        "news": 0.25,        # Prioritized (was 0.13)
        "graph": 0.25,       # (was 0.30)
        "compliance": 0.20,  # (was 0.25)
        "financial": 0.20,   # (was 0.22)
        "audio": 0.10,       # (unchanged)
    }

    total_weight = 0.0
    weighted_sum = 0.0
    all_evidence = []
    
    # Track individual high-risk signals for override logic
    high_risk_count = 0      # Score >= 7.0
    critical_risk_count = 0  # Score >= 8.5
    max_individual_score = 0.0

    for agent_key, weight in weights.items():
        findings_key = f"{agent_key}_findings"
        finding = state.get(findings_key)
        if finding and isinstance(finding, dict):
            score = finding.get("risk_score", 0.0)
            weighted_sum += score * weight
            total_weight += weight
            
            if score > max_individual_score:
                max_individual_score = score
            
            if score >= 8.5:
                critical_risk_count += 1
            if score >= 7.0:
                high_risk_count += 1

            for f in finding.get("findings", []):
                all_evidence.append({
                    "source": agent_key.title(),
                    "finding": f,
                    "severity": (
                        "CRITICAL" if score >= 8.5 else
                        "HIGH" if score >= 7.0 else
                        "MEDIUM" if score >= 4.0 else
                        "LOW"
                    ),
                })

    # 1. Base Weighted Score
    base_score = weighted_sum / total_weight if total_weight > 0 else 0.0
    
    # 2. Apply Overrides
    # If any single agent is CRITICAL, floor the score to 7.5 (High Risk)
    if critical_risk_count >= 1:
        base_score = max(base_score, 7.5)
        
    # If TWO or more agents are HIGH or CRITICAL, floor the score to 8.0 (Critical floor)
    if high_risk_count >= 2:
        base_score = max(base_score, 8.2)

    fraud_risk_score = round(base_score, 1)

    # 3. Determine Verdict based on boosted score
    if fraud_risk_score >= 8.0:
        verdict = "CRITICAL"
    elif fraud_risk_score >= 6.5:
        verdict = "HIGH_RISK"
    elif fraud_risk_score >= 4.0:
        verdict = "CAUTION"
    else:
        verdict = "SAFE"

    company = state.get("company_name", "Unknown")
    _logger.info(f"Synthesis Complete: {company} -> {verdict} ({fraud_risk_score})")

    if verdict in ("CRITICAL", "HIGH_RISK"):
        try:
            import asyncio
            from app.shared.alert_dispatcher import dispatch_risk_alert
            top_findings = [e["finding"] for e in all_evidence[:3]]
            asyncio.create_task(dispatch_risk_alert(company, fraud_risk_score, verdict, top_findings))
        except Exception as e:
            _logger.warning(f"Alert dispatch failed: {e}")

    return {
        "fraud_risk_score": fraud_risk_score,
        "verdict": verdict,
        "evidence": all_evidence,
        "investigation_complete": True,
        "messages": [f"Synthesis: score={fraud_risk_score}, verdict={verdict} (High-Signal Detected: {high_risk_count})"],
    }
