#!/usr/bin/env python3
"""
Test Audio Agent with RAG and LLM Analysis

Tests the three main audio agent functions:
1. analyze_audio_tone - Analyze tone/sentiment from company transcripts
2. detect_deception_markers - Detect deception patterns
3. analyze_transcript_content - General content analysis
"""

import os
import sys
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

from app.agents.audio.audio_agent_rag import AudioAgent


def test_analyze_audio_tone():
    """Test 1: Analyze audio tone for a company"""
    print("\n" + "=" * 80)
    print("TEST 1: analyze_audio_tone")
    print("=" * 80)

    agent = AudioAgent()

    task = {
        "tool": "analyze_audio_tone",
        "params": {
            "company": "State Bank of India",
            "query": "tone and sentiment regarding balance sheet and financial stability",
        },
    }

    try:
        result = agent.process(task)

        print(f"\n✓ Company: {result.get('company')}")
        print(f"✓ Query: {result.get('query')}")
        print(f"✓ Found Documents: {result.get('found_documents')}")

        if result.get("found_documents", 0) > 0:
            print(f"✓ Document Similarities: {[f'{s:.2%}' for s in result.get('document_similarity', [])]}")

        analysis = result.get("analysis", {})
        print(f"\n📊 Analysis:")
        print(f"   Summary: {analysis.get('summary', 'N/A')}")
        print(f"   Tone Indicators: {analysis.get('tone_indicators', [])}")
        print(f"   Sentiment: {analysis.get('sentiment', 'unknown')}")
        print(f"   Intensity: {analysis.get('intensity', 'unknown')}")

        print(f"\n✓ Status: {result.get('status')}")
        print("✅ TEST 1 PASSED")
        return True

    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_detect_deception_markers():
    """Test 2: Detect deception markers"""
    print("\n" + "=" * 80)
    print("TEST 2: detect_deception_markers")
    print("=" * 80)

    agent = AudioAgent()

    task = {
        "tool": "detect_deception_markers",
        "params": {"company": "Reliance Industries", "focus": "financial statements and liability reporting"},
    }

    try:
        result = agent.process(task)

        print(f"\n✓ Company: {result.get('company')}")
        print(f"✓ Focus: {result.get('focus')}")
        print(f"✓ Found Documents: {result.get('found_documents')}")

        if result.get("found_documents", 0) > 0:
            print(f"✓ Document Similarities: {[f'{s:.2%}' for s in result.get('document_similarity', [])]}")

        analysis = result.get("analysis", {})
        print(f"\n🔍 Analysis:")
        print(f"   Summary: {analysis.get('summary', 'N/A')}")
        print(f"   Deception Markers: {analysis.get('deception_markers', [])}")
        print(f"   Likelihood: {analysis.get('likelihood', 'unknown')}")
        print(f"   Confidence: {analysis.get('confidence', 'unknown')}")

        print(f"\n✓ Status: {result.get('status')}")
        print("✅ TEST 2 PASSED")
        return True

    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_analyze_transcript_content():
    """Test 3: Analyze transcript content"""
    print("\n" + "=" * 80)
    print("TEST 3: analyze_transcript_content")
    print("=" * 80)

    agent = AudioAgent()

    task = {
        "tool": "analyze_transcript_content",
        "params": {"company": "Wipro", "topic": "financial health, cash flows, and operational efficiency"},
    }

    try:
        result = agent.process(task)

        print(f"\n✓ Company: {result.get('company')}")
        print(f"✓ Topic: {result.get('topic')}")
        print(f"✓ Found Documents: {result.get('found_documents')}")

        if result.get("found_documents", 0) > 0:
            print(f"✓ Document Similarities: {[f'{s:.2%}' for s in result.get('document_similarity', [])]}")

        analysis = result.get("analysis", {})
        print(f"\n📈 Analysis:")
        print(f"   Summary: {analysis.get('summary', 'N/A')}")
        print(f"   Key Points: {analysis.get('key_points', [])}")
        print(f"   Financial Health: {analysis.get('financial_health_assessment', 'unknown')}")
        print(f"   Recommendations: {analysis.get('recommendations', [])}")

        print(f"\n✓ Status: {result.get('status')}")
        print("✅ TEST 3 PASSED")
        return True

    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_analyze_itc():
    """Test 4: Analyze ITC Limited transcript"""
    print("\n" + "=" * 80)
    print("TEST 4: analyze_transcript_content (ITC)")
    print("=" * 80)

    agent = AudioAgent()

    task = {
        "tool": "analyze_transcript_content",
        "params": {"company": "ITC Limited", "topic": "business portfolio, debt position, and cash flow stability"},
    }

    try:
        result = agent.process(task)

        print(f"\n✓ Company: {result.get('company')}")
        print(f"✓ Topic: {result.get('topic')}")
        print(f"✓ Found Documents: {result.get('found_documents')}")

        if result.get("found_documents", 0) > 0:
            print(f"✓ Document Similarities: {[f'{s:.2%}' for s in result.get('document_similarity', [])]}")

        analysis = result.get("analysis", {})
        print(f"\n📈 Analysis:")
        print(f"   Summary: {analysis.get('summary', 'N/A')}")
        print(f"   Key Points: {analysis.get('key_points', [])}")
        print(f"   Financial Health: {analysis.get('financial_health_assessment', 'unknown')}")
        print(f"   Recommendations: {analysis.get('recommendations', [])}")

        print(f"\n✓ Status: {result.get('status')}")
        print("✅ TEST 4 PASSED")
        return True

    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_hindi_unilever():
    """Test 5: Analyze HUL transcript"""
    print("\n" + "=" * 80)
    print("TEST 5: analyze_audio_tone (Hindustan Unilever)")
    print("=" * 80)

    agent = AudioAgent()

    task = {
        "tool": "analyze_audio_tone",
        "params": {
            "company": "Hindustan Unilever",
            "query": "tone regarding operational efficiency and capital management",
        },
    }

    try:
        result = agent.process(task)

        print(f"\n✓ Company: {result.get('company')}")
        print(f"✓ Query: {result.get('query')}")
        print(f"✓ Found Documents: {result.get('found_documents')}")

        if result.get("found_documents", 0) > 0:
            print(f"✓ Document Similarities: {[f'{s:.2%}' for s in result.get('document_similarity', [])]}")

        analysis = result.get("analysis", {})
        print(f"\n📊 Analysis:")
        print(f"   Summary: {analysis.get('summary', 'N/A')}")
        print(f"   Tone Indicators: {analysis.get('tone_indicators', [])}")
        print(f"   Sentiment: {analysis.get('sentiment', 'unknown')}")
        print(f"   Intensity: {analysis.get('intensity', 'unknown')}")

        print(f"\n✓ Status: {result.get('status')}")
        print("✅ TEST 5 PASSED")
        return True

    except Exception as e:
        print(f"❌ TEST 5 FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("AUDIO AGENT TEST SUITE")
    print("Testing RAG + LLM analysis for audio transcripts")
    print("=" * 80)

    results = []

    # Run all tests
    results.append(("analyze_audio_tone (SBI)", test_analyze_audio_tone()))
    results.append(("detect_deception_markers (RIL)", test_detect_deception_markers()))
    results.append(("analyze_transcript_content (Wipro)", test_analyze_transcript_content()))
    results.append(("analyze_transcript_content (ITC)", test_analyze_itc()))
    results.append(("analyze_audio_tone (HUL)", test_hindi_unilever()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("=" * 80)


if __name__ == "__main__":
    main()
