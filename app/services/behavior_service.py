from __future__ import annotations

from app.schemas import BehaviorInsights
from app.services.task_service import TaskService


class BehaviorService:
    def generate_insights(self, task_service: TaskService) -> BehaviorInsights:
        completion_rate = task_service.completion_rate()
        procrastination_risk = round(max(0.0, 0.9 - completion_rate), 3)
        burnout_risk = round(min(1.0, 0.25 + len(task_service.list_all()) / 100), 3)
        return BehaviorInsights(
            peak_hours=[9, 10, 11, 15],
            procrastination_risk=procrastination_risk,
            burnout_risk=burnout_risk,
            weekly_productivity_forecast=[round(50 + completion_rate * 10 + i * 0.8, 2) for i in range(7)],
        )
