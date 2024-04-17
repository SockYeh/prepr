import aiohttp, os, logging, pydantic
from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from ..utils.database_handler import (
    create_comment,
    get_comments,
    get_comment,
    update_comment,
    delete_comment,
)
from ..utils.session_handler import is_logged_in

load_dotenv(find_dotenv())

router = APIRouter(prefix="/comments", tags=["comments"])
logger = logging.getLogger(__name__)


class CommentForm(pydantic.BaseModel):
    user: str
    comment: str
    problem: str
    likes: int = 0

    model_config = {"arbitrary_types_allowed": True}


@router.get("/", response_class=JSONResponse, status_code=status.HTTP_200_OK)
async def get_comments_ep(request: Request, problem_id: str):
    comments = await get_comments(problem_id=problem_id)
    return JSONResponse(
        content={"comments": [comment.model_dump() for comment in comments]}
    )


@router.post(
    "/",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(is_logged_in)],
)
async def add_comment_ep(request: Request, comment: CommentForm):
    op = await create_comment(**comment.model_dump())
    return JSONResponse(content={"message": f"Added comment with ID: {op}"})


@router.patch(
    "/{comment_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[],  # HELP!
)
async def update_comment_ep(request: Request, comment_id: str, comment: CommentForm):
    op = await update_comment(comment_id, **comment.model_dump())
    return JSONResponse(content={"message": f"Comment updated with ID: {op}"})


@router.get(
    "/{comment_id}", response_class=JSONResponse, status_code=status.HTTP_200_OK
)
async def get_comment_ep(request: Request, comment_id: str):
    comment = await get_comment(comment_id)
    return JSONResponse(content={"comment": (comment.model_dump())})


@router.delete(
    "/{comment_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[],  # HELP!
)
async def delete_comment_ep(request: Request, comment_id: str):
    await delete_comment(comment_id)
