"""In-memory service layer for branches module."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass
class Branch:
    id: str
    code: str
    name: str
    address: str
    is_active: bool


class BranchService:
    def __init__(self) -> None:
        self._by_id: dict[str, Branch] = {}
        self._ids_by_code: dict[str, str] = {}
        self._seq = 0
        self._lock = RLock()

    def list_branches(self) -> list[Branch]:
        with self._lock:
            return [Branch(**vars(item)) for item in self._by_id.values()]

    def create_branch(self, *, code: str, name: str, address: str, is_active: bool) -> Branch:
        with self._lock:
            if code in self._ids_by_code:
                raise ValueError("branch code already exists")
            self._seq += 1
            branch_id = f"br-{self._seq:04d}"
            branch = Branch(id=branch_id, code=code, name=name, address=address, is_active=is_active)
            self._by_id[branch_id] = branch
            self._ids_by_code[code] = branch_id
            return Branch(**vars(branch))

    def get_branch(self, branch_id: str) -> Branch:
        with self._lock:
            if branch_id not in self._by_id:
                raise KeyError("branch not found")
            return Branch(**vars(self._by_id[branch_id]))

    def update_branch(self, branch_id: str, *, name: str | None, address: str | None, is_active: bool | None) -> Branch:
        with self._lock:
            if branch_id not in self._by_id:
                raise KeyError("branch not found")
            branch = self._by_id[branch_id]
            if name is not None:
                branch.name = name
            if address is not None:
                branch.address = address
            if is_active is not None:
                branch.is_active = is_active
            return Branch(**vars(branch))

    def delete_branch(self, branch_id: str) -> None:
        with self._lock:
            branch = self.get_branch(branch_id)
            del self._by_id[branch_id]
            del self._ids_by_code[branch.code]

    def reset_state(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._ids_by_code.clear()
            self._seq = 0


branch_service = BranchService()
