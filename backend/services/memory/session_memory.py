"""
Conversational Memory Service for BharatInsure AI.
Preserves multi-turn conversation context across multiple Indian language switches.
"""

import time
from typing import Dict, List, Optional, Any

class SessionMemory:
    def __init__(self):
        # Maps session_id -> { "messages": [...], "current_category": str, "last_updated": float }
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "current_category": "General Insurance",
                "last_language": "en",
                "last_updated": time.time()
            }
        return self.sessions[session_id]

    def add_turn(self, session_id: str, user_content: str, assistant_content: str, user_lang: str, category: Optional[str] = None):
        session = self.get_or_create_session(session_id)
        
        session["messages"].append({
            "role": "user",
            "content": user_content,
            "language": user_lang,
            "timestamp": time.time()
        })

        session["messages"].append({
            "role": "assistant",
            "content": assistant_content,
            "language": user_lang,
            "timestamp": time.time()
        })

        if category:
            session["current_category"] = category
            
        session["last_language"] = user_lang
        session["last_updated"] = time.time()

        # Keep last 10 turns (20 messages) to prevent context explosion
        if len(session["messages"]) > 20:
            session["messages"] = session["messages"][-20:]

    def get_history(self, session_id: str, limit: int = 6) -> List[Dict[str, Any]]:
        session = self.get_or_create_session(session_id)
        return session["messages"][-limit:]

    def get_current_category(self, session_id: str) -> str:
        session = self.get_or_create_session(session_id)
        return session.get("current_category", "General Insurance")

    def format_history_for_prompt(self, session_id: str, limit: int = 6) -> str:
        history = self.get_history(session_id, limit=limit)
        if not history:
            return "No previous conversation history."

        formatted_lines = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            lang = msg.get("language", "en")
            formatted_lines.append(f"{role} [{lang}]: {msg['content']}")

        return "\n".join(formatted_lines)

    def clear(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

# Singleton instance
session_memory = SessionMemory()
