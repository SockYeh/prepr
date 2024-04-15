import aiohttp, os, logging
from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from ..utils.database_handler import (
    create_comment,
    get_comments,
    CommentModel,
    get_comment,
    update_comment,
    delete_comment,
)
from ..utils.session_handler import is_logged_in

load_dotenv(find_dotenv())

router = APIRouter(
    prefix="/comments", tags=["comments", "posts", "forums", "discussions"]
)
logger = logging.getLogger(__name__)
