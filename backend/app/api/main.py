import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from .routes import auth
from .utils.database_handler import close_db, open_db, create_user_db


@asynccontextmanager
async def lifespan(app: FastAPI):

    await open_db()
    yield

    await close_db()


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET"])

routers = [auth.router]
for router in routers:
    app.include_router(router)
