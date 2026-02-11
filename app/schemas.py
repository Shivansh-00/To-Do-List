from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    due_at: datetime | None = None
    parent_task_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    due_at: datetime | None = None
    status: TaskStatus | None = None
    tags: list[str] | None = None


class Task(TaskBase):
    id: UUID = Field(default_factory=uuid4)
    status: TaskStatus = TaskStatus.TODO
    priority_score: float = 50.0
    estimated_minutes: int = 30
    predicted_due_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskBreakdownResponse(BaseModel):
    task_id: UUID
    generated_subtasks: list[str]


class TaskEstimationResponse(BaseModel):
    task_id: UUID
    estimated_minutes: int
    confidence: float


class BehaviorInsights(BaseModel):
    peak_hours: list[int]
    procrastination_risk: float
    burnout_risk: float
    weekly_productivity_forecast: list[float]


class ScheduleBlock(BaseModel):
    task_id: UUID
    starts_at: datetime
    ends_at: datetime
    confidence: float
    explanation: dict[str, Any]


class ScheduleRequest(BaseModel):
    tasks: list[UUID]
    start_at: datetime


class ScheduleResponse(BaseModel):
    blocks: list[ScheduleBlock]


class RealtimeEvent(BaseModel):
    type: str
    payload: dict[str, Any]
