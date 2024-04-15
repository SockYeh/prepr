from fastapi import HTTPException, Request
from dotenv import load_dotenv, find_dotenv
from os import environ

load_dotenv(find_dotenv())

admins = environ["ADMINS"].split(", ")


async def is_admin(request: Request):
    """Validates the session of the user."""
    try:
        assert request.session["user_id"] in admins
    except AssertionError:
        raise HTTPException(status_code=403, detail="You are not an admin.")


async def is_logged_in(request: Request):
    """Validates the session of the user."""
    try:
        assert request.session["user_id"]
    except AssertionError:
        raise HTTPException(status_code=403, detail="You are not logged in.")
