from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import TaskModel
from app.schemas import Task, TaskCreate, TaskStatus, TaskUpdate


class TaskService:
    """Database-backed task service."""

    def create(self, db: Session, payload: TaskCreate, owner_id: str) -> TaskModel:
        tags_json = json.dumps(payload.tags) if payload.tags else "[]"
        task = TaskModel(
            title=payload.title,
            description=payload.description,
            due_at=payload.due_at,
            parent_task_id=payload.parent_task_id,
            tags=tags_json,
            owner_id=owner_id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def list_all(self, db: Session, owner_id: str) -> list[TaskModel]:
        return (
            db.query(TaskModel)
            .filter(TaskModel.owner_id == owner_id)
            .order_by(TaskModel.created_at.desc())
            .all()
        )

    def get(self, db: Session, task_id: str, owner_id: str) -> TaskModel:
        task = (
            db.query(TaskModel)
            .filter(TaskModel.id == task_id, TaskModel.owner_id == owner_id)
            .first()
        )
        if not task:
            raise KeyError(f"Task {task_id} not found")
        return task

    def update(self, db: Session, task_id: str, owner_id: str, payload: TaskUpdate) -> TaskModel:
        task = self.get(db, task_id, owner_id)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "tags":
                setattr(task, field, json.dumps(value))
            elif field == "status":
                setattr(task, field, value.value if hasattr(value, "value") else value)
            else:
                setattr(task, field, value)
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db: Session, task_id: str, owner_id: str) -> None:
        task = self.get(db, task_id, owner_id)
        # Delete children first
        children = (
            db.query(TaskModel)
            .filter(TaskModel.parent_task_id == task_id, TaskModel.owner_id == owner_id)
            .all()
        )
        for child in children:
            db.delete(child)
        db.delete(task)
        db.commit()

    def completion_rate(self, db: Session, owner_id: str) -> float:
        tasks = self.list_all(db, owner_id)
        if not tasks:
            return 0.0
        done = sum(1 for t in tasks if t.status == "done")
        return done / len(tasks)

    def to_schema(self, task: TaskModel) -> Task:
        """Convert a DB model to a Pydantic schema."""
        import json as _json
        tags = _json.loads(task.tags) if task.tags else []
        return Task(
            id=task.id,
            title=task.title,
            description=task.description,
            status=TaskStatus(task.status) if task.status else TaskStatus.TODO,
            priority_score=task.priority_score or 50.0,
            estimated_minutes=task.estimated_minutes or 30,
            due_at=task.due_at,
            predicted_due_at=task.predicted_due_at,
            parent_task_id=task.parent_task_id,
            tags=tags,
            owner_id=task.owner_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
