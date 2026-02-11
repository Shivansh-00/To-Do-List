from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.dependencies import ai_service, task_service
from app.models import User
from app.schemas import TaskBreakdownResponse, TaskEstimationResponse

router = APIRouter(prefix="/v1/tasks", tags=["ai"])


@router.post("/{task_id}/ai-breakdown", response_model=TaskBreakdownResponse)
async def ai_breakdown(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        db_task = task_service.get(db, task_id, current_user.id)
        task = task_service.to_schema(db_task)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TaskBreakdownResponse(task_id=task.id, generated_subtasks=ai_service.generate_subtasks(task))


@router.post("/{task_id}/estimate", response_model=TaskEstimationResponse)
async def estimate_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        db_task = task_service.get(db, task_id, current_user.id)
        task = task_service.to_schema(db_task)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    minutes, confidence = ai_service.estimate_effort(task)
    db_task.estimated_minutes = minutes
    db.commit()
    return TaskEstimationResponse(task_id=task.id, estimated_minutes=minutes, confidence=confidence)
