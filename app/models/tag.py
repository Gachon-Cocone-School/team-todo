from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.todo import todo_tags

if TYPE_CHECKING:
    from app.models.todo import Todo


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    todos: Mapped[list[Todo]] = relationship(
        "Todo", secondary=todo_tags, back_populates="tags"
    )
