from typing import Dict, Any, Optional
import uuid
import threading
import time

class Session:
    """Represents a single conversation session."""
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id  # 关联的用户ID
        self.current_state_id: Optional[str] = None
        self.variables: Dict[str, Any] = {}
        self.last_user_input: Optional[str] = None
        # 保存最近若干轮用户输入，用于LLM意图识别的上下文
        self.user_history: list[str] = []
        self.created_at: float = time.time()  # 会话创建时间
        self.last_active: float = time.time()  # 最后活跃时间

    def get(self, key: str, default: Any = None) -> Any:
        return self.__dict__.get(key, default)

    def set(self, key: str, value: Any):
        self.__setattr__(key, value)
        self.update_activity()  # 更新活跃时间

    def update_activity(self):
        """更新会话最后活跃时间"""
        self.last_active = time.time()

    def is_expired(self, timeout: int = 3600) -> bool:
        """
        检查会话是否过期

        Args:
            timeout: 超时时间（秒），默认3600秒（1小时）

        Returns:
            True表示已过期，False表示未过期
        """
        return (time.time() - self.last_active) > timeout

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_state_id": self.current_state_id,
            "variables": self.variables,
            "last_user_input": self.last_user_input,
            "user_history": self.user_history,
        }

class SessionManager:
    """
    线程安全的会话管理器

    功能：
    1. 管理所有活跃的对话会话
    2. 支持多线程并发访问
    3. 自动清理过期会话
    """
    def __init__(self, session_timeout: int = 3600):
        """
        初始化会话管理器

        Args:
            session_timeout: 会话超时时间（秒），默认3600秒（1小时）
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.RLock()  # 使用可重入锁保护会话字典
        self.session_timeout = session_timeout

    def get_session(self, session_id: str, user_id: Optional[str] = None) -> Session:
        """
        获取或创建会话（线程安全）

        Args:
            session_id: 会话ID
            user_id: 用户ID（可选，用于关联会话与用户）

        Returns:
            Session对象
        """
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = Session(session_id, user_id)
            else:
                # 更新活跃时间
                session = self._sessions[session_id]
                session.update_activity()
                # 如果提供了user_id，更新会话的user_id
                if user_id and not session.user_id:
                    session.user_id = user_id
            return self._sessions[session_id]

    def create_session(self) -> Session:
        """
        创建新会话（线程安全）

        Returns:
            新创建的Session对象
        """
        with self._lock:
            session_id = str(uuid.uuid4())
            session = Session(session_id)
            self._sessions[session_id] = session
            return session

    def clear_session(self, session_id: str):
        """
        删除指定会话（线程安全）

        Args:
            session_id: 会话ID
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def clear_expired_sessions(self) -> int:
        """
        清理所有过期会话（线程安全）

        Returns:
            清理的会话数量
        """
        with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired(self.session_timeout)
            ]
            for sid in expired_ids:
                del self._sessions[sid]
            return len(expired_ids)

    def get_active_session_count(self) -> int:
        """
        获取活跃会话数量（线程安全）

        Returns:
            活跃会话数
        """
        with self._lock:
            return len(self._sessions)

    def get_all_session_ids(self) -> list:
        """
        获取所有会话ID（线程安全）

        Returns:
            会话ID列表
        """
        with self._lock:
            return list(self._sessions.keys())
