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
from typing import Any, Callable, Dict, Optional

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...shared.llm_portkey import chat_complete


class FinancialAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)

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
    # Internal helper: call LLM via Portkey and return JSON per contract
    # ------------------------------------------------------------------
    def _call_llm(
        self,
        tool_name: str,
        params: Dict[str, Any],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a structured prompt to the LLM via Portkey and parse JSON output.

        The LLM is expected to return a JSON object matching the tool contract.
        Raises RuntimeError on HTTP or parsing issues.
        """

        system_prompt = self._build_system_prompt(tool_name)
        user_content = {
            "tool": tool_name,
            "params": params,
            "metadata": {
                "investigation_id": task.get("investigation_id") if task else None,
                "task_id": task.get("task_id") if task else None,
            },
        }

        self.logger.debug("Calling LLM for financial tool", extra={"tool": tool_name})

        try:
            result = chat_complete(
                user_prompt=json.dumps(user_content),
                system_prompt=system_prompt,
                temperature=0.2,
                metadata={"agent": "financial", "tool": tool_name},
            )
            content = result.get("content")
            if not content:
                raise ValueError("missing content")
            return json.loads(content)
        except Exception as exc:
            raise RuntimeError(f"Financial LLM call failed: {exc}") from exc

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
