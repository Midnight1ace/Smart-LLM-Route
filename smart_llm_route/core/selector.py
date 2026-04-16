from typing import List, Optional
from ..models.registry import ModelRegistry, ModelMetadata

class ModelSelector:
    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def select_best_model(self, task_type: str, max_budget: float) -> Optional[ModelMetadata]:
        candidates = self.registry.list_models_by_capability(task_type)
        
        if not candidates:
            return None
            
        affordable = [m for m in candidates if m.cost_per_1k <= max_budget]
        
        if not affordable:
            return min(candidates, key=lambda x: x.cost_per_1k)

        return max(affordable, key=lambda x: x.cost_per_1k)