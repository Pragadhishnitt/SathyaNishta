"""Test suite for Audio Agent

This file contains test cases for the audio agent's tools:
- analyze_audio_tone
- detect_deception_markers
- load_audio_file

Run this file to test the agent with seeded earnings call transcripts:
    python3 backend/app/agents/audio/test_audio_agent.py
"""

import json
import sys
from pathlib import Path

# Add backend to path for imports
repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from app.agents.audio.audio_agent import AudioAgent


def test_analyze_audio_tone():
    """Test audio tone analysis from transcripts"""
    print("\n" + "=" * 60)
    print("Test 1: analyze_audio_tone")
    print("=" * 60)

    agent = AudioAgent()

    task = {
        "tool": "analyze_audio_tone",
        "params": {"company_name": "Hindustan Unilever Limited", "period": "Q4"},
        "investigation_id": "test_001",
        "task_id": "audio_test_1",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_detect_deception_markers():
    """Test deception markers detection in transcripts"""
    print("\n" + "=" * 60)
    print("Test 2: detect_deception_markers")
    print("=" * 60)

    agent = AudioAgent()

    task = {
        "tool": "detect_deception_markers",
        "params": {"company_name": "ITC Limited", "period": "Q4"},
        "investigation_id": "test_001",
        "task_id": "audio_test_2",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_load_audio_file():
    """Test audio file loading by company"""
    print("\n" + "=" * 60)
    print("Test 3: load_audio_file")
    print("=" * 60)

    agent = AudioAgent()

    task = {
        "tool": "load_audio_file",
        "params": {"company_name": "Wipro Limited", "period": "Q4"},
        "investigation_id": "test_001",
        "task_id": "audio_test_3",
    }

    try:
        result = agent.process(task)
        print("\n✓ Result:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


def test_multi_company_comparison():
    """Test analysis across multiple companies"""
    print("\n" + "=" * 60)
    print("Test 4: Multi-Company Tone Comparison")
    print("=" * 60)

    agent = AudioAgent()
    companies = ["Hindustan Unilever Limited", "ITC Limited", "Wipro Limited"]

    results_list = []
    for company in companies:
        task = {
            "tool": "analyze_audio_tone",
            "params": {"company_name": company, "period": "Q4"},
            "investigation_id": "test_001",
            "task_id": f"audio_test_compare_{company}",
        }

        try:
            result = agent.process(task)
            results_list.append({"company": company, "tone_result": result})
        except Exception as e:
            print(f"\n⚠️  {company}: {e}")

    if results_list:
        print("\n✓ Comparison Results:")
        print(json.dumps(results_list, indent=2))
        return results_list
    return None


def run_all_tests():
    """Run all test cases"""
    print("\n" + "=" * 80)
    print(" " * 20 + "AUDIO AGENT TEST SUITE")
    print("=" * 80)
    print("\nTesting with seeded earnings call transcripts from:")
    print("  • Hindustan Unilever Limited (HUL)")
    print("  • ITC Limited (ITC)")
    print("  • Wipro Limited (WIPRO)")
    print("  • State Bank of India (SBI)")
    print("  • Reliance Industries Limited (RIL)")

    results = {
        "analyze_audio_tone": test_analyze_audio_tone(),
        "detect_deception_markers": test_detect_deception_markers(),
        "load_audio_file": test_load_audio_file(),
        "multi_company_comparison": test_multi_company_comparison(),
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
