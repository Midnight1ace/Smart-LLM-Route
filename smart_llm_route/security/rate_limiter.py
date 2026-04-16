import time
from typing import Dict, Optional
from dataclasses import dataclass
from threading import Lock

@dataclass
class RateLimitConfig:
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    max_tokens_per_day: int = 100000

class RateLimiter:
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self.requests: Dict[str, list] = {}
        self.tokens_today: Dict[str, int] = {}
        self.lock = Lock()
        self._last_reset = time.time()

    def check_limit(self, client_id: str, tokens: int = 0) -> tuple[bool, str]:
        with self.lock:
            self._check_daily_reset()
            
            current_time = time.time()
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            
            if client_id not in self.requests:
                self.requests[client_id] = []
            
            recent_requests = [t for t in self.requests[client_id] if t > minute_ago]
            if len(recent_requests) >= self.config.max_requests_per_minute:
                return False, f"Rate limit: max {self.config.max_requests_per_minute} requests per minute"
            
            hour_requests = [t for t in self.requests[client_id] if t > hour_ago]
            if len(hour_requests) >= self.config.max_requests_per_hour:
                return False, f"Rate limit: max {self.config.max_requests_per_hour} requests per hour"
            
            daily_tokens = self.tokens_today.get(client_id, 0)
            if daily_tokens + tokens > self.config.max_tokens_per_day:
                return False, f"Token limit: max {self.config.max_tokens_per_day} tokens per day"
            
            self.requests[client_id].append(current_time)
            self.tokens_today[client_id] = daily_tokens + tokens
            
            return True, "OK"

    def _check_daily_reset(self):
        current_time = time.time()
        if current_time - self._last_reset > 86400:
            self.tokens_today.clear()
            self._last_reset = current_time

    def get_remaining(self, client_id: str) -> dict:
        with self.lock:
            current_time = time.time()
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            
            requests = self.requests.get(client_id, [])
            recent = len([t for t in requests if t > minute_ago])
            hour_count = len([t for t in requests if t > hour_ago])
            
            daily_tokens = self.tokens_today.get(client_id, 0)
            
            return {
                "requests_per_minute": self.config.max_requests_per_minute - recent,
                "requests_per_hour": self.config.max_requests_per_hour - hour_count,
                "tokens_remaining": self.config.max_tokens_per_day - daily_tokens
            }