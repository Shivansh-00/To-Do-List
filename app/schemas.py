from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, EmailStr


# ── Auth Schemas ──────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    full_name: str | None = None
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Task Schemas ──────────────────────────────────────────────

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    description: str | None = None
    due_at: datetime | None = None
    parent_task_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    due_at: datetime | None = None
    status: TaskStatus | None = None
    tags: list[str] | None = None
    priority_score: float | None = None


class Task(TaskBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.TODO
    priority_score: float = 50.0
    estimated_minutes: int = 30
    predicted_due_at: datetime | None = None
    owner_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class TaskBreakdownResponse(BaseModel):
    task_id: str
    generated_subtasks: list[str]


class TaskEstimationResponse(BaseModel):
    task_id: str
    estimated_minutes: int
    confidence: float


class BehaviorInsights(BaseModel):
    peak_hours: list[int]
    procrastination_risk: float
    burnout_risk: float
    weekly_productivity_forecast: list[float]


class ScheduleBlock(BaseModel):
    task_id: str
    starts_at: datetime
    ends_at: datetime
    confidence: float
    explanation: dict[str, Any]


class ScheduleRequest(BaseModel):
    tasks: list[str]
    start_at: datetime


class ScheduleResponse(BaseModel):
    blocks: list[ScheduleBlock]


class RealtimeEvent(BaseModel):
    type: str
    payload: dict[str, Any]
