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
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client


# Handle imports for both standalone and module usage
if __name__ == "__main__":
    # Standalone mode: adjust path and import directly
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    sys.path.insert(0, str(repo_root / "backend"))
    from app.agents.base_agent import BaseAgent
    from app.shared.logger import setup_logger
else:
    # Module mode: use relative imports
    from ..base_agent import BaseAgent
    from ...shared.logger import setup_logger
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent

# Load environment variables from repo root
load_dotenv(repo_root / ".env.example")


class ComplianceAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)
        # Use Gemini API directly (no Portkey needed)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Initialize Supabase client for RAG
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
        else:
            self.supabase = None
            self.logger.warning("Supabase credentials not found, RAG queries will be limited")
        
        # Initialize embedding model for RAG queries
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Same model used for storing

        self.tool_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "check_sebi_regulations": self.check_sebi_regulations,
            "verify_indas_compliance": self.verify_indas_compliance,
            "rag_legal_query": self.rag_legal_query,
        }

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
        """Perform semantic search on legal documents using Supabase pgvector."""
        query = params.get("query")
        source_filter = params.get("source_filter")
        top_k = params.get("top_k", 3)
        
        if not query:
            raise ValueError("rag_legal_query requires 'query' parameter")
        
        if not self.supabase:
            raise RuntimeError("Supabase not configured. Cannot perform RAG query.")
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Start building query
            query_builder = self.supabase.table('legal_documents').select('*')
            
            # Add source filter if provided
            if source_filter and isinstance(source_filter, list):
                # Convert source_filter to uppercase to match stored format
                uppercase_filters = [s.upper() for s in source_filter]
                # Always include Companies Act when SEBI or IndAS is queried
                if "SEBI" in uppercase_filters or "INDAS" in uppercase_filters:
                    if "COMPANIES_ACT" not in uppercase_filters:
                        uppercase_filters.append("COMPANIES_ACT")
                query_builder = query_builder.in_('source', uppercase_filters)
            
            # Execute query to get all matching documents
            response = query_builder.execute()
            
            if not response.data:
                return {"results": []}
            
            # Calculate cosine similarity manually for each document
            import numpy as np
            
            results_with_similarity = []
            query_vec = np.array(query_embedding, dtype=np.float32)
            
            for row in response.data:
                doc_embedding = row.get('embedding')
                if doc_embedding:
                    # Convert from string to list if needed
                    if isinstance(doc_embedding, str):
                        doc_embedding = json.loads(doc_embedding)
                    
                    doc_vec = np.array(doc_embedding, dtype=np.float32)
                    # Cosine similarity
                    similarity = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))
                    results_with_similarity.append({
                        "id": row.get("id"),
                        "document": row.get("document", ""),
                        "source": row.get("source", ""),
                        "content": row.get("content", ""),
                        "similarity": float(similarity)
                    })
            
            # Sort by similarity descending and take top_k
            results_with_similarity.sort(key=lambda x: x['similarity'], reverse=True)
            top_results = results_with_similarity[:top_k]
            
            # Format results according to contract
            results = []
            for row in top_results:
                results.append({
                    "document_id": str(row["id"]),
                    "title": row["document"],
                    "source": row["source"],
                    "relevance_score": row["similarity"],
                    "excerpt": row["content"][:200]  # First 200 chars
                })
            
            return {"results": results}
        
        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")
            return {
                "results": [],
                "error": str(e)
            }

    # ------------------------------------------------------------------
    # Internal helper: call Gemini and return JSON per contract
    # ------------------------------------------------------------------
    def _call_llm(
        self,
        tool_name: str,
        params: Dict[str, Any],
        task: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a structured prompt to Gemini and parse JSON output.

        The LLM is expected to return a JSON object matching the tool contract.
        Raises RuntimeError on parsing issues.
        """

        if not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")

        system_prompt = self._build_system_prompt(tool_name)
        user_content = {
            "tool": tool_name,
            "params": params,
            "metadata": {
                "investigation_id": task.get("investigation_id") if task else None,
                "task_id": task.get("task_id") if task else None,
            },
        }

        prompt = f"{system_prompt}\n\nTask:\n{json.dumps(user_content, indent=2)}"

        self.logger.debug("Calling Gemini for compliance tool", extra={"tool": tool_name, "params": params})

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(result_text)
        
        except json.JSONDecodeError as exc:
            self.logger.error("Failed to parse Gemini JSON response", extra={"response": response.text})
            raise RuntimeError(f"Failed to parse LLM JSON response: {exc}") from exc
        except Exception as exc:
            self.logger.error("Gemini API call failed", extra={"error": str(exc)})
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
