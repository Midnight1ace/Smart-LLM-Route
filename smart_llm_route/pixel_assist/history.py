import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .session import ChatSession, SessionManager


class ChatHistory:
    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".pixel_assist" / "history"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_manager = SessionManager()
        self._load_all_sessions()

    def _get_session_file(self, session_id: str) -> Path:
        return self.storage_path / f"{session_id}.json"

    def _load_all_sessions(self):
        for file in self.storage_path.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    session = ChatSession.from_dict(data)
                    self.session_manager.sessions[session.id] = session
            except (json.JSONDecodeError, KeyError):
                pass

    def save_session(self, session: ChatSession) -> bool:
        try:
            file_path = self._get_session_file(session.id)
            with open(file_path, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load_session(self, session_id: str) -> Optional[ChatSession]:
        file_path = self._get_session_file(session_id)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return ChatSession.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def delete_session(self, session_id: str) -> bool:
        file_path = self._get_session_file(session_id)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        sessions = self.session_manager.get_recent_sessions(limit)
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at,
                "last_active": s.last_active,
                "message_count": len(s.messages)
            }
            for s in sessions
        ]

    def create_new_session(self, title: str = "") -> ChatSession:
        session = self.session_manager.create_session(title)
        self.save_session(session)
        return session

    def search_messages(self, query: str) -> List[Dict[str, Any]]:
        results = []
        query_lower = query.lower()
        
        for session in self.session_manager.list_sessions():
            for msg in session.messages:
                if query_lower in msg.get("content", "").lower():
                    results.append({
                        "session_id": session.id,
                        "session_title": session.title,
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                        "timestamp": msg.get("timestamp")
                    })
        
        return results

    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        session = self.load_session(session_id)
        if not session:
            return None
        
        if format == "json":
            return json.dumps(session.to_dict(), indent=2)
        elif format == "markdown":
            lines = [f"# {session.title or 'Chat'}\n"]
            for msg in session.messages:
                lines.append(f"**{msg['role']}**: {msg['content']}\n")
            return "\n".join(lines)
        
        return None

    def clear_all(self) -> int:
        count = 0
        for file in self.storage_path.glob("*.json"):
            file.unlink()
            count += 1
        self.session_manager.sessions.clear()
        return count
