class BaseAgent:
    def process(self, task):
        raise NotImplementedError

    async def aprocess(self, task):
        raise NotImplementedError
