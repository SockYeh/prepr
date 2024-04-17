import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, problems, comments
from .utils.database_handler import (
    close_db,
    open_db,
    create_user_db,
    create_problems_db,
    create_comments_db,
)

origins = ["http://localhost:8000", "http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):

    await open_db()
    yield

    await close_db()


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


routers = [auth.router, problems.router, comments.router]
for router in routers:
    app.include_router(router)
