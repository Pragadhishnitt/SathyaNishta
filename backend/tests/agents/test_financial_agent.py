"""Test suite for Financial Agent

This file contains test cases for the financial agent's tools:
- analyze_balance_sheet
- calculate_financial_ratios
- detect_cash_flow_divergence
- detect_related_party_transactions

Run this file to test the agent with seeded balance sheet data:
    python3 backend/app/agents/financial/test_financial_agent.py
"""

import json
import sys
from pathlib import Path

# Add backend to path for imports
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from app.agents.financial.financial_agent import FinancialAgent


def test_analyze_balance_sheet():
    """Test balance sheet analysis"""
    print("\n" + "=" * 60)
    print("Test 1: analyze_balance_sheet")
    print("=" * 60)

    agent = FinancialAgent()

    task = {
        "tool": "analyze_balance_sheet",
        "params": {"company_name": "HindustanUnilever", "period": "FY2024"},
        "investigation_id": "test_001",
        "task_id": "financial_test_1",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_calculate_financial_ratios():
    """Test financial ratios calculation"""
    print("\n" + "=" * 60)
    print("Test 2: calculate_financial_ratios")
    print("=" * 60)

    agent = FinancialAgent()

    task = {
        "tool": "calculate_financial_ratios",
        "params": {"company_name": "Infosys", "period": "FY2024"},
        "investigation_id": "test_001",
        "task_id": "financial_test_2",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_detect_cash_flow_divergence():
    """Test cash flow divergence detection"""
    print("\n" + "=" * 60)
    print("Test 3: detect_cash_flow_divergence")
    print("=" * 60)

    agent = FinancialAgent()

    task = {
        "tool": "detect_cash_flow_divergence",
        "params": {"company_name": "Wipro", "period": "FY2024"},
        "investigation_id": "test_001",
        "task_id": "financial_test_3",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_detect_related_party_transactions():
    """Test related party transaction detection"""
    print("\n" + "=" * 60)
    print("Test 4: detect_related_party_transactions")
    print("=" * 60)

    agent = FinancialAgent()

    task = {
        "tool": "detect_related_party_transactions",
        "params": {"company_name": "SBI", "period": "FY2024"},
        "investigation_id": "test_001",
        "task_id": "financial_test_4",
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
    print(" " * 20 + "FINANCIAL AGENT TEST SUITE")
    print("=" * 80)
    print("\nTesting with seeded balance sheet data from:")
    print("  • Hindustan Unilever Limited (HUL)")
    print("  • ITC Limited (ITC)")
    print("  • Wipro Limited (WIPRO)")
    print("  • State Bank of India (SBI)")
    print("  • Reliance Industries Limited (RIL)")

    results = {
        "analyze_balance_sheet": test_analyze_balance_sheet(),
        "calculate_financial_ratios": test_calculate_financial_ratios(),
        "detect_cash_flow_divergence": test_detect_cash_flow_divergence(),
        "detect_related_party_transactions": test_detect_related_party_transactions(),
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
