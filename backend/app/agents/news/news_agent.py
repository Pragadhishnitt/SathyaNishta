"""NewsAgent — Real-time web/news sentiment analysis using Tavily + DDG fallback.

Searches for recent news about a company, then analyzes sentiment and risk
signals using LLM to detect immediate crises (e.g., CFO resignations,
regulatory actions, sudden stock drops).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.shared.logger import setup_logger
from app.shared.llm_portkey import chat_complete
from tenacity import retry, wait_exponential, stop_after_attempt

_logger = setup_logger("news_agent")


class NewsAgent:
    """Searches recent news for a company and extracts risk signals."""

    def __init__(self) -> None:
        self._tavily_client: Optional[Any] = None
        self._init_tavily()

    def _init_tavily(self) -> None:
        """Try to init Tavily client; fall back to DDG if unavailable."""
        try:
            import os
            api_key = os.getenv("TAVILY_API_KEY", "")
            if api_key:
                from tavily import TavilyClient
                self._tavily_client = TavilyClient(api_key=api_key)
                _logger.info("NewsAgent: Tavily client initialized")
            else:
                _logger.warning("NewsAgent: No TAVILY_API_KEY — will use DuckDuckGo fallback")
        except ImportError:
            _logger.warning("NewsAgent: tavily package not installed — will use DuckDuckGo fallback")

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def _search_tavily(self, company: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search via Tavily API (returns clean, RAG-optimized content)."""
        if not self._tavily_client:
            return []
        try:
            response = self._tavily_client.search(
                query=f"{company} fraud scandal investigation regulatory action recent news",
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
            )
            results = []
            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")[:500],
                    "source": "Tavily",
                })
            return results
        except Exception as e:
            _logger.warning(f"Tavily search failed: {e}")
            return []

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def _search_duckduckgo(self, company: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fallback: search via DuckDuckGo (free, no API key)."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                raw = list(ddgs.news(
                    f"{company} fraud investigation regulatory",
                    max_results=max_results,
                ))
            results = []
            for r in raw:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("body", "")[:500],
                    "source": "DuckDuckGo",
                })
            return results
        except Exception as e:
            _logger.warning(f"DuckDuckGo search failed: {e}")
            return []

    def search(self, company: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search with Tavily first, then DDG fallback."""
        results = self._search_tavily(company, max_results)
        if not results:
            results = self._search_duckduckgo(company, max_results)
        return results

    def analyze(self, company: str, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Use LLM to analyze news articles for risk signals."""
        if not articles:
            return {
                "sentiment": "neutral",
                "risk_score": 2.0,
                "findings": ["No recent news articles found for analysis"],
                "crisis_detected": False,
            }

        articles_text = "\n\n".join(
            f"**{a['title']}** ({a['source']})\n{a['content']}"
            for a in articles[:5]
        )

        prompt = f"""You are a financial news risk analyst for the Sathya Nishta fraud investigation system.

Analyze these recent news articles about "{company}" and assess:
1. Overall sentiment (positive/neutral/negative)
2. Risk signals (regulatory actions, executive departures, fraud allegations, lawsuits)
3. Crisis indicators (sudden events that indicate immediate danger)
4. Risk score from 0–10 (0=no risk, 10=critical crisis)

News Articles:
{articles_text}

Return ONLY JSON (no markdown):
{{"sentiment": "positive|neutral|negative", "risk_score": <float 0-10>, "findings": ["<finding1>", ...], "crisis_detected": true/false, "crisis_summary": "<if crisis detected>"}}"""

        try:
            result = chat_complete(
                user_prompt=prompt,
                system_prompt="You are a financial news risk analyst. Output JSON only.",
                temperature=0.2,
            )
            content = result.get("content", "").strip()

            # Parse JSON
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0].strip() if "```json" in content else content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)
            return parsed
        except Exception as e:
            _logger.error(f"News analysis LLM call failed: {e}")
            return {
                "sentiment": "unknown",
                "risk_score": 3.0,
                "findings": [f"News analysis unavailable: {str(e)[:80]}"],
                "crisis_detected": False,
            }
