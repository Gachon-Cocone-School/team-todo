from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.tag import Tag
from app.models.todo import Priority, Status, Todo, todo_tags
from app.models.user import User
from app.schemas.todo import TodoCreate, TodoUpdate


def get_todos(
    db: Session,
    status: Status | None = None,
    priority: Priority | None = None,
    assignee_id: int | None = None,
    tag_id: int | None = None,
) -> list[Todo]:
    stmt = select(Todo)
    if status is not None:
        stmt = stmt.where(Todo.status == status)
    if priority is not None:
        stmt = stmt.where(Todo.priority == priority)
    if assignee_id is not None:
        stmt = stmt.where(Todo.assignee_id == assignee_id)
    if tag_id is not None:
        stmt = stmt.join(todo_tags, todo_tags.c.todo_id == Todo.id).where(
            todo_tags.c.tag_id == tag_id
        )
    return list(db.execute(stmt).scalars().all())


def get_todo(db: Session, todo_id: int) -> Todo | None:
    return db.execute(
        select(Todo).where(Todo.id == todo_id).options(selectinload(Todo.tags))
    ).scalar_one_or_none()


def create_todo(db: Session, data: TodoCreate) -> Todo:
    if data.assignee_id is not None and db.get(User, data.assignee_id) is None:
        raise ValueError("User not found")
    todo = Todo(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        due_date=data.due_date,
        assignee_id=data.assignee_id,
        created_by=data.created_by,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def update_todo(db: Session, todo_id: int, data: TodoUpdate) -> Todo | None:
    todo = db.get(Todo, todo_id)
    if todo is None:
        return None
    updated = data.model_fields_set
    if "title" in updated and data.title is not None:
        todo.title = data.title
    if "description" in updated:
        todo.description = data.description
    if "status" in updated and data.status is not None:
        todo.status = data.status
    if "priority" in updated and data.priority is not None:
        todo.priority = data.priority
    if "due_date" in updated:
        todo.due_date = data.due_date
    if "assignee_id" in updated:
        if data.assignee_id is not None and db.get(User, data.assignee_id) is None:
            raise ValueError("User not found")
        todo.assignee_id = data.assignee_id
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo(db: Session, todo_id: int) -> bool:
    todo = db.get(Todo, todo_id)
    if todo is None:
        return False
    db.delete(todo)
    db.commit()
    return True


def attach_tag(db: Session, todo_id: int, tag_id: int) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise ValueError("Todo not found")
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise ValueError("Tag not found")
    if tag in todo.tags:
        raise ValueError("Tag already attached")
    todo.tags.append(tag)
    db.commit()
    db.refresh(todo)
    return todo


def detach_tag(db: Session, todo_id: int, tag_id: int) -> Todo:
    todo = db.get(Todo, todo_id)
    if todo is None:
        raise ValueError("Todo not found")
    tag = db.get(Tag, tag_id)
    if tag is None or tag not in todo.tags:
        raise ValueError("Tag not attached")
    todo.tags.remove(tag)
    db.commit()
    db.refresh(todo)
    return todo
