from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum

class BudgetPeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class Budget:
    amount: float
    period: BudgetPeriod
    project: Optional[str] = None

class CostTracker:
    def __init__(self):
        self.spending: float = 0.0
        self.spending_by_project: Dict[str, float] = {}
        self.spending_by_model: Dict[str, float] = {}
        self.budgets: Dict[str, Budget] = {}
        self.daily_spending: Dict[str, float] = {}
        self._last_reset = datetime.now()

    def add_cost(self, cost: float, model: str, project: Optional[str] = None):
        self.spending += cost
        self.spending_by_model[model] = self.spending_by_model.get(model, 0.0) + cost
        
        if project:
            self.spending_by_project[project] = self.spending_by_project.get(project, 0.0) + cost
        
        today = datetime.now().date().isoformat()
        self.daily_spending[today] = self.daily_spending.get(today, 0.0) + cost

    def set_budget(self, project: str, amount: float, period: BudgetPeriod = BudgetPeriod.DAILY):
        self.budgets[project] = Budget(amount=amount, period=period, project=project)

    def check_budget(self, project: Optional[str] = None) -> dict:
        if not project or project not in self.budgets:
            return {"within_budget": True, "remaining": float('inf'), "percent_used": 0}
        
        budget = self.budgets[project]
        
        if budget.period == BudgetPeriod.DAILY:
            today = datetime.now().date().isoformat()
            current = self.daily_spending.get(today, 0.0)
        else:
            current = self.spending_by_project.get(project, 0.0)
        
        remaining = budget.amount - current
        percent = (current / budget.amount * 100) if budget.amount > 0 else 0
        
        return {
            "within_budget": remaining >= 0,
            "remaining": remaining,
            "percent_used": percent,
            "budget": budget.amount
        }

    def get_model_spending(self) -> Dict[str, float]:
        return dict(self.spending_by_model)

    def get_total_spending(self) -> float:
        return self.spending