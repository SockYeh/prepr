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


def convert_bsonid_to_string(obj: dict) -> dict:
    obj["_id"] = str(obj["_id"])
    obj["user"] = str(obj["user"])
    obj["problem"] = str(obj["problem"])
    obj["likes"] = str(obj["likes"])
    return obj


@router.get("/", response_class=JSONResponse, status_code=status.HTTP_200_OK)
async def get_comments_ep(request: Request, problem_id: str):
    comments = await get_comments(problem_id=problem_id)
    return JSONResponse(
        content={
            "comments": [
                convert_bsonid_to_string(obj=comment.model_dump())
                for comment in comments
            ]
        }
    )


@router.post(
    "/",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(is_logged_in)],
)
async def add_comment_ep(request: Request, comment: CommentModel):
    op = await create_comment(**comment.model_dump())
    return JSONResponse(content={"message": f"Added comment with ID: {op}"})


@router.patch(
    "/{comment_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[],  # HELP!
)
async def update_comment_ep(request: Request, comment_id: str, comment: CommentModel):
    op = await update_comment(comment_id, **comment.model_dump())
    return JSONResponse(content={"message": f"Comment updated with ID: {op}"})


@router.get(
    "/{comment_id}", response_class=JSONResponse, status_code=status.HTTP_200_OK
)
async def get_comment_ep(request: Request, comment_id: str):
    comment = await get_comment(comment_id)
    return JSONResponse(
        content={"comment": convert_bsonid_to_string(comment.model_dump())}
    )


@router.delete(
    "/{comment_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[],  # HELP!
)
async def delete_comment_ep(request: Request, comment_id: str):
    await delete_comment(comment_id)
