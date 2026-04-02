from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import comments, tags, todos, users


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Team Todo API", version="0.1.0", lifespan=lifespan)

app.include_router(users.router)
app.include_router(todos.router)
app.include_router(comments.router)
app.include_router(tags.router)
