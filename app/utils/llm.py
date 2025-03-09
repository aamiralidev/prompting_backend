from typing import List, Dict

class DummyLLM:
    @staticmethod
    async def infer(messages: List[Dict[str, str]]) -> str:
        # This is a dummy implementation
        # In a real application, this would connect to an actual LLM service
        last_message = messages[-1]["content"]
        return f"This is a dummy response to: {last_message}"

llm = DummyLLM() 