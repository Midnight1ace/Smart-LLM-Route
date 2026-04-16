import json
from pathlib import Path
from typing import Optional
from .tracker import RequestRecord, FeedbackType
from datetime import datetime

class LearningMemory:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or ".smart_llm_route_memory.json"
        self.records: list[dict] = []
        self._load()

    def _load(self):
        path = Path(self.storage_path)
        if path.exists():
            with open(path) as f:
                self.records = json.load(f)

    def save(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.records, f, indent=2, default=str)

    def add_record(self, record: RequestRecord):
        self.records.append({
            "id": record.id,
            "task_type": record.task_type,
            "task_description": record.task_description,
            "model": record.model,
            "provider": record.provider,
            "timestamp": record.timestamp.isoformat(),
            "success": record.success,
            "latency_ms": record.latency_ms,
            "cost": record.cost,
            "feedback": record.feedback.value if record.feedback else None
        })
        self.save()

    def get_best_model_for_task(self, task_type: str) -> Optional[str]:
        task_records = [r for r in self.records if r.get("task_type") == task_type]
        if not task_records:
            return None
        
        model_perf = {}
        for r in task_records:
            model = r.get("model")
            if model not in model_perf:
                model_perf[model] = {"success": 0, "total": 0}
            model_perf[model]["total"] += 1
            if r.get("success") or r.get("feedback") == "positive":
                model_perf[model]["success"] += 1
        
        if not model_perf:
            return None
        
        best = max(model_perf.items(), key=lambda x: x[1]["success"] / x[1]["total"] if x[1]["total"] > 0 else 0)
        return best[0]