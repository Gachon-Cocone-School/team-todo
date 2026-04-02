from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.todo import Priority, Status
from app.schemas.tag import TagResponse


class TodoCreate(BaseModel):
    title: str
    description: str | None = None
    status: Status = Status.todo
    priority: Priority = Priority.medium
    due_date: date | None = None
    assignee_id: int | None = None
    created_by: int


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    due_date: date | None = None
    assignee_id: int | None = None


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: Status
    priority: Priority
    due_date: date | None
    assignee_id: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = []

    model_config = ConfigDict(from_attributes=True)
