from __future__ import annotations

from typing import Optional

from app.orchestration.langgraph_workflow import SupervisorState, build_workflow


class Supervisor:
    """Orchestration entrypoint.

    For now, this is a bare LangGraph workflow with Supervisor as the entry node
    and no business logic.
    """

    def __init__(self):
        self._workflow = build_workflow()

    def invoke(self, state: Optional[SupervisorState] = None):
        return self._workflow.invoke(state or {})

    async def ainvoke(self, state: Optional[SupervisorState] = None):
        return await self._workflow.ainvoke(state or {})

    def synthesize(self):
        # Kept for backward-compatibility with the existing stub.
        # Prefer invoke()/ainvoke() going forward.
        return self.invoke({})
