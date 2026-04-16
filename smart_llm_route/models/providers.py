from abc import ABC, abstractmethod
from typing import Any, Dict
import aiohttp
import json

class BaseProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        pass

class OpenAIProvider(BaseProvider):
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        return {
            "content": f"Response from {model} for: {prompt}",
            "usage": {"total_tokens": 100},
            "provider": "openai"
        }

class AnthropicProvider(BaseProvider):
    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        return {
            "content": f"Claude response from {model} for: {prompt}",
            "usage": {"total_tokens": 120},
            "provider": "anthropic"
        }

class LocalProvider(BaseProvider):
    """Generic local model provider (Ollama, LM Studio, etc.)"""
    def __init__(self, api_key: str, base_url: str = "http://localhost:11434"):
        super().__init__(api_key)
        self.base_url = base_url

    async def generate(self, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "content": data.get("response", ""),
                            "usage": {"total_tokens": len(prompt.split()) + len(data.get("response", "").split())},
                            "provider": "local"
                        }
                    else:
                        return {
                            "content": f"Error: Local model server returned status {response.status}",
                            "usage": {"total_tokens": 0},
                            "provider": "local"
                        }
        except aiohttp.ClientConnectorError:
            return {
                "content": "Error: Cannot connect to local model server. Make sure Ollama is running on port 11434",
                "usage": {"total_tokens": 0},
                "provider": "local"
            }
        except Exception as e:
            return {
                "content": f"Error: {str(e)}",
                "usage": {"total_tokens": 0},
                "provider": "local"
            }

    async def list_models(self) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "models": [m["name"] for m in data.get("models", [])]}
                    return {"success": False, "error": f"Status {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def get_provider(provider_name: str, api_key: str, **kwargs) -> BaseProvider:
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "local": LocalProvider
    }
    if provider_name not in providers:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return providers[provider_name](api_key, **kwargs)