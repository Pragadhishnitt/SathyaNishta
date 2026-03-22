"""Compliance agent implementation aligned with contract specs.

This agent exposes contract-aligned tool handlers:
- check_sebi_regulations
- verify_indas_compliance
- rag_legal_query

`process` expects a task dict of the shape:
{
    "tool": "check_sebi_regulations" | "verify_indas_compliance" | "rag_legal_query",
    "params": { ... }  # matches the contract for that tool
}
It routes to the corresponding handler and returns the tool's output dict.
"""


import json
import os
from typing import Any, Callable, Dict, List, Optional

# Load .env if present (for local dev)
from dotenv import load_dotenv
load_dotenv()

from ...core.config import settings


from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...shared.llm_portkey import chat_complete
from ...core.config import settings


class ComplianceAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)

        # Initialize Supabase client for RAG
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_KEY
        if supabase_url and supabase_key:
            from supabase import create_client, Client
            self.supabase: Optional[Client] = create_client(supabase_url, supabase_key)
        else:
            self.supabase = None
            self.logger.warning("Supabase credentials not found, RAG queries will be limited")



        self.tool_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "check_sebi_regulations": self.check_sebi_regulations,
            "verify_indas_compliance": self.verify_indas_compliance,
            "rag_legal_query": self.rag_legal_query,
        }

        # Initialize Cohere client for embeddings
        try:
            import cohere
            cohere_api_key = getattr(settings, "COHERE_API_KEY", None)
            if cohere_api_key:
                self.cohere_client = cohere.Client(cohere_api_key)
            else:
                self.cohere_client = None
                self.logger.warning("Cohere API key not found in settings, RAG queries will be limited")
        except ImportError:
            self.cohere_client = None
            self.logger.warning("cohere package not installed. Install with: pip install cohere")

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route the incoming task to the correct compliance tool.

        Expected task keys: tool (str), params (dict).
        Raises ValueError for unknown tools or missing params.
        """

        tool_name = task.get("tool")
        params = task.get("params", {})

        if not tool_name:
            raise ValueError("ComplianceAgent task missing 'tool'")
        if tool_name not in self.tool_map:
            raise ValueError(f"Unsupported compliance tool: {tool_name}")
        if not isinstance(params, dict):
            raise ValueError("ComplianceAgent task 'params' must be a dict")

        self.logger.debug("Running compliance tool", extra={"tool": tool_name, "params": params})
        return self.tool_map[tool_name](params, task)

    # ---------------------------------------------------------------------
    # Tool implementations (contract-compliant shapes)
    # ---------------------------------------------------------------------
    def check_sebi_regulations(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a finding against SEBI LODR, Companies Act, and other Indian regulations."""
        return self._call_llm("check_sebi_regulations", params, task)

    def verify_indas_compliance(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-reference financial findings against IndAS accounting standards."""
        return self._call_llm("verify_indas_compliance", params, task)

    def rag_legal_query(self, params: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic search on regulatory documents using Supabase pgvector."""
        query = params.get("query")
        source_filter = params.get("source_filter")
        category_filter = params.get("category_filter")
        top_k = params.get("top_k", 3)

        if not query:
            raise ValueError("rag_legal_query requires 'query' parameter")

        if not self.supabase:
            raise RuntimeError("Supabase not configured. Cannot perform RAG query.")


        try:
            # Use instance cohere_client for embedding
            if self.cohere_client is None:
                raise RuntimeError("Cohere client not initialized. Ensure 'cohere' is installed and COHERE_API_KEY is set in settings.")
            response = self.cohere_client.embed(
                texts=[query],
                model="embed-english-v3.0",
                input_type="search_query"
            )
            query_embedding = response.embeddings[0]  # 1024 dimensions

            # Prepare source filter - map to schema format
            source_array = None
            if source_filter and isinstance(source_filter, list):
                source_map = {
                    "SEBI": "SEBI",
                    "INDAS": "IndAS",
                    "COMPANIES_ACT": "CompaniesAct"
                }
                source_array = [source_map.get(s.upper(), s) for s in source_filter]

            # Call the search_regulatory_documents SQL function
            rpc_params = {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "source_filter": source_array,
                "category_filter": category_filter
            }

            response = self.supabase.rpc('search_regulatory_documents', rpc_params).execute()

            if not response.data:
                return {"results": []}

            # Format results according to contract
            results = []
            for row in response.data:
                results.append({
                    "document_id": str(row.get("id")),
                    "title": row.get("title", ""),
                    "source": row.get("source", ""),
                    "category": row.get("category"),
                    "doc_type": row.get("doc_type"),
                    "relevance_score": float(row.get("similarity", 0.0)),
                    "excerpt": row.get("content_chunk", "")[:200],  # First 200 chars
                    "effective_date": row.get("effective_date"),
                    "url": row.get("url"),
                    "metadata": row.get("metadata", {})
                })

            return {"results": results}

        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")
            return {
                "results": [],
                "error": str(e)
            }

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
        Raises RuntimeError on parsing issues.
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

        self.logger.debug("Calling LLM for compliance tool", extra={"tool": tool_name, "params": params})

        try:
            result = chat_complete(
                user_prompt=json.dumps(user_content),
                system_prompt=system_prompt,
                temperature=0.2,
                metadata={"agent": "compliance", "tool": tool_name},
            )
            content = result.get("content", "").strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)

        except json.JSONDecodeError as exc:
            self.logger.error("Failed to parse LLM JSON response")
            raise RuntimeError(f"Failed to parse LLM JSON response: {exc}") from exc
        except Exception as exc:
            self.logger.error("LLM request failed", extra={"error": str(exc)})
            raise RuntimeError(f"LLM request failed: {exc}") from exc

    def _build_system_prompt(self, tool_name: str) -> str:
        """Craft tool-specific instructions with required schema hints."""

        contract_notes = {
            "check_sebi_regulations": "Analyze against SEBI LODR, Companies Act 2013. Return violations (list with regulation_id, regulation_title, violation_description, severity, penalty_clause), violation_probability (float 0.0-1.0), cited_documents (list[str]).",
            "verify_indas_compliance": "Analyze against IndAS standards. Return indas_violations (list with standard_id, standard_title, violation_description, severity), compliance_score (float 0.0-1.0), cited_documents (list[str]).",
            "rag_legal_query": "Search SEBI/IndAS/Companies Act documents. Return results (list with document_id, title, source, relevance_score float 0.0-1.0, excerpt 100-200 words).",
        }

        base_rules = [
            "You are the Compliance Agent. Output JSON only.",
            "Follow the contract schema strictly.",
            "All dates must be ISO 8601 if present.",
        ]

        return "\n".join(base_rules + [contract_notes.get(tool_name, "Follow the contract schema strictly.")])
