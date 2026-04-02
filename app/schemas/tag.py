from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TagCreate(BaseModel):
    name: str
    color: str | None = None


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagResponse(BaseModel):
    id: int
    name: str
    color: str | None

    model_config = ConfigDict(from_attributes=True)
