import os
from .routes import auth
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET"])

routers = [auth.router]
for router in routers:
    app.include_router(router)
