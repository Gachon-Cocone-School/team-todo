from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


def get_tags(db: Session) -> list[Tag]:
    return list(db.execute(select(Tag)).scalars().all())


def get_tag(db: Session, tag_id: int) -> Tag | None:
    return db.get(Tag, tag_id)


def create_tag(db: Session, data: TagCreate) -> Tag:
    existing = db.execute(select(Tag).where(Tag.name == data.name)).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Tag name already exists")
    tag = Tag(name=data.name, color=data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def update_tag(db: Session, tag_id: int, data: TagUpdate) -> Tag | None:
    tag = db.get(Tag, tag_id)
    if tag is None:
        return None
    if data.name is not None:
        duplicate = db.execute(
            select(Tag).where(Tag.name == data.name, Tag.id != tag_id)
        ).scalar_one_or_none()
        if duplicate is not None:
            raise ValueError("Tag name already exists")
        tag.name = data.name
    if "color" in data.model_fields_set:
        tag.color = data.color
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag_id: int) -> bool:
    tag = db.get(Tag, tag_id)
    if tag is None:
        return False
    db.delete(tag)
    db.commit()
    return True
