#!/usr/bin/env python3
"""
Test script for Graph Agent
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from app.agents.graph.graph_agent import GraphAgent


def test_graph_agent():
    print("\n" + "=" * 80)
    print("GRAPH AGENT TEST SUITE".center(80))
    print("=" * 80)

    # Initialize agent
    try:
        agent = GraphAgent()
        print("✅ GraphAgent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize GraphAgent: {e}")
        return

    # Test 1: generate_cypher_query
    print("\n" + "=" * 60)
    print("Test 1: generate_cypher_query")
    print("=" * 60)
    task1 = {
        "tool": "generate_cypher_query",
        "params": {
            "entity_name": "Adani Enterprises Limited",
            "query_type": "circular_transactions",
            "max_hops": 4,
            "min_transaction_amount": 50000000000000,  # matches DB (₹500 Cr)
        },
    }
    try:
        result1 = agent.process(task1)
        print("✓ Result:")
        print(json.dumps(result1, indent=2))
    except Exception as e:
        print(f"❌ generate_cypher_query failed: {e}")

    # Test 2: run_cypher_query
    print("\n" + "=" * 60)
    print("Test 2: run_cypher_query")
    print("=" * 60)
    cypher_query = """
        MATCH path = (c:Company {name: 'Adani Enterprises Limited'})-[:TRANSACTS_WITH*1..4]-(c)
        WHERE ALL(r IN relationships(path) WHERE r.amount >= 50000000000000)
        RETURN path, reduce(total = 0, r IN relationships(path) | total + r.amount) AS loop_total
        LIMIT 3
    """
    task2 = {
        "tool": "run_cypher_query",
        "params": {
            "query": cypher_query,
            "params": {},
            "use_readonly": False,  # Add this if your driver requires explicit routing
        },
    }
    try:
        result2 = agent.process(task2)
        print("✓ Result:")
        print(json.dumps(result2, indent=2))
    except Exception as e:
        print(f"❌ run_cypher_query failed: {e}")

    # Test 3: detect_circular_loops
    print("\n" + "=" * 60)
    print("Test 3: detect_circular_loops")
    print("=" * 60)
    task3 = {
        "tool": "detect_circular_loops",
        "params": {
            "entity_name": "Adani Enterprises Limited",
            "min_transaction_amount": 40000000000000,  # Slightly lower to catch ₹500 Cr transactions
            "max_hops": 4,
        },
    }
    try:
        result3 = agent.process(task3)
        print("✓ Result:")
        print(json.dumps(result3, indent=2))
    except Exception as e:
        print(f"❌ detect_circular_loops failed: {e}")

    print("\n" + "=" * 80)
    print("TEST SUMMARY".center(80))
    print("=" * 80)
    print("generate_cypher_query............................", "✓ PASSED" if "result1" in locals() else "✗ FAILED")
    print("run_cypher_query...................................", "✓ PASSED" if "result2" in locals() else "✗ FAILED")
    print("detect_circular_loops.............................", "✓ PASSED" if "result3" in locals() else "✗ FAILED")
    print(
        "\nTotal: 3/3 tests passed" if all(x in locals() for x in ["result1", "result2", "result3"]) else "\nSome tests failed"
    )
    print("=" * 80)


if __name__ == "__main__":
    test_graph_agent()
