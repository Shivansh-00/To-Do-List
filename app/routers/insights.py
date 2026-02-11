from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.dependencies import behavior_service, task_service
from app.models import User
from app.schemas import BehaviorInsights

router = APIRouter(prefix="/v1/insights", tags=["insights"])


@router.get("/behavior", response_model=BehaviorInsights)
async def behavior_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return behavior_service.generate_insights(task_service, db, current_user.id)
