from typing import Optional, Dict, Any
from .validator import InputValidator, OutputFilter, ValidationResult
from .rate_limiter import RateLimiter, RateLimitConfig
from .key_manager import KeyManager
from .auth import AuthManager
from .cost_limiter import CostLimiter, CostLimit

class SecurityLayer:
    def __init__(
        self,
        enable_validation: bool = True,
        enable_rate_limiting: bool = True,
        enable_auth: bool = False,
        enable_cost_limits: bool = True,
        rate_config: Optional[RateLimitConfig] = None,
        cost_limits: Optional[CostLimit] = None
    ):
        self.validator = InputValidator() if enable_validation else None
        self.output_filter = OutputFilter() if enable_validation else None
        self.rate_limiter = RateLimiter(rate_config) if enable_rate_limiting else None
        self.key_manager = KeyManager()
        self.auth_manager = AuthManager() if enable_auth else None
        self.cost_limiter = CostLimiter(cost_limits) if enable_cost_limits else None

    def validate_input(self, prompt: str, task_type: str, budget: float) -> ValidationResult:
        if self.validator:
            return self.validator.validate(prompt, task_type, budget)
        return ValidationResult(is_valid=True, sanitized_input=prompt)

    def filter_output(self, output: str) -> str:
        if self.output_filter:
            return self.output_filter.filter(output)
        return output

    def check_rate_limit(self, client_id: str, tokens: int = 0) -> tuple[bool, str]:
        if self.rate_limiter:
            return self.rate_limiter.check_limit(client_id, tokens)
        return True, "OK"

    def check_cost_limit(self, client_id: str, estimated_cost: float) -> tuple[bool, str]:
        if self.cost_limiter:
            return self.cost_limiter.check_limit(client_id, estimated_cost)
        return True, "OK"

    def record_cost(self, client_id: str, cost: float):
        if self.cost_limiter:
            self.cost_limiter.record_cost(client_id, cost)

    def authenticate(self, username: str, password: str) -> Optional[str]:
        if self.auth_manager:
            return self.auth_manager.authenticate(username, password)
        return None

    def verify_token(self, token: str) -> Optional[dict]:
        if self.auth_manager:
            return self.auth_manager.verify_token(token)
        return None

    def get_api_key(self, provider: str) -> Optional[str]:
        return self.key_manager.get_key(provider)

    def has_api_key(self, provider: str) -> bool:
        return self.key_manager.has_key(provider)