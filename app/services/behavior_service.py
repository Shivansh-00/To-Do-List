from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas import BehaviorInsights
from app.services.task_service import TaskService


class BehaviorService:
    def generate_insights(self, task_service: TaskService, db: Session, owner_id: str) -> BehaviorInsights:
        completion_rate = task_service.completion_rate(db, owner_id)
        all_tasks = task_service.list_all(db, owner_id)
        procrastination_risk = round(max(0.0, 0.9 - completion_rate), 3)
        burnout_risk = round(min(1.0, 0.25 + len(all_tasks) / 100), 3)
        return BehaviorInsights(
            peak_hours=[9, 10, 11, 15],
            procrastination_risk=procrastination_risk,
            burnout_risk=burnout_risk,
            weekly_productivity_forecast=[round(50 + completion_rate * 10 + i * 0.8, 2) for i in range(7)],
        )
