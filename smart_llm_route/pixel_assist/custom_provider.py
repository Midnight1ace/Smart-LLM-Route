from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import aiohttp
import json


class CustomModelProvider:
    """Provider for custom local models (Ollama, LM Studio, etc.)"""
    
    def __init__(self, model_config: dict):
        self.name = model_config["name"]
        self.base_url = model_config.get("base_url", "http://localhost:11434")
        self.api_key = model_config.get("api_key", "")
        self.endpoint = model_config.get("endpoint", "/api/generate")
        self.provider_type = model_config.get("provider", "local")
        self.context_length = model_config.get("context_length", 4096)

    async def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        try:
            url = f"{self.base_url}{self.endpoint}"
            
            if self.provider_type == "ollama" or "/api/generate" in self.endpoint:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                if system_prompt:
                    payload["system"] = system_prompt
                    
            elif self.provider_type == "openai-compatible" or "/v1/chat" in self.endpoint:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False
                }
                
            else:
                payload = {
                    "model": model,
                    "prompt": prompt
                }
            
            headers = {}
            if self.api_key and self.api_key != "none":
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_response(data)
                    else:
                        error_text = await response.text()
                        return {
                            "content": f"Error: Server returned status {response.status}\n{error_text}",
                            "usage": {"total_tokens": 0},
                            "provider": self.provider_type,
                            "model": model
                        }
                        
        except aiohttp.ClientConnectorError:
            return {
                "content": f"Error: Cannot connect to {self.name}. Make sure the server is running at {self.base_url}",
                "usage": {"total_tokens": 0},
                "provider": self.provider_type,
                "model": model
            }
        except Exception as e:
            return {
                "content": f"Error: {str(e)}",
                "usage": {"total_tokens": 0},
                "provider": self.provider_type,
                "model": model
            }

    def _parse_response(self, data: Dict) -> Dict[str, Any]:
        if "response" in data:
            return {
                "content": data["response"],
                "usage": {"total_tokens": data.get("eval_count", 0)},
                "provider": self.provider_type,
                "model": self.name
            }
        elif "choices" in data:
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": {"total_tokens": data.get("usage", {}).get("total_tokens", 0)},
                "provider": self.provider_type,
                "model": self.name
            }
        elif "content" in data:
            return {
                "content": data["content"],
                "usage": {"total_tokens": data.get("tokens", 0)},
                "provider": self.provider_type,
                "model": self.name
            }
        else:
            return {
                "content": str(data),
                "usage": {"total_tokens": 0},
                "provider": self.provider_type,
                "model": self.name
            }

    async def list_models(self) -> List[str]:
        try:
            async with aiohttp.ClientSession() as session:
                if "/api/generate" in self.endpoint:
                    async with session.get(f"{self.base_url}/api/tags") as response:
                        if response.status == 200:
                            data = await response.json()
                            return [m["name"] for m in data.get("models", [])]
                elif "/v1" in self.endpoint:
                    async with session.get(f"{self.base_url}/v1/models") as response:
                        if response.status == 200:
                            data = await response.json()
                            return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        return []


class ModelRegistry:
    """Registry for all available models including custom ones"""
    
    def __init__(self):
        self._providers: Dict[str, CustomModelProvider] = {}
        self._models: Dict[str, dict] = {}
    
    def register_model(self, name: str, config: dict):
        self._models[name] = config
        if config.get("base_url"):
            self._providers[name] = CustomModelProvider(config)
    
    def get_provider(self, model_name: str) -> Optional[CustomModelProvider]:
        return self._providers.get(model_name)
    
    def get_model_config(self, model_name: str) -> Optional[dict]:
        return self._models.get(model_name)
    
    def list_models(self) -> List[dict]:
        return [
            {"name": name, **config} 
            for name, config in self._models.items()
        ]
    
    def unregister_model(self, name: str) -> bool:
        if name in self._models:
            del self._models[name]
            self._providers.pop(name, None)
            return True
        return False


_registry = ModelRegistry()


def get_registry() -> ModelRegistry:
    return _registry


def register_model(name: str, config: dict):
    _registry.register_model(name, config)


def get_model_provider(name: str) -> Optional[CustomModelProvider]:
    return _registry.get_provider(name)
