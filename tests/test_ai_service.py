from app.schemas import Task
from app.services.ai_service import AIService


def test_estimate_effort_reasonable_range() -> None:
    service = AIService()
    task = Task(title="Prepare board deck", description="Draft KPI summary and strategic narrative")
    minutes, confidence = service.estimate_effort(task)

    assert 20 <= minutes <= 480
    assert 0.35 <= confidence <= 0.92
