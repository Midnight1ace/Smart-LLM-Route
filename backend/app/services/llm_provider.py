import asyncio
from typing import List, Dict

from anthropic import AsyncAnthropic
from app.core.config import get_settings
from openai import AsyncOpenAI

MODEL_COSTS = {
    "gpt-4o": {"input": 5.0, "output": 15.0},      # per 1M tokens
    "gpt-4o-mini": {"input": 0.15, "output": 0.6}, # per 1M tokens
    "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
}

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    sleep = (backoff_in_seconds * 2 ** x)
                    await asyncio.sleep(sleep)
                    x += 1
        return wrapper
    return decorator

class LLMProvider:
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.anthropic_client = AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)

    @retry_with_backoff()
    async def complete(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        if "gpt" in model:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        elif "claude" in model:
            system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
            user_messages = [m for m in messages if m["role"] != "system"]
            
            response = await self.anthropic_client.messages.create(
                model=model,
                system=system_msg,
                messages=user_messages,
                max_tokens=1024,
                **kwargs
            )
            return response.content[0].text
        else:
            return f"Model {model} not supported in this demo provider."

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        costs = MODEL_COSTS.get(model, {"input": 0, "output": 0})
        return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000

llm_provider = LLMProvider()

def get_llm_provider():
    return llm_provider
