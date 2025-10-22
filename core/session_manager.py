from typing import Dict, Any, Optional
import uuid

class Session:
    """Represents a single conversation session."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_state_id: Optional[str] = None
        self.variables: Dict[str, Any] = {}
        self.last_user_input: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)

    def set(self, key: str, value: Any):
        self.__setattr__(key, value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "current_state_id": self.current_state_id,
            "variables": self.variables,
            "last_user_input": self.last_user_input,
        }

class SessionManager:
    """Manages all active conversation sessions in memory."""
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def get_session(self, session_id: str) -> Session:
        """

        Retrieves an existing session or creates a new one if it doesn't exist.
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id)
        return self._sessions[session_id]

    def create_session(self) -> Session:
        """Creates a new session with a unique ID."""
        session_id = str(uuid.uuid4())
        session = Session(session_id)
        self._sessions[session_id] = session
        return session

    def clear_session(self, session_id: str):
        """Removes a session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
