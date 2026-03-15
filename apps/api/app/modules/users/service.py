"""In-memory service layer for users module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class User:
    id: str
    username: str
    full_name: str
    role: str
    is_active: bool


class UserService:
    """Application service encapsulating users CRUD rules."""

    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._ids_by_username: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_users(self) -> list[User]:
        with self._lock:
            return [User(**vars(item)) for item in self._by_id.values()]

    def create_user(self, *, username: str, full_name: str, role: str, is_active: bool) -> User:
        with self._lock:
            if username in self._ids_by_username:
                raise ValueError("username already exists")

            self._seq += 1
            user_id = f"usr-{self._seq:04d}"
            user = User(id=user_id, username=username, full_name=full_name, role=role, is_active=is_active)
            self._by_id[user_id] = user
            self._ids_by_username[username] = user_id
            return User(**vars(user))

    def get_user(self, user_id: str) -> User:
        with self._lock:
            if user_id not in self._by_id:
                raise KeyError("user not found")
            return User(**vars(self._by_id[user_id]))

    def update_user(self, user_id: str, *, full_name: str | None, role: str | None, is_active: bool | None) -> User:
        with self._lock:
            if user_id not in self._by_id:
                raise KeyError("user not found")

            user = self._by_id[user_id]
            if full_name is not None:
                user.full_name = full_name
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active

            return User(**vars(user))

    def delete_user(self, user_id: str) -> None:
        with self._lock:
            user = self.get_user(user_id)
            del self._by_id[user_id]
            del self._ids_by_username[user.username]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_username.clear()
            self._seq = 0


user_service = UserService()
