from typing import Optional
from ..models.registry import ModelRegistry, ModelMetadata
from .tracker import PerformanceTracker
from .memory import LearningMemory

class RouteOptimizer:
    def __init__(self, registry: ModelRegistry, tracker: PerformanceTracker, memory: Optional[LearningMemory] = None):
        self.registry = registry
        self.tracker = tracker
        self.memory = memory

    def select_optimal_model(
        self, 
        task_type: str, 
        max_budget: float,
        min_success_rate: float = 0.5
    ) -> Optional[ModelMetadata]:
        candidates = self.registry.list_models_by_capability(task_type)
        
        if not candidates:
            return None
        
        model_scores = self._get_task_scores(task_type)
        
        if not model_scores:
            return self._select_by_cost(candidates, max_budget)
        
        best_candidates = []
        for model in candidates:
            score = model_scores.get(model.name, {}).get("rate", 0.5)
            if score >= min_success_rate and model.cost_per_1k <= max_budget:
                best_candidates.append((model, score))
        
        if not best_candidates:
            return self._select_by_cost(candidates, max_budget)
        
        best_candidates.sort(key=lambda x: (x[1], -x[0].cost_per_1k), reverse=True)
        return best_candidates[0][0]

    def _get_task_scores(self, task_type: str) -> dict:
        task_perf = self.tracker.get_task_performance(task_type)
        model_scores = task_perf.get("model_scores", {})
        
        if model_scores:
            return model_scores
        
        if self.memory:
            task_records = [r for r in self.memory.records if r.get("task_type") == task_type]
            if not task_records:
                return {}
            
            model_scores = {}
            for r in task_records:
                model = r.get("model")
                if model not in model_scores:
                    model_scores[model] = {"success": 0, "total": 0}
                model_scores[model]["total"] += 1
                if r.get("success") or r.get("feedback") == "positive":
                    model_scores[model]["success"] += 1
            
            for model in model_scores:
                model_scores[model]["rate"] = model_scores[model]["success"] / model_scores[model]["total"]
        
        return model_scores

    def _select_by_cost(
        self, 
        candidates: list[ModelMetadata], 
        max_budget: float
    ) -> Optional[ModelMetadata]:
        affordable = [m for m in candidates if m.cost_per_1k <= max_budget]
        if not affordable:
            return min(candidates, key=lambda x: x.cost_per_1k)
        return min(affordable, key=lambda x: x.cost_per_1k)