from app.services.ai_service import AIService
from app.services.behavior_service import BehaviorService
from app.services.realtime import ConnectionManager
from app.services.task_service import TaskService


task_service = TaskService()
ai_service = AIService()
behavior_service = BehaviorService()
realtime_manager = ConnectionManager()
