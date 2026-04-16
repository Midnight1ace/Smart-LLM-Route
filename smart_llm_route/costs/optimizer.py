from typing import Optional
from ..models.registry import ModelRegistry, ModelMetadata
from .tracker import CostTracker, BudgetPeriod

class CostOptimizer:
    def __init__(self, registry: ModelRegistry, tracker: CostTracker):
        self.registry = registry
        self.tracker = tracker

    def select_cheapest_model(
        self, 
        task_type: str, 
        min_quality: float = 0.3
    ) -> Optional[ModelMetadata]:
        candidates = self.registry.list_models_by_capability(task_type)
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x.cost_per_1k)
        
        for model in candidates:
            budget_status = self.check_model_budget_fit(model.cost_per_1k)
            if budget_status.get("within_budget"):
                return model
        
        return candidates[0]

    def check_model_budget_fit(self, cost: float) -> dict:
        return self.tracker.check_budget()

    def suggest_cost_reduction(self) -> list:
        suggestions = []
        
        total = self.tracker.get_total_spending()
        if total > 10:
            suggestions.append("Consider using smaller models for simple tasks")
            suggestions.append("Add more budget limits")
        
        model_spending = self.tracker.get_model_spending()
        expensive_models = [m for m, c in model_spending.items() if c > 0 and 
                       any(model.cost_per_1k > 0.01 for model in self.registry.models.values() 
                           if model.name == m)]
        
        if expensive_models:
            suggestions.append(f"High spend on: {', '.join(expensive_models)}")
        
        return suggestions