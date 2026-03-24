#!/usr/bin/env python
"""Debug script to test LLM response directly."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.shared.llm_portkey import get_portkey_client
from app.shared.logger import setup_logger

logger = setup_logger("LLMDebug")

def test_llm_response():
    """Test what the LLM actually returns."""
    
    client =  get_portkey_client()
    logger.info("LLM client initialized")
    
    test_prompt = """Analyze this financial data and provide insights.

Financial Documents:
Company: Hindustan Unilever Limited
Document: Balance Sheet
Content: Total Assets: 100000 Cr, Current Liabilities: 30000 Cr

Provide your analysis in JSON format with these fields:
{
    "summary": "Brief summary of findings",
    "key_metrics": ["metric1", "metric2"],
    "anomalies": [],
    "health_indicator": "healthy" | "warning" | "critical",
    "recommendations": ["rec1", "rec2"]
}"""
    
    logger.info(f"Sending prompt of length {len(test_prompt)}")
    logger.info(f"Prompt: {test_prompt[:300]}")
    
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a financial analyst. Provide valid JSON response."},
            {"role": "user", "content": test_prompt}
        ],
        max_tokens=2000,
        temperature=0.5,
    )
    
    response_text = response.choices[0].message.content
    logger.info(f"Response length: {len(response_text)}")
    logger.info(f"Full response:\n{response_text}")
    
    # Also print to stdout
    print(f"\n{'='*80}")
    print(f"RESPONSE LENGTH: {len(response_text)}")
    print(f"FULL RESPONSE:")
    print(response_text)
    print(f"{'='*80}\n")

if __name__ == "__main__":
    test_llm_response()
