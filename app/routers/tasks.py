from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.dependencies import ai_service, realtime_manager, task_service
from app.schemas import Task, TaskCreate, TaskUpdate

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
async def list_tasks() -> list[Task]:
    return task_service.list_all()


@router.post("", response_model=Task)
async def create_task(payload: TaskCreate) -> Task:
    task = task_service.create(payload)
    task.predicted_due_at = ai_service.predict_deadline(task)
    minutes, _ = ai_service.estimate_effort(task)
    task.estimated_minutes = minutes
    await realtime_manager.broadcast({"type": "task.created", "payload": task.model_dump(mode="json")})
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    try:
        return task_service.get(task_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{task_id}", response_model=Task)
async def update_task(task_id: str, payload: TaskUpdate) -> Task:
    try:
        task = task_service.update(task_id, payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await realtime_manager.broadcast({"type": "task.updated", "payload": task.model_dump(mode="json")})
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str) -> None:
    try:
        task_service.delete(task_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await realtime_manager.broadcast({"type": "task.deleted", "payload": {"task_id": task_id}})
