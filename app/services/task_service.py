from __future__ import annotations

from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.schemas import Task, TaskCreate, TaskStatus, TaskUpdate


class TaskService:
    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}

    def create(self, payload: TaskCreate) -> Task:
        task = Task(**payload.model_dump())
        self._tasks[task.id] = task
        return task

    def list_all(self) -> list[Task]:
        return sorted(self._tasks.values(), key=lambda t: t.created_at)

    def _normalize_id(self, task_id: UUID | str) -> UUID:
        return task_id if isinstance(task_id, UUID) else UUID(str(task_id))

    def get(self, task_id: UUID | str) -> Task:
        normalized_id = self._normalize_id(task_id)
        task = self._tasks.get(normalized_id)
        if not task:
            raise KeyError(f"Task {task_id} not found")
        return task

    def update(self, task_id: UUID | str, payload: TaskUpdate) -> Task:
        task = self.get(task_id)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = datetime.utcnow()
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: UUID | str) -> None:
        normalized_id = self._normalize_id(task_id)
        self.get(normalized_id)
        child_ids = [task.id for task in self._tasks.values() if task.parent_task_id == normalized_id]
        for child_id in child_ids:
            self.delete(child_id)
        del self._tasks[normalized_id]

    def get_children(self, task_id: UUID) -> list[Task]:
        return [task for task in self._tasks.values() if task.parent_task_id == task_id]

    def completion_rate(self, tasks: Iterable[Task] | None = None) -> float:
        items = list(tasks if tasks is not None else self._tasks.values())
        if not items:
            return 0.0
        done = sum(1 for task in items if task.status == TaskStatus.DONE)
        return done / len(items)
