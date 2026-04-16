from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ModelMetadata:
    name: str
    provider: str
    cost_per_1k: float
    capabilities: List[str]

class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, ModelMetadata] = {}

    def register_model(self, name: str, provider: str, cost: float, capabilities: List[str]):
        self.models[name] = ModelMetadata(
            name=name, 
            provider=provider, 
            cost_per_1k=cost, 
            capabilities=capabilities
        )

    def get_model(self, name: str) -> Optional[ModelMetadata]:
        return self.models.get(name)

    def list_models_by_capability(self, capability: str) -> List[ModelMetadata]:
        return [m for m in self.models.values() if capability in m.capabilities]
    
    def list_all_models(self) -> List[ModelMetadata]:
        return list(self.models.values())