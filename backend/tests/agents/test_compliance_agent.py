"""Test suite for Compliance Agent

This file contains test cases for the compliance agent's three main tools:
- check_sebi_regulations
- verify_indas_compliance
- rag_legal_query

Run this file to test the agent in isolation:
    python3 backend/app/agents/compliance/test_compliance_agent.py
"""

import json
import sys
from pathlib import Path

# Add backend to path for imports
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from app.agents.compliance.compliance_agent import ComplianceAgent


def test_check_sebi_regulations():
    """Test SEBI regulations validation"""
    print("\n" + "=" * 60)
    print("Test 1: check_sebi_regulations")
    print("=" * 60)

    agent = ComplianceAgent()

    task = {
        "tool": "check_sebi_regulations",
        "params": {
            "finding_text": "Company did not disclose a ₹500 Cr related-party transaction in quarterly filing",
            "regulation_context": "related_party",
        },
        "investigation_id": "test_001",
        "task_id": "compliance_test_1",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_verify_indas_compliance():
    """Test IndAS compliance verification"""
    print("\n" + "=" * 60)
    print("Test 2: verify_indas_compliance")
    print("=" * 60)

    agent = ComplianceAgent()

    task = {
        "tool": "verify_indas_compliance",
        "params": {
            "finding_text": "Company recognized revenue before delivery of goods and services",
            "indas_context": "revenue_recognition",
        },
        "investigation_id": "test_001",
        "task_id": "compliance_test_2",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_rag_legal_query():
    """Test RAG-based legal document search"""
    print("\n" + "=" * 60)
    print("Test 3: rag_legal_query")
    print("=" * 60)

    agent = ComplianceAgent()

    task = {
        "tool": "rag_legal_query",
        "params": {
            "query": "What are the disclosure requirements for related party transactions?",
            "source_filter": ["SEBI", "IndAS"],
            "top_k": 3,
        },
        "investigation_id": "test_001",
        "task_id": "compliance_test_3",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def run_all_tests():
    """Run all test cases"""
    print("\n" + "=" * 80)
    print(" " * 20 + "COMPLIANCE AGENT TEST SUITE")
    print("=" * 80)

    results = {
        "check_sebi_regulations": test_check_sebi_regulations(),
        "verify_indas_compliance": test_verify_indas_compliance(),
        "rag_legal_query": test_rag_legal_query(),
    }

    # Summary
    print("\n" + "=" * 80)
    print(" " * 30 + "TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results.values() if r is not None)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result is not None else "✗ FAILED"
        print(f"{test_name:.<50} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 80 + "\n")

    return results


if __name__ == "__main__":
    run_all_tests()
