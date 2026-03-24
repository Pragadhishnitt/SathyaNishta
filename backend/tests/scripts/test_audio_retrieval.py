#!/usr/bin/env python3
"""Test audio agent document retrieval in detail"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from app.agents.audio.audio_agent_rag import AudioAgent

agent = AudioAgent()

print("=" * 80)
print("DETAILED AUDIO RETRIEVAL TEST")
print("=" * 80)

# Test various company name formats
test_companies = [
    "State Bank of India",
    "SBI",
    "Wipro",
    "ITC",
    "ITC Limited",
    "Reliance Industries",
    "Hindustan Unilever"
]

print(f"\nAgent database engine initialized: {agent.engine is not None}")
print(f"Agent LLM client initialized: {agent.llm_client is not None}")

for company in test_companies:
    print(f"\n--- Testing: '{company}' ---")
    try:
        docs = agent._retrieve_audio_documents(company, "financial performance", top_k=3)
        print(f"✓ Retrieved {len(docs)} documents")
        if docs:
            for doc in docs:
                print(f"  - {doc['company_name']} (similarity: {doc['similarity']:.2%})")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
