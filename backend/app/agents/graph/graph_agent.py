"""Graph agent implementation aligned with contract specs.

This agent exposes contract-aligned tool handlers:
- generate_cypher_query
- run_cypher_query
- detect_circular_loops

`process` expects a task dict of the shape:
{
    "tool": "generate_cypher_query" | "run_cypher_query" | "detect_circular_loops",
    "params": { ... }  # matches the contract for that tool
}
It routes to the corresponding handler and returns the tool's output dict.
"""

import json
from typing import Any, Callable, Dict, List, Optional

from neo4j import GraphDatabase
from tenacity import retry, wait_exponential, stop_after_attempt

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger
from ...shared.llm_portkey import chat_complete
from ...core.config import settings


class GraphAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)

        # Initialize Neo4j driver
        neo4j_uri = settings.NEO4J_URI
        neo4j_username = settings.NEO4J_USERNAME
        neo4j_password = settings.NEO4J_PASSWORD
        if neo4j_uri and neo4j_username and neo4j_password:
            self.neo4j_driver = GraphDatabase.driver(
                neo4j_uri, auth=(neo4j_username, neo4j_password)
            )
        else:
            self.neo4j_driver = None
            self.logger.warning(
                "Neo4j credentials not found, graph queries will be limited"
            )

        self.tool_map: Dict[
            str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]
        ] = {
            "generate_cypher_query": self.generate_cypher_query,
            "run_cypher_query": self.run_cypher_query,
            "detect_circular_loops": self.detect_circular_loops,
        }

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=5),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def get_graph_payload(self, entity_name: str, max_hops: int = 5) -> Dict[str, Any]:
        """Return Neo4j subgraph as serializable node/edge objects for UI rendering."""
        if not self.neo4j_driver:
            return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

        query = """
        MATCH path = (start:Company {name: $name})-[:TRANSACTS_WITH*1..{max_hops}]->(end:Company)
        WHERE start <> end
        WITH nodes(path) AS ns, relationships(path) AS rels
        RETURN
            [n IN ns | {
                id: toString(id(n)),
                label: coalesce(n.name, toString(id(n))),
                type: CASE WHEN coalesce(n.risk_score, 0) >= 7 THEN 'suspicious' ELSE 'entity' END,
                risk: coalesce(n.risk_score, 0),
                amount: coalesce(n.total_transaction_amount, 0)
            }] AS nodes,
            [r IN rels | {
                source: toString(startNode(r).name),
                target: toString(endNode(r).name),
                amount: coalesce(r.amount, r.transaction_amount, 0),
                date: toString(coalesce(r.date, r.transaction_date, '')),
                suspicious: coalesce(r.is_suspicious, false)
            }] AS edges
        LIMIT 200
        """.replace(
            "{max_hops}", str(max_hops)
        )

        with self.neo4j_driver.session() as session:
            result = session.run(query, name=entity_name)
            all_nodes: Dict[str, Dict[str, Any]] = {}
            all_edges: List[Dict[str, Any]] = []

            for record in result:
                for node in record["nodes"] or []:
                    all_nodes[node["id"]] = node
                for edge in record["edges"] or []:
                    all_edges.append(
                        {
                            "from": edge.get("source"),
                            "to": edge.get("target"),
                            "amount": edge.get("amount", 0),
                            "suspicious": bool(edge.get("suspicious", False)),
                            "label": (
                                f"₹{edge.get('amount', 0)} Cr"
                                if edge.get("amount")
                                else ""
                            ),
                        }
                    )

            return {
                "nodes": list(all_nodes.values()),
                "edges": all_edges,
                "node_count": len(all_nodes),
                "edge_count": len(all_edges),
            }

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route the incoming task to the correct graph tool.

        Expected task keys: tool (str), params (dict).
        Raises ValueError for unknown tools or missing params.
        """

        tool_name = task.get("tool")
        params = task.get("params", {})

        if not tool_name:
            raise ValueError("GraphAgent task missing 'tool'")
        if tool_name not in self.tool_map:
            raise ValueError(f"Unsupported graph tool: {tool_name}")
        if not isinstance(params, dict):
            raise ValueError("GraphAgent task 'params' must be a dict")

        self.logger.debug(
            "Running graph tool", extra={"tool": tool_name, "params": params}
        )
        return self.tool_map[tool_name](params, task)

    # ---------------------------------------------------------------------
    # Tool implementations (contract-compliant shapes)
    # ---------------------------------------------------------------------
    def generate_cypher_query(
        self, params: Dict[str, Any], task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Converts a natural language investigation goal into a Cypher query."""
        entity_name = params.get("entity_name")
        query_type = params.get("query_type")
        max_hops = params.get("max_hops", 5)
        min_transaction_amount = params.get("min_transaction_amount", 0)

        if not entity_name:
            raise ValueError("generate_cypher_query requires 'entity_name' parameter")
        if not query_type:
            raise ValueError("generate_cypher_query requires 'query_type' parameter")

        # Use LLM to generate the Cypher query
        return self._call_llm("generate_cypher_query", params, task)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=5),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def run_cypher_query(
        self, params: Dict[str, Any], task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes a Cypher query against Neo4j and returns structured results."""
        query = params.get("query")
        query_params = params.get("params", {})

        if not query:
            raise ValueError("run_cypher_query requires 'query' parameter")

        if not self.neo4j_driver:
            raise RuntimeError("Neo4j not configured. Cannot run Cypher query.")

        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query, query_params)
                records = []
                for record in result:
                    # Convert Neo4j record to dict, handling special objects
                    record_dict = {}
                    for key, value in record.items():
                        if hasattr(value, "nodes") and hasattr(value, "relationships"):
                            # This is a Path object - extract nodes and relationships
                            path_data = {
                                "nodes": [
                                    self._serialize_node(node) for node in value.nodes
                                ],
                                "relationships": [
                                    {
                                        "type": rel.type,
                                        "start_node_id": rel.start_node.id,
                                        "end_node_id": rel.end_node.id,
                                        "properties": {
                                            k: self._serialize_value(v)
                                            for k, v in dict(rel).items()
                                        },
                                    }
                                    for rel in value.relationships
                                ],
                            }
                            record_dict[key] = path_data
                        elif hasattr(value, "id") and hasattr(value, "labels"):
                            # This is a Node object
                            record_dict[key] = self._serialize_node(value)
                        else:
                            record_dict[key] = self._serialize_value(value)
                    records.append(record_dict)

                return {"results": records, "result_count": len(records)}
        except Exception as e:
            self.logger.error(f"Cypher query failed: {e}")
            return {"results": [], "result_count": 0, "error": str(e)}

    def detect_circular_loops(
        self, params: Dict[str, Any], task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """High-level tool that combines Cypher generation, execution, and validation."""
        entity_name = params.get("entity_name")
        max_hops = params.get("max_hops", 5)
        min_transaction_amount = params.get("min_transaction_amount", 0)

        if not entity_name:
            raise ValueError("detect_circular_loops requires 'entity_name' parameter")

        # Use a direct, working Cypher query for circular loops instead of LLM-generated one
        # This detects circular trading patterns starting with the specified entity (A -> B -> C -> A)
        # Entity matching is case-insensitive to handle variations
        cypher_query = f"""
        MATCH p = (start:Company)-[r1:TRANSACTS_WITH*1..{max_hops}]->(start)
        WHERE toLower(start.name) CONTAINS toLower($entity_name) OR toLower(start.id) CONTAINS toLower($entity_name)
        WITH p, start, reduce(total = 0, rel IN relationships(p) | total + coalesce(rel.amount, 0)) as total_amount
        WHERE total_amount >= $min_amount
        RETURN
            [n IN nodes(p) | n.name] as company_path,
            [n IN nodes(p) | n.id] as company_ids,
            [rel IN relationships(p) | rel.amount] as amounts,
            [rel IN relationships(p) | rel.date] as dates,
            total_amount as total_circular_amount,
            length(p) as path_length
        LIMIT 20
        """

        # Run the query
        run_params = {
            "query": cypher_query,
            "params": {
                "entity_name": entity_name,
                "min_amount": min_transaction_amount,
            },
        }
        run_result = self.run_cypher_query(run_params, task)
        results = run_result.get("results", [])

        # Process results into contract format
        loops_found = []
        total_circular_amount = 0

        for record in results:
            company_path = record.get("company_path", [])
            amounts = record.get("amounts", [])
            dates = record.get("dates", [])
            total_amount = record.get("total_circular_amount", 0)
            path_length = record.get("path_length", 0)

            if company_path and len(company_path) > 2:
                loops_found.append(
                    {
                        "companies": company_path,
                        "transaction_amounts": amounts,
                        "transaction_dates": dates,
                        "total_amount": total_amount,
                        "loop_length": path_length,
                        "risk_indicator": (
                            "SUSPICIOUS" if total_amount > 10_000_000_000 else "NOTABLE"
                        ),  # ₹10B threshold
                    }
                )
                total_circular_amount += total_amount

        # Calculate risk score based on findings
        risk_score = 0.0
        if loops_found:
            risk_score = min(
                10.0, 3.0 + len(loops_found) * 1.5
            )  # Higher score for more loops
            # Further increase if large amounts involved
            if total_circular_amount > 50_000_000_000:  # ₹50B+
                risk_score = min(10.0, risk_score + 3.0)

        findings = []
        if loops_found:
            findings.append(
                f"🚨 Detected {len(loops_found)} circular trading pattern(s)"
            )
            findings.append(f"Total circular amount: ₹{total_circular_amount:,.0f}")
            for i, loop in enumerate(loops_found, 1):
                path_str = " → ".join(
                    loop["companies"] + [loop["companies"][0]]
                )  # Show cycle
                findings.append(f"Loop {i}: {path_str} (₹{loop['total_amount']:,.0f})")
        else:
            findings.append("No circular trading loops detected")
            risk_score = 1.0

        return {
            "loops_found": loops_found,
            "total_loop_count": len(loops_found),
            "total_circular_amount": total_circular_amount,
            "risk_score": risk_score,
            "findings": findings,
        }

    def _serialize_node(self, node):
        """Convert a Neo4j Node to a JSON-serializable dict."""
        return {
            "id": node.id,
            "labels": list(node.labels),
            "properties": {k: self._serialize_value(v) for k, v in dict(node).items()},
        }

    def _serialize_value(self, value):
        """Convert Neo4j types to JSON-serializable Python types."""
        from datetime import date, datetime
        from neo4j.time import DateTime, Date, Time

        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            return value
        elif isinstance(value, (date, datetime, Date, DateTime, Time)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return str(value)

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

        self.logger.debug(
            "Calling LLM for graph tool", extra={"tool": tool_name, "params": params}
        )

        try:
            result = chat_complete(
                user_prompt=json.dumps(user_content),
                system_prompt=system_prompt,
                temperature=0.2,
                metadata={"agent": "graph", "tool": tool_name},
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
            "generate_cypher_query": """Generate a valid Cypher query for Neo4j graph database. Return cypher_query (str) and explanation (str).

For circular_loop queries: Find transaction paths that form loops starting and ending at the specified entity_name.
- Use MATCH path = (c:Company {{name: $entity_name}})-[:TRANSACTS_WITH*1..{max_hops}]-(c)
- Filter transactions WHERE ALL(r IN relationships(path) WHERE r.amount > $min_amount)
- Return path and loop_total: reduce(total = 0, r IN relationships(path) | total + r.amount) AS loop_total

Example: MATCH path = (c:Company {{name: $entity_name}})-[:TRANSACTS_WITH*1..5]-(c) WHERE ALL(r IN relationships(path) WHERE r.amount > 10000000000) RETURN path, reduce(total = 0, r IN relationships(path) | total + r.amount) AS loop_total

For ownership_chain: Find ownership relationships.
For transaction_path: Find direct/indirect transaction connections.""",
            "run_cypher_query": "This tool executes Cypher queries. Not for LLM to implement.",
            "detect_circular_loops": "This tool combines query generation and execution. Not for LLM to implement.",
        }

        base_rules = [
            "You are the Graph Agent. Output JSON only.",
            "Follow the contract schema strictly.",
            "For Cypher queries, use proper Neo4j syntax.",
            "Entity names should be matched case-insensitively where possible.",
        ]

        return "\n".join(
            base_rules
            + [contract_notes.get(tool_name, "Follow the contract schema strictly.")]
        )
