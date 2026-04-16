import re
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None
    sanitized_input: Optional[str] = None

class InputValidator:
    MAX_PROMPT_LENGTH = 100000
    MAX_TASK_TYPE_LENGTH = 100
    MAX_BUDGET = 100.0
    
    BLOCKED_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'\$\{',
    ]
    
    def __init__(self):
        self.blocked_regex = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]

    def validate(self, prompt: str, task_type: str, budget: float) -> ValidationResult:
        if not prompt or not prompt.strip():
            return ValidationResult(is_valid=False, error="Prompt cannot be empty")
        
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            return ValidationResult(is_valid=False, error=f"Prompt exceeds max length of {self.MAX_PROMPT_LENGTH}")
        
        if not task_type or not task_type.strip():
            return ValidationResult(is_valid=False, error="Task type cannot be empty")
        
        if len(task_type) > self.MAX_TASK_TYPE_LENGTH:
            return ValidationResult(is_valid=False, error=f"Task type exceeds max length of {self.MAX_TASK_TYPE_LENGTH}")
        
        if budget <= 0 or budget > self.MAX_BUDGET:
            return ValidationResult(is_valid=False, error=f"Budget must be between 0 and {self.MAX_BUDGET}")
        
        sanitized = self._sanitize(prompt)
        
        for regex in self.blocked_regex:
            if regex.search(sanitized):
                return ValidationResult(is_valid=False, error="Input contains blocked patterns")
        
        return ValidationResult(is_valid=True, sanitized_input=sanitized)

    def _sanitize(self, text: str) -> str:
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        return text.strip()

class OutputFilter:
    BLOCKED_PATTERNS = [
        r'api_key["\s]*[=:]["\s]*[a-zA-Z0-9\-_]{20,}',
        r'secret["\s]*[=:]["\s]*[a-zA-Z0-9\-_]{20,}',
        r'password["\s]*[=:]["\s]*\S+',
        r'token["\s]*[=:]["\s]*[a-zA-Z0-9\-_]{20,}',
    ]
    
    def __init__(self):
        self.blocked_regex = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]
        self.redaction = "[REDACTED]"

    def filter(self, output: str) -> str:
        if not output:
            return output
        
        for regex in self.blocked_regex:
            output = regex.sub(f'{self.redaction}', output)
        
        return output
    
    def check_for_secrets(self, text: str) -> bool:
        for regex in self.blocked_regex:
            if regex.search(text):
                return True
        return False