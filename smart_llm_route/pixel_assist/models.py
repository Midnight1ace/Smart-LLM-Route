import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CustomModel:
    name: str
    provider: str
    base_url: str
    api_key: str
    capabilities: List[str]
    cost_per_1k: float
    description: str
    endpoint: str = "/api/generate"
    context_length: int = 4096


class CustomModelManager:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".pixel_assist" / "models"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.models_file = self.storage_path / "custom_models.json"
        self._load()

    def _load(self):
        if self.models_file.exists():
            try:
                with open(self.models_file, "r") as f:
                    data = json.load(f)
                    self.models = [CustomModel(**m) for m in data]
            except Exception:
                self.models = []
        else:
            self.models = []

    def _save(self):
        with open(self.models_file, "w") as f:
            json.dump([asdict(m) for m in self.models], f, indent=2)

    def add_model(self, model: CustomModel) -> bool:
        if any(m.name == model.name for m in self.models):
            return False
        self.models.append(model)
        self._save()
        return True

    def remove_model(self, name: str) -> bool:
        for i, m in enumerate(self.models):
            if m.name == name:
                self.models.pop(i)
                self._save()
                return True
        return False

    def get_model(self, name: str) -> Optional[CustomModel]:
        for m in self.models:
            if m.name == name:
                return m
        return None

    def list_models(self) -> List[CustomModel]:
        return self.models

    def update_model(self, name: str, **kwargs) -> bool:
        for i, m in enumerate(self.models):
            if m.name == name:
                for key, value in kwargs.items():
                    if hasattr(m, key):
                        setattr(m, key, value)
                self._save()
                return True
        return False


model_manager = CustomModelManager()


def add_ollama_model(name: str, description: str = "", capabilities: List[str] = None):
    if capabilities is None:
        capabilities = ["general", "coding"]
    
    model = CustomModel(
        name=name,
        provider="local",
        base_url="http://localhost:11434",
        api_key="",
        capabilities=capabilities,
        cost_per_1k=0.0,
        description=description or f"Ollama model: {name}",
        endpoint="/api/generate"
    )
    return model_manager.add_model(model)


def add_custom_api_model(
    name: str,
    base_url: str,
    endpoint: str = "/v1/chat/completions",
    api_key: str = "none",
    capabilities: List[str] = None,
    cost_per_1k: float = 0.0,
    description: str = ""
):
    if capabilities is None:
        capabilities = ["general", "coding"]
    
    model = CustomModel(
        name=name,
        provider="custom",
        base_url=base_url,
        api_key=api_key,
        capabilities=capabilities,
        cost_per_1k=cost_per_1k,
        description=description,
        endpoint=endpoint
    )
    return model_manager.add_model(model)
