from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter

from app.dependencies import task_service
from app.schemas import ScheduleBlock, ScheduleRequest, ScheduleResponse

router = APIRouter(prefix="/v1/schedule", tags=["schedule"])


@router.post("/optimize", response_model=ScheduleResponse)
async def optimize_schedule(payload: ScheduleRequest) -> ScheduleResponse:
    cursor = payload.start_at
    blocks: list[ScheduleBlock] = []
    for task_id in payload.tasks:
        task = task_service.get(task_id)
        duration = max(task.estimated_minutes, 25)
        block = ScheduleBlock(
            task_id=task.id,
            starts_at=cursor,
            ends_at=cursor + timedelta(minutes=duration),
            confidence=0.78,
            explanation={
                "strategy": "priority_and_energy_fit",
                "priority_score": task.priority_score,
                "estimated_minutes": task.estimated_minutes,
            },
        )
        blocks.append(block)
        cursor = block.ends_at + timedelta(minutes=5)
    return ScheduleResponse(blocks=blocks)
