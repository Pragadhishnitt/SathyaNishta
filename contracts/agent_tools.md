# Agent Tool Specifications
## Sathya Nishta — Agent Contract

**TEAM B OWNS THIS FILE**

This document defines the exact Python function signatures that each specialist agent must implement. These are the "tools" that agents use to perform their analysis.

**Critical Rule:** All tool functions must accept and return the exact types specified. Supervisor and Reflection agents depend on these contracts.

Version: 1.0.0  
Last Updated: Sprint 1

---

## Contract Rules

1. **All tools are Python functions** in the agent's `tools.py` file
2. **Type hints are mandatory** — use Pydantic models or built-in types
3. **Return types must be dict** (JSON-serializable)
4. **Errors must raise exceptions** with clear messages (not return error codes)
5. **All monetary values in INR paise** (integer) to avoid floating-point errors
6. **All dates in ISO 8601 format** (`YYYY-MM-DD`)

---

## 💰 Financial Agent Tools

### `analyze_balance_sheet`

**Purpose:** Analyzes balance sheet line items and compares across periods.

**Input:**
```python
{
    "company_ticker": str,  # e.g., "ADANI", "RELIANCE.NS"
    "period": str,  # e.g., "Q3-2024", "FY2023"
    "comparison_periods": List[str]  # e.g., ["Q2-2024", "Q3-2023"]
}
```

**Output:**
```python
{
    "total_assets": int,  # in INR paise
    "total_liabilities": int,  # in INR paise
    "total_equity": int,  # in INR paise
    "debt": int,  # in INR paise
    "cash_and_equivalents": int,  # in INR paise
    
    # Growth metrics (percentage)
    "debt_growth_yoy_percent": float,
    "assets_growth_yoy_percent": float,
    
    # Anomalies detected
    "anomalies": List[str],  # Human-readable descriptions
    
    # Source references
    "source_documents": List[str]  # e.g., ["Q3_2024_balance_sheet.pdf"]
}
```

**Example:**
```python
{
    "total_assets": 50000000000000,  # ₹5,00,000 Cr
    "total_liabilities": 20000000000000,  # ₹2,00,000 Cr
    "total_equity": 30000000000000,
    "debt": 15000000000000,
    "cash_and_equivalents": 5000000000000,
    "debt_growth_yoy_percent": 42.5,
    "assets_growth_yoy_percent": 12.3,
    "anomalies": [
        "Debt spiked by 42.5% compared to Q2-2024 (outside 2-year historical range)",
        "Debt-to-equity ratio increased from 0.35 to 0.50"
    ],
    "source_documents": ["Q3_2024_balance_sheet.pdf", "Q2_2024_balance_sheet.pdf"]
}
```

---

### `calculate_financial_ratios`

**Purpose:** Computes key financial ratios and flags anomalies.

**Input:**
```python
{
    "company_ticker": str,
    "period": str,
    "comparison_periods": List[str]
}
```

**Output:**
```python
{
    "ratios": {
        "debt_to_equity": float,
        "current_ratio": float,
        "interest_coverage": float,
        "return_on_equity": float,
        "asset_turnover": float
    },
    "historical_comparison": {
        "debt_to_equity_2yr_avg": float,
        "current_ratio_2yr_avg": float
    },
    "anomalies": List[str],
    "source_documents": List[str]
}
```

---

### `detect_cash_flow_divergence`

**Purpose:** Detects the "profit is up, cash is down" red flag (classic circular trading signal).

**Input:**
```python
{
    "company_ticker": str,
    "period": str
}
```

**Output:**
```python
{
    "ebitda": int,  # INR paise
    "ebitda_growth_percent": float,  # YoY
    "operating_cash_flow": int,  # INR paise
    "operating_cash_flow_growth_percent": float,  # YoY
    "divergence_detected": bool,
    "divergence_magnitude_percent": float,  # Absolute difference
    "severity": str,  # "critical" | "high" | "medium" | "low"
    "explanation": str,  # Human-readable
    "source_documents": List[str]
}
```

**Example:**
```python
{
    "ebitda": 1200000000000,  # ₹12,000 Cr
    "ebitda_growth_percent": 15.5,
    "operating_cash_flow": 800000000000,  # ₹8,000 Cr
    "operating_cash_flow_growth_percent": -8.2,
    "divergence_detected": True,
    "divergence_magnitude_percent": 23.7,
    "severity": "high",
    "explanation": "EBITDA grew 15.5% but operating cash flow declined 8.2%. This 23.7% divergence suggests revenue recognition without actual cash collection — a potential circular trading signal.",
    "source_documents": ["Q3_2024_cashflow.pdf", "Q3_2023_cashflow.pdf"]
}
```

---

### `detect_related_party_transactions`

**Purpose:** Identifies undisclosed or suspicious related-party transactions.

**Input:**
```python
{
    "company_ticker": str,
    "period": str
}
```

**Output:**
```python
{
    "related_party_transactions": List[{
        "counterparty": str,
        "amount": int,  # INR paise
        "transaction_type": str,  # "loan", "purchase", "sale", "investment"
        "disclosed": bool,
        "suspicious": bool,
        "reason": str  # Why it's flagged as suspicious
    }],
    "total_undisclosed_amount": int,  # INR paise
    "source_documents": List[str]
}
```

---

## 🕸️ Graph Agent Tools

### `generate_cypher_query`

**Purpose:** Converts a natural language investigation goal into a Cypher query.

**Input:**
```python
{
    "entity_name": str,  # e.g., "Adani"
    "query_type": str,  # "circular_loop" | "ownership_chain" | "transaction_path"
    "max_hops": int,  # Maximum path length (default: 5)
    "min_transaction_amount": int  # INR paise (filter small transactions)
}
```

**Output:**
```python
{
    "cypher_query": str,  # Valid Cypher query
    "explanation": str  # What this query does
}
```

**Example:**
```python
{
    "cypher_query": "MATCH path = (c:Company {name: 'Adani'})-[:TRANSACTS_WITH*1..5]-(c) WHERE ALL(r IN relationships(path) WHERE r.amount > 10000000000) RETURN path, reduce(total = 0, r IN relationships(path) | total + r.amount) AS loop_total",
    "explanation": "Finds all circular transaction paths starting and ending at Adani, with max 5 hops, filtering transactions < ₹100 Cr"
}
```

---

### `run_cypher_query`

**Purpose:** Executes a Cypher query against Neo4j and returns structured results.

**Input:**
```python
{
    "query": str,  # Cypher query
    "params": Dict[str, Any]  # Query parameters
}
```

**Output:**
```python
{
    "results": List[Dict[str, Any]],  # Query results
    "result_count": int
}
```

**Example:**
```python
{
    "results": [
        {
            "path": ["Adani", "Shell_A", "Shell_B", "Adani"],
            "loop_total": 50000000000000  # ₹500 Cr
        },
        {
            "path": ["Adani", "Mauritius_Fund", "Adani"],
            "loop_total": 30000000000000  # ₹300 Cr
        }
    ],
    "result_count": 2
}
```

---

### `detect_circular_loops`

**Purpose:** High-level tool that combines Cypher generation, execution, and validation.

**Input:**
```python
{
    "entity_name": str,
    "max_hops": int,
    "min_transaction_amount": int  # INR paise
}
```

**Output:**
```python
{
    "loops_found": List[{
        "path": List[str],  # ["Company A", "Shell B", "Company A"]
        "path_length": int,
        "total_flow": int,  # INR paise
        "transaction_dates": List[str],  # ISO 8601 dates
        "suspicious": bool,
        "reason": str  # Why it's suspicious
    }],
    "total_loop_count": int,
    "total_circular_amount": int  # INR paise
}
```

**Example:**
```python
{
    "loops_found": [
        {
            "path": ["Adani", "Vinod_Adani_Trust", "Shell_Mauritius", "Adani"],
            "path_length": 3,
            "total_flow": 50000000000000,
            "transaction_dates": ["2024-07-15", "2024-08-20", "2024-09-10"],
            "suspicious": True,
            "reason": "Same amount (₹500 Cr) flows in circle within 90 days"
        }
    ],
    "total_loop_count": 1,
    "total_circular_amount": 50000000000000
}
```

---

## 🎙️ Audio Agent Tools

### `load_audio_file`

**Purpose:** Fetches audio file from Supabase Storage and prepares it for analysis.

**Input:**
```python
{
    "file_key": str,  # Supabase Storage key, e.g., "earnings_calls/adani_q3_2024.mp3"
    "start_time_sec": Optional[int],  # Start of segment to analyze
    "end_time_sec": Optional[int]  # End of segment
}
```

**Output:**
```python
{
    "file_key": str,
    "duration_sec": int,
    "audio_base64": str,  # Base64-encoded audio (for Gemini API)
    "format": str,  # "mp3", "wav", etc.
    "segment_analyzed": Optional[{
        "start_sec": int,
        "end_sec": int
    }]
}
```

---

### `analyze_audio_tone`

**Purpose:** Analyzes vocal tone, stress, and emotional state using Gemini's native audio input.

**Critical:** This tool must send **raw audio** to Gemini (no transcription step). Gemini 1.5 Flash supports native audio analysis.

**Input:**
```python
{
    "audio_base64": str,  # From load_audio_file
    "context": str  # What to focus on, e.g., "revenue discussion"
}
```

**Output:**
```python
{
    "segments": List[{
        "start_sec": int,
        "end_sec": int,
        "tone_label": str,  # "confident" | "nervous" | "neutral" | "stressed" | "hesitant"
        "stress_score": float,  # 0.0 to 1.0
        "speaking_pace": str,  # "slow" | "normal" | "fast"
        "pitch_change": str,  # "stable" | "rising" | "falling" | "erratic"
    }],
    "overall_tone": str,
    "confidence_in_analysis": float  # 0.0 to 1.0
}
```

---

### `detect_deception_markers`

**Purpose:** Identifies vocal cues associated with deception (hedging language, topic avoidance, stress spikes).

**Input:**
```python
{
    "audio_base64": str,
    "transcript": Optional[str],  # If available (from Gemini or separate ASR)
    "focus_topics": List[str]  # Topics to watch for (e.g., ["revenue", "related party transactions"])
}
```

**Output:**
```python
{
    "deception_markers": List[{
        "timestamp_sec": int,
        "marker_type": str,  # "hedging_language" | "topic_avoidance" | "stress_spike" | "inconsistency"
        "detail": str,  # What was detected
        "confidence": float  # 0.0 to 1.0
    }],
    "hedging_word_count": int,  # "I think", "maybe", "possibly", etc.
    "topic_avoidance_count": int,
    "overall_deception_likelihood": float,  # 0.0 to 1.0
    "explanation": str
}
```

**Example:**
```python
{
    "deception_markers": [
        {
            "timestamp_sec": 734,
            "marker_type": "hedging_language",
            "detail": "Speaker used 'I believe' and 'we think' 5 times when discussing Q3 revenue",
            "confidence": 0.88
        },
        {
            "timestamp_sec": 782,
            "marker_type": "topic_avoidance",
            "detail": "Analyst asked about cash flow, CEO shifted to EBITDA growth without answering",
            "confidence": 0.92
        },
        {
            "timestamp_sec": 810,
            "marker_type": "stress_spike",
            "detail": "Voice stress increased by 40% when questioned about related-party transactions",
            "confidence": 0.85
        }
    ],
    "hedging_word_count": 15,
    "topic_avoidance_count": 2,
    "overall_deception_likelihood": 0.78,
    "explanation": "Multiple deception markers detected during revenue and related-party transaction discussions"
}
```

---

## ⚖️ Compliance Agent Tools

### `check_sebi_regulations`

**Purpose:** Validates a finding against SEBI LODR, Companies Act, and other Indian regulations.

**Input:**
```python
{
    "finding_text": str,  # Description of the finding (e.g., from Financial or Graph agent)
    "regulation_context": str  # "related_party" | "disclosure" | "insider_trading" | "general"
}
```

**Output:**
```python
{
    "violations": List[{
        "regulation_id": str,  # e.g., "SEBI_LODR_Reg_23"
        "regulation_title": str,
        "violation_description": str,
        "severity": str,  # "critical" | "high" | "medium" | "low"
        "penalty_clause": Optional[str]
    }],
    "violation_probability": float,  # 0.0 to 1.0
    "cited_documents": List[str]  # Source regulations from RAG
}
```

**Example:**
```python
{
    "violations": [
        {
            "regulation_id": "SEBI_LODR_Reg_23_2",
            "regulation_title": "Related Party Transactions - Disclosure Requirements",
            "violation_description": "Company did not disclose a ₹500 Cr related-party transaction exceeding the ₹1 Cr threshold in quarterly filing",
            "severity": "critical",
            "penalty_clause": "Section 188 of Companies Act, 2013"
        }
    ],
    "violation_probability": 0.95,
    "cited_documents": ["SEBI_LODR_Reg_23.pdf", "CompaniesAct_Section_188.pdf"]
}
```

---

### `verify_indas_compliance`

**Purpose:** Cross-references financial findings against IndAS accounting standards.

**Input:**
```python
{
    "finding_text": str,
    "indas_context": str  # "revenue_recognition" | "asset_valuation" | "related_party" | "disclosure"
}
```

**Output:**
```python
{
    "indas_violations": List[{
        "standard_id": str,  # e.g., "IndAS_24"
        "standard_title": str,
        "violation_description": str,
        "severity": str
    }],
    "compliance_score": float,  # 0.0 to 1.0 (1.0 = fully compliant)
    "cited_documents": List[str]
}
```

---

### `rag_legal_query`

**Purpose:** Performs semantic search on legal documents (SEBI regs, IndAS, precedents) using pgvector.

**Input:**
```python
{
    "query": str,  # Natural language query
    "source_filter": Optional[List[str]],  # Filter by source: ["SEBI", "IndAS"]
    "top_k": int  # Number of results to return (default: 3)
}
```

**Output:**
```python
{
    "results": List[{
        "document_id": str,
        "title": str,
        "source": str,
        "relevance_score": float,  # Cosine similarity (0.0 to 1.0)
        "excerpt": str  # Relevant text chunk
    }]
}
```

---

## Implementation Checklist for Team B

Each agent must implement these tools in their `tools.py` file:

### Financial Agent (`agents/financial/tools.py`)
- [ ] `analyze_balance_sheet`
- [ ] `calculate_financial_ratios`
- [ ] `detect_cash_flow_divergence`
- [ ] `detect_related_party_transactions`

### Graph Agent (`agents/graph/tools.py`)
- [ ] `generate_cypher_query`
- [ ] `run_cypher_query`
- [ ] `detect_circular_loops`

### Audio Agent (`agents/audio/tools.py`)
- [ ] `load_audio_file`
- [ ] `analyze_audio_tone`
- [ ] `detect_deception_markers`

### Compliance Agent (`agents/compliance/tools.py`)
- [ ] `check_sebi_regulations`
- [ ] `verify_indas_compliance`
- [ ] `rag_legal_query`

---

## Testing Requirements

Each tool must have:
1. **Unit tests** with known inputs and expected outputs
2. **Fixtures** for test data (sample balance sheets, audio files, etc.)
3. **Error handling tests** (malformed input, missing data, API failures)

Example test:
```python
def test_detect_cash_flow_divergence():
    result = detect_cash_flow_divergence({
        "company_ticker": "TEST_COMPANY",
        "period": "Q3-2024"
    })
    assert result["divergence_detected"] == True
    assert result["severity"] in ["critical", "high", "medium", "low"]
    assert len(result["source_documents"]) > 0
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-02-04 | Initial contract definition |
