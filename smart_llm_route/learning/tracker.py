from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class FeedbackType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

@dataclass
class RequestRecord:
    id: str
    task_type: str
    task_description: str
    model: str
    provider: str
    timestamp: datetime
    success: bool
    latency_ms: float
    cost: float
    feedback: Optional[FeedbackType] = None

class PerformanceTracker:
    def __init__(self):
        self.records: list[RequestRecord] = []
        self._id_counter = 0

    def record_request(
        self,
        task_type: str,
        task_description: str,
        model: str,
        provider: str,
        success: bool,
        latency_ms: float,
        cost: float
    ) -> str:
        self._id_counter += 1
        record_id = f"req_{self._id_counter}"
        record = RequestRecord(
            id=record_id,
            task_type=task_type,
            task_description=task_description,
            model=model,
            provider=provider,
            timestamp=datetime.now(),
            success=success,
            latency_ms=latency_ms,
            cost=cost
        )
        self.records.append(record)
        return record_id

    def add_feedback(self, request_id: str, feedback: FeedbackType):
        for record in self.records:
            if record.id == request_id:
                record.feedback = feedback
                break

    def get_model_performance(self, model: str) -> dict:
        model_records = [r for r in self.records if r.model == model]
        if not model_records:
            return {"total": 0, "success_rate": 0.0, "avg_cost": 0.0, "avg_latency": 0.0}
        
        total = len(model_records)
        successes = sum(1 for r in model_records if r.success or r.feedback == FeedbackType.POSITIVE)
        total_cost = sum(r.cost for r in model_records)
        total_latency = sum(r.latency_ms for r in model_records)
        
        return {
            "total": total,
            "success_rate": successes / total,
            "avg_cost": total_cost / total,
            "avg_latency": total_latency / total
        }

    def get_task_performance(self, task_type: str) -> dict:
        task_records = [r for r in self.records if r.task_type == task_type]
        if not task_records:
            return {"best_model": None, "model_scores": {}}
        
        model_scores = {}
        for record in task_records:
            if record.model not in model_scores:
                model_scores[record.model] = {"success": 0, "total": 0}
            model_scores[record.model]["total"] += 1
            if record.success or record.feedback == FeedbackType.POSITIVE:
                model_scores[record.model]["success"] += 1
        
        for model in model_scores:
            model_scores[model]["rate"] = model_scores[model]["success"] / model_scores[model]["total"]
        
        best_model = max(model_scores.items(), key=lambda x: x[1]["rate"])[0] if model_scores else None
        
        return {"best_model": best_model, "model_scores": model_scores}