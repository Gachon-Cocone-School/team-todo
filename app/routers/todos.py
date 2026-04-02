from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.models.todo import Priority, Status, Todo
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[TodoResponse])
def list_todos(
    status: Status | None = None,
    priority: Priority | None = None,
    assignee_id: int | None = None,
    tag_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Todo]:
    return crud.todo.get_todos(
        db, status=status, priority=priority, assignee_id=assignee_id, tag_id=tag_id
    )


@router.post("", response_model=TodoResponse, status_code=201)
def create_todo(data: TodoCreate, db: Session = Depends(get_db)) -> object:
    try:
        return crud.todo.create_todo(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)) -> object:
    todo = crud.todo.get_todo(db, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    todo_id: int, data: TodoUpdate, db: Session = Depends(get_db)
) -> object:
    try:
        todo = crud.todo.update_todo(db, todo_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=200)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    if not crud.todo.delete_todo(db, todo_id):
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"detail": "Todo deleted"}


@router.post("/{todo_id}/tags/{tag_id}", status_code=200)
def attach_tag(
    todo_id: int, tag_id: int, db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        crud.todo.attach_tag(db, todo_id, tag_id)
    except ValueError as exc:
        msg = str(exc)
        status = 400 if msg == "Tag already attached" else 404
        raise HTTPException(status_code=status, detail=msg) from exc
    return {"detail": "Tag attached"}


@router.delete("/{todo_id}/tags/{tag_id}", status_code=200)
def detach_tag(
    todo_id: int, tag_id: int, db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        crud.todo.detach_tag(db, todo_id, tag_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"detail": "Tag detached"}
