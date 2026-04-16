from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CostLimit:
    max_cost_per_request: float = 1.0
    max_cost_per_hour: float = 10.0
    max_cost_per_day: float = 100.0

class CostLimiter:
    def __init__(self, limits: Optional[CostLimit] = None):
        self.limits = limits or CostLimit()
        self.spending: dict = {}
        self.last_reset: dict = {}

    def check_limit(self, client_id: str, estimated_cost: float) -> tuple[bool, str]:
        self._check_resets(client_id)
        
        hourly = self.spending.get(client_id, {}).get('hour', 0)
        daily = self.spending.get(client_id, {}).get('day', 0)
        
        if estimated_cost > self.limits.max_cost_per_request:
            return False, f"Request cost ${estimated_cost:.2f} exceeds limit ${self.limits.max_cost_per_request:.2f}"
        
        if hourly + estimated_cost > self.limits.max_cost_per_hour:
            return False, f"Hourly limit ${self.limits.max_cost_per_hour:.2f} would be exceeded"
        
        if daily + estimated_cost > self.limits.max_cost_per_day:
            return False, f"Daily limit ${self.limits.max_cost_per_day:.2f} would be exceeded"
        
        return True, "OK"

    def record_cost(self, client_id: str, cost: float):
        if client_id not in self.spending:
            self.spending[client_id] = {'hour': 0, 'day': 0}
        
        self.spending[client_id]['hour'] += cost
        self.spending[client_id]['day'] += cost

    def _check_resets(self, client_id: str):
        now = datetime.now()
        
        if client_id not in self.last_reset:
            self.last_reset[client_id] = {'hour': now, 'day': now}
        
        if now - self.last_reset[client_id]['hour'] > timedelta(hours=1):
            self.spending[client_id]['hour'] = 0
            self.last_reset[client_id]['hour'] = now
        
        if now - self.last_reset[client_id]['day'] > timedelta(days=1):
            self.spending[client_id]['day'] = 0
            self.last_reset[client_id]['day'] = now

    def get_remaining(self, client_id: str) -> dict:
        self._check_resets(client_id)
        spending = self.spending.get(client_id, {'hour': 0, 'day': 0})
        
        return {
            'request_remaining': self.limits.max_cost_per_request,
            'hourly_remaining': max(0, self.limits.max_cost_per_hour - spending['hour']),
            'daily_remaining': max(0, self.limits.max_cost_per_day - spending['day'])
        }

    def reset_client(self, client_id: str):
        if client_id in self.spending:
            self.spending[client_id] = {'hour': 0, 'day': 0}