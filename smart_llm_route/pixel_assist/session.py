import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    title: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_active = datetime.now().isoformat()

    def update_title(self, title: str):
        self.title = title

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages

    def clear(self):
        self.messages.clear()
        self.last_active = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "title": self.title,
            "messages": self.messages,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatSession":
        session = cls(
            id=data.get("id", str(uuid.uuid4())),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_active=data.get("last_active", datetime.now().isoformat()),
            title=data.get("title", ""),
            messages=data.get("messages", []),
            metadata=data.get("metadata", {})
        )
        return session


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def create_session(self, title: str = "") -> ChatSession:
        session = ChatSession(title=title or f"Chat {len(self.sessions) + 1}")
        self.sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[ChatSession]:
        return list(self.sessions.values())

    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        sorted_sessions = sorted(
            self.sessions.values(),
            key=lambda s: s.last_active,
            reverse=True
        )
        return sorted_sessions[:limit]
