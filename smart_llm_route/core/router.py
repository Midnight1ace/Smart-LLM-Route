import os
import time
from typing import Any, Dict, Optional
from .selector import ModelSelector
from ..models.providers import get_provider
from ..models.registry import ModelRegistry
from ..learning.tracker import PerformanceTracker, FeedbackType, RequestRecord
from ..learning.optimizer import RouteOptimizer
from ..learning.memory import LearningMemory
from ..security.security import SecurityLayer
from ..security.rate_limiter import RateLimitConfig
from ..security.cost_limiter import CostLimit

class SmartRouter:
    def __init__(
        self,
        registry: ModelRegistry,
        use_learning: bool = True,
        security: Optional[SecurityLayer] = None,
        client_id: str = "default"
    ):
        self.registry = registry
        self.selector = ModelSelector(registry)
        self.providers = {}
        self.use_learning = use_learning
        self.client_id = client_id
        self.security = security
        
        if use_learning:
            self.tracker = PerformanceTracker()
            self.memory = LearningMemory()
            self.optimizer = RouteOptimizer(registry, self.tracker, self.memory)
        else:
            self.tracker = None
            self.optimizer = None
            self.memory = None

    async def route(
        self,
        task_description: str,
        task_type: str,
        budget: float = 0.5,
        token: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        if self.security:
            if token:
                auth = self.security.verify_token(token)
                if not auth:
                    raise PermissionError("Invalid or expired token")
            
            validation = self.security.validate_input(task_description, task_type, budget)
            if not validation.is_valid:
                raise ValueError(validation.error)
            
            allowed, msg = self.security.check_rate_limit(self.client_id)
            if not allowed:
                raise Exception(f"Rate limit exceeded: {msg}")
            
            allowed, msg = self.security.check_cost_limit(self.client_id, budget)
            if not allowed:
                raise Exception(f"Cost limit exceeded: {msg}")
        
        start_time = time.time()
        
        if model_override:
            selected_model_meta = self.registry.get_model(model_override)
            if not selected_model_meta:
                raise Exception(f"Model not found: {model_override}")
            if selected_model_meta.cost_per_1k > budget:
                raise Exception(f"Model {model_override} exceeds budget. Cost: {selected_model_meta.cost_per_1k}, Budget: {budget}")
        elif self.use_learning and self.optimizer:
            selected_model_meta = self.optimizer.select_optimal_model(task_type, budget)
        else:
            selected_model_meta = self.selector.select_best_model(task_type, budget)
        
        if not selected_model_meta:
            raise Exception("No suitable model found for the given task and budget.")

        provider_name = selected_model_meta.provider
        
        if self.security:
            api_key = self.security.get_api_key(provider_name)
            if not api_key:
                api_key = "dummy-key-for-testing"
        else:
            api_key = os.getenv(f"{provider_name.upper()}_API_KEY", "dummy-key")
        
        if provider_name not in self.providers:
            self.providers[provider_name] = get_provider(provider_name, api_key)

        provider = self.providers[provider_name]
        response = await provider.generate(selected_model_meta.name, task_description)
        
        if self.security:
            response['content'] = self.security.filter_output(response['content'])
        
        latency_ms = (time.time() - start_time) * 1000
        cost = selected_model_meta.cost_per_1k
        request_id = None
        
        if self.use_learning and self.tracker and self.memory:
            request_id = self.tracker.record_request(
                task_type=task_type,
                task_description=task_description,
                model=selected_model_meta.name,
                provider=provider_name,
                success=True,
                latency_ms=latency_ms,
                cost=cost
            )
            
            if request_id and self.tracker.records:
                last_record = self.tracker.records[-1]
                self.memory.add_record(last_record)
        
        if self.security and cost > 0:
            self.security.record_cost(self.client_id, cost)
        
        return {
            "model": selected_model_meta.name,
            "response": response,
            "request_id": request_id if self.use_learning else None
        }

    def give_feedback(self, request_id: str, feedback: str):
        if not self.use_learning or not self.tracker:
            return
        
        feedback_type = FeedbackType.POSITIVE if feedback == "positive" else FeedbackType.NEGATIVE
        self.tracker.add_feedback(request_id, feedback_type)
        
        for record in self.tracker.records:
            if record.id == request_id:
                if self.memory:
                    self.memory.add_record(record)
                break

    def get_learned_model(self, task_type: str) -> Optional[str]:
        if self.memory:
            return self.memory.get_best_model_for_task(task_type)
        return None

    def get_stats(self) -> Dict[str, Any]:
        if not self.use_learning:
            return {}
        
        in_memory_count = len(self.tracker.records) if self.tracker else 0
        from_memory = len(self.memory.records) if self.memory else 0
        
        model_perf = {}
        if self.memory and self.memory.records:
            for r in self.memory.records:
                model = r.get("model")
                if model not in model_perf:
                    model_perf[model] = {"success": 0, "total": 0, "total_cost": 0.0}
                model_perf[model]["total"] += 1
                model_perf[model]["total_cost"] += r.get("cost", 0)
                if r.get("success") or r.get("feedback") == "positive":
                    model_perf[model]["success"] += 1
            for m in model_perf:
                model_perf[m]["success_rate"] = model_perf[m]["success"] / model_perf[m]["total"]
                model_perf[m]["avg_cost"] = model_perf[m]["total_cost"] / model_perf[m]["total"]
        
        return {
            "total_requests": from_memory,
            "in_memory_requests": in_memory_count,
            "model_performance": model_perf
        }

    def get_rate_limit_status(self) -> Optional[dict]:
        if self.security and self.security.rate_limiter:
            return self.security.rate_limiter.get_remaining(self.client_id)
        return None

    def get_cost_limit_status(self) -> Optional[dict]:
        if self.security and self.security.cost_limiter:
            return self.security.cost_limiter.get_remaining(self.client_id)
        return None