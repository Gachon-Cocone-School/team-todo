from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter(tags=["comments"])


@router.get("/todos/{todo_id}/comments", response_model=list[CommentResponse])
def list_comments(todo_id: int, db: Session = Depends(get_db)) -> list[Comment]:
    result = crud.comment.get_comments(db, todo_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return result


@router.post(
    "/todos/{todo_id}/comments", response_model=CommentResponse, status_code=201
)
def create_comment(
    todo_id: int, data: CommentCreate, db: Session = Depends(get_db)
) -> object:
    try:
        return crud.comment.create_comment(db, todo_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/comments/{comment_id}", response_model=CommentResponse)
def get_comment(comment_id: int, db: Session = Depends(get_db)) -> object:
    comment = crud.comment.get_comment(db, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int, data: CommentUpdate, db: Session = Depends(get_db)
) -> object:
    comment = crud.comment.update_comment(db, comment_id, data)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


@router.delete("/comments/{comment_id}", status_code=200)
def delete_comment(comment_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    if not crud.comment.delete_comment(db, comment_id):
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"detail": "Comment deleted"}
