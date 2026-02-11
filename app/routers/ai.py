from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.dependencies import ai_service, task_service
from app.schemas import TaskBreakdownResponse, TaskEstimationResponse

router = APIRouter(prefix="/v1/tasks", tags=["ai"])


@router.post("/{task_id}/ai-breakdown", response_model=TaskBreakdownResponse)
async def ai_breakdown(task_id: str) -> TaskBreakdownResponse:
    try:
        task = task_service.get(task_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TaskBreakdownResponse(task_id=task.id, generated_subtasks=ai_service.generate_subtasks(task))


@router.post("/{task_id}/estimate", response_model=TaskEstimationResponse)
async def estimate_task(task_id: str) -> TaskEstimationResponse:
    try:
        task = task_service.get(task_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    minutes, confidence = ai_service.estimate_effort(task)
    task.estimated_minutes = minutes
    return TaskEstimationResponse(task_id=task.id, estimated_minutes=minutes, confidence=confidence)
