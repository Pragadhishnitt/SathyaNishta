"""Graph agent skeleton — Sprint 1.

Detects circular transaction networks via Neo4j.
Sprint 1 returns mock AgentFinding; real Neo4j queries drop in Sprint 2.
"""

from typing import Any, Dict

from ..base_agent import BaseAgent
from ...shared.logger import setup_logger


class GraphAgent(BaseAgent):
    def __init__(self) -> None:
        self.logger = setup_logger(self.__class__.__name__)

    def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Sprint 1 stub — returns mock circular-trading finding."""
        self.logger.debug("GraphAgent.process called", extra={"task": task})
        return {
            "risk_score": 9.1,
            "findings": [
                "STUB: 3-node circular loop detected",
                "STUB: Total circular flow ₹1,440 Cr in Q3 2024",
                "STUB: Shared director on target + shell company boards",
            ],
            "evidence": {
                "circular_loop": "Adani → Shell A → Shell B → Adani (source: mock)",
                "circular_flow": "₹1,440 Cr (source: mock)",
                "shared_director": "Director X on Adani + Shell A (source: mock)",
            },
        }
