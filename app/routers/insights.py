from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import behavior_service, task_service
from app.schemas import BehaviorInsights

router = APIRouter(prefix="/v1/insights", tags=["insights"])


@router.get("/behavior", response_model=BehaviorInsights)
async def behavior_insights() -> BehaviorInsights:
    return behavior_service.generate_insights(task_service)
