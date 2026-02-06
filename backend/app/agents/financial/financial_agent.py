"""Financial agent implementation aligned with contract specs.

This agent exposes contract-aligned tool handlers:
- analyze_balance_sheet
- calculate_financial_ratios
- detect_cash_flow_divergence
- detect_related_party_transactions

`process` expects a task dict of the shape:
{
    "tool": "analyze_balance_sheet" | "calculate_financial_ratios" | ...,
    "params": { ... }  # matches the contract for that tool
}
It routes to the corresponding handler and returns the tool's output dict.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger


class FinancialAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)
        # LLM endpoint (e.g., Portkey or OpenAI-compatible router)
        self.llm_url = os.getenv("LLM_API_URL", "https://api.portkey.ai/v1/chat/completions")
        self.llm_api_key = os.getenv("PORTKEY_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.portkey_config = os.getenv("PORTKEY_CONFIG")
        self.llm_model = self._model_from_portkey_config() or "gemini-2.5-flash"

        self.tool_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "analyze_balance_sheet": self.analyze_balance_sheet,
            "calculate_financial_ratios": self.calculate_financial_ratios,
            "detect_cash_flow_divergence": self.detect_cash_flow_divergence,
            "detect_related_party_transactions": self.detect_related_party_transactions,
        }

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route the incoming task to the correct financial tool.

        Expected task keys: tool (str), params (dict).
        Raises ValueError for unknown tools or missing params.
        """

        tool_name = task.get("tool")
        params = task.get("params", {})

        if not tool_name:
            raise ValueError("FinancialAgent task missing 'tool'")
        if tool_name not in self.tool_map:
            raise ValueError(f"Unsupported financial tool: {tool_name}")
        if not isinstance(params, dict):
            raise ValueError("FinancialAgent task 'params' must be a dict")

        self.logger.debug("Running financial tool", extra={"tool": tool_name, "params": params})
        return self.tool_map[tool_name](params, task)

    # ---------------------------------------------------------------------
    # Tool implementations (contract-compliant shapes with placeholder data)
    # ---------------------------------------------------------------------
    def analyze_balance_sheet(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate balance sheet analysis to the external financial analysis API."""

        return self._call_llm("analyze_balance_sheet", params, task)

    def calculate_financial_ratios(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_llm("calculate_financial_ratios", params, task)

    def detect_cash_flow_divergence(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_llm("detect_cash_flow_divergence", params, task)

    def detect_related_party_transactions(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        return self._call_llm("detect_related_party_transactions", params, task)

    # ------------------------------------------------------------------
    # Internal helper: call LLM and return JSON per contract
    # ------------------------------------------------------------------
    def _call_llm(
        self,
        tool_name: str,
        params: Dict[str, Any],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a structured prompt to the LLM router and parse JSON output.

        The LLM is expected to return a JSON object matching the tool contract.
        Raises RuntimeError on HTTP or parsing issues.
        """

        if not self.llm_api_key:
            raise RuntimeError("LLM_API_KEY or PORTKEY_API_KEY is not set")

        system_prompt = self._build_system_prompt(tool_name)
        user_content = {
            "tool": tool_name,
            "params": params,
            "metadata": {
                "investigation_id": task.get("investigation_id") if task else None,
                "task_id": task.get("task_id") if task else None,
            },
        }

        body = {
            "model": self.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_api_key}",
        }

        portkey_config_header = self._portkey_config_header()
        if portkey_config_header:
            headers["x-portkey-config"] = portkey_config_header

        self.logger.debug("Calling LLM for financial tool", extra={"tool": tool_name, "body": body})

        try:
            response = requests.post(self.llm_url, headers=headers, json=body, timeout=60)
        except Exception as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        if not response.ok:
            raise RuntimeError(f"LLM returned {response.status_code}: {response.text}")

        try:
            data = response.json()
            # OpenAI-style responses contain choices[0].message.content
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if not content:
                raise ValueError("missing content")
            return json.loads(content)
        except Exception as exc:
            raise RuntimeError("Failed to parse LLM JSON response") from exc

    def _build_system_prompt(self, tool_name: str) -> str:
        """Craft tool-specific instructions with required schema hints."""

        contract_notes = {
            "analyze_balance_sheet": "Return total_assets, total_liabilities, total_equity, debt, cash_and_equivalents (ints in INR paise), debt_growth_yoy_percent, assets_growth_yoy_percent (floats), anomalies (list[str]), source_documents (list[str]).",
            "calculate_financial_ratios": "Return ratios{debt_to_equity,current_ratio,interest_coverage,return_on_equity,asset_turnover}, historical_comparison{debt_to_equity_2yr_avg,current_ratio_2yr_avg}, anomalies (list[str]), source_documents (list[str]).",
            "detect_cash_flow_divergence": "Return ebitda, operating_cash_flow (ints INR paise), ebitda_growth_percent, operating_cash_flow_growth_percent, divergence_detected (bool), divergence_magnitude_percent (float), severity (critical|high|medium|low), explanation (str), source_documents (list[str]).",
            "detect_related_party_transactions": "Return related_party_transactions (list of counterparty, amount int INR paise, transaction_type, disclosed bool, suspicious bool, reason), total_undisclosed_amount (int), source_documents (list[str]).",
        }

        base_rules = [
            "You are the Financial Agent. Output JSON only.",
            "Monetary values are integers in INR paise (no floats).",
            "Dates must be ISO 8601 if present.",
        ]

        return " \n".join(base_rules + [contract_notes.get(tool_name, "Follow the contract schema strictly.")])

    def _model_from_portkey_config(self) -> Optional[str]:
        """Extract model from PORTKEY_CONFIG if present (JSON or key:value text)."""

        if not self.portkey_config:
            return None

        config_text = self.portkey_config.strip()
        try:
            data = json.loads(config_text)
            if isinstance(data, dict):
                model = data.get("model")
                if isinstance(model, str) and model.strip():
                    return model.strip()
        except Exception:
            pass

        match = re.search(r"model\s*[:=]\s*[\"']?([\w.-]+)", config_text)
        if match:
            return match.group(1)
        return None

    def _portkey_config_header(self) -> Optional[str]:
        """Return the x-portkey-config header value, injecting api_key when needed."""

        if not self.portkey_config:
            return None

        config_text = self.portkey_config.strip()
        try:
            data = json.loads(config_text)
            if isinstance(data, dict):
                if data.get("provider") and not data.get("api_key") and self.gemini_api_key:
                    data["api_key"] = self.gemini_api_key
                return json.dumps(data)
        except Exception:
            pass

        return self.portkey_config


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        repo_root = Path(__file__).resolve().parents[4]
        load_dotenv(repo_root / ".env", override=False)
    except Exception:
        pass

    agent = FinancialAgent()

    sample_tasks = [
        {
            "tool": "analyze_balance_sheet",
            "params": {
                "company_ticker": "RELIANCE.NS",
                "period": "Q3-2024",
                "comparison_periods": ["Q2-2024", "Q3-2023"],
            },
            "investigation_id": "test-investigation-001",
            "task_id": "task-001",
        },
        {
            "tool": "calculate_financial_ratios",
            "params": {
                "company_ticker": "RELIANCE.NS",
                "period": "Q3-2024",
                "comparison_periods": ["Q2-2024", "Q3-2023"],
            },
            "investigation_id": "test-investigation-001",
            "task_id": "task-002",
        },
        {
            "tool": "detect_cash_flow_divergence",
            "params": {
                "company_ticker": "RELIANCE.NS",
                "period": "Q3-2024",
            },
            "investigation_id": "test-investigation-001",
            "task_id": "task-003",
        },
        {
            "tool": "detect_related_party_transactions",
            "params": {
                "company_ticker": "RELIANCE.NS",
                "period": "Q3-2024",
            },
            "investigation_id": "test-investigation-001",
            "task_id": "task-004",
        },
    ]

    for task in sample_tasks:
        result = agent.process(task)
        print(f"\nTool: {task['tool']}")
        print(json.dumps(result, indent=2))
