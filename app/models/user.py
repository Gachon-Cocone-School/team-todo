from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.todo import Todo


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    todos_assigned: Mapped[list[Todo]] = relationship(
        "Todo",
        foreign_keys="Todo.assignee_id",
        back_populates="assignee",
        passive_deletes=True,
    )
    todos_created: Mapped[list[Todo]] = relationship(
        "Todo",
        foreign_keys="Todo.created_by",
        back_populates="creator",
    )
    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
