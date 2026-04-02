from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.todo import Todo
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate


def get_comments(db: Session, todo_id: int) -> list[Comment] | None:
    """None이면 Todo가 존재하지 않음."""
    if db.get(Todo, todo_id) is None:
        return None
    return list(
        db.execute(select(Comment).where(Comment.todo_id == todo_id)).scalars().all()
    )


def get_comment(db: Session, comment_id: int) -> Comment | None:
    return db.get(Comment, comment_id)


def create_comment(db: Session, todo_id: int, data: CommentCreate) -> Comment:
    if db.get(Todo, todo_id) is None:
        raise ValueError("Todo not found")
    if db.get(User, data.author_id) is None:
        raise ValueError("User not found")
    comment = Comment(todo_id=todo_id, author_id=data.author_id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db: Session, comment_id: int, data: CommentUpdate) -> Comment | None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        return None
    comment.content = data.content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int) -> bool:
    comment = db.get(Comment, comment_id)
    if comment is None:
        return False
    db.delete(comment)
    db.commit()
    return True
