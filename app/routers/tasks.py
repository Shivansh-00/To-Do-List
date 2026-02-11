from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.dependencies import ai_service, realtime_manager, task_service
from app.models import User
from app.schemas import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
async def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = task_service.list_all(db, current_user.id)
    return [task_service.to_schema(t) for t in tasks]


@router.post("", response_model=Task)
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_task = task_service.create(db, payload, current_user.id)
    task = task_service.to_schema(db_task)
    task.predicted_due_at = ai_service.predict_deadline(task)
    minutes, _ = ai_service.estimate_effort(task)
    task.estimated_minutes = minutes
    # Update DB with AI predictions
    db_task.predicted_due_at = task.predicted_due_at
    db_task.estimated_minutes = minutes
    db.commit()
    await realtime_manager.broadcast({"type": "task.created", "payload": task.model_dump(mode="json")})
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        db_task = task_service.get(db, task_id, current_user.id)
        return task_service.to_schema(db_task)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        db_task = task_service.update(db, task_id, current_user.id, payload)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    task = task_service.to_schema(db_task)
    await realtime_manager.broadcast({"type": "task.updated", "payload": task.model_dump(mode="json")})
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        task_service.delete(db, task_id, current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await realtime_manager.broadcast({"type": "task.deleted", "payload": {"task_id": task_id}})
