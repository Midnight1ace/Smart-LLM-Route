import hashlib
import secrets
import time
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class User:
    user_id: str
    username: str
    password_hash: str
    role: str = "user"
    created_at: float = 0

class AuthManager:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.tokens: Dict[str, dict] = {}
        self.token_expiry = 3600

    def create_user(self, username: str, password: str, role: str = "user") -> str:
        user_id = secrets.token_hex(16)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.users[username] = User(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            role=role,
            created_at=time.time()
        )
        
        return user_id

    def authenticate(self, username: str, password: str) -> Optional[str]:
        user = self.users.get(username)
        if not user:
            return None
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != user.password_hash:
            return None
        
        return self._create_token(user)

    def _create_token(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'created_at': time.time()
        }
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        token_data = self.tokens.get(token)
        if not token_data:
            return None
        
        if time.time() - token_data['created_at'] > self.token_expiry:
            del self.tokens[token]
            return None
        
        return token_data

    def revoke_token(self, token: str):
        if token in self.tokens:
            del self.tokens[token]

    def require_role(self, token: str, required_role: str) -> bool:
        token_data = self.verify_token(token)
        if not token_data:
            return False
        
        roles = {'admin': 3, 'moderator': 2, 'user': 1}
        user_level = roles.get(token_data.get('role', 'user'), 0)
        required_level = roles.get(required_role, 0)
        
        return user_level >= required_level