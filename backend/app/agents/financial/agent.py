import asyncio
from typing import Any, Dict

from app.shared.llm_portkey import chat_complete

from ..base_agent import BaseAgent


class FinancialAgent(BaseAgent):
    def process(self, task: Dict[str, Any]):
        prompt = f"""You are a financial investigation assistant.

Analyze the following payload and return:
1) key financial risks
2) suspicious patterns
3) 3 follow-up questions

Payload:
{task}
"""
        result = chat_complete(
            user_prompt=prompt,
            system_prompt="You are a precise financial analyst.",
            temperature=0.2,
            metadata={"agent": "financial"},
        )
        return result["content"]

    async def aprocess(self, task: Dict[str, Any]):
        return await asyncio.to_thread(self.process, task)
