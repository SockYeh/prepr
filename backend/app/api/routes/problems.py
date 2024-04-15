import aiohttp, os, logging
from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from ..utils.database_handler import (
    get_problems,
    ProblemModel,
    create_problem,
    update_problem,
    get_problem,
    delete_problem,
)
from ..utils.session_handler import is_admin

load_dotenv(find_dotenv())

router = APIRouter(prefix="/problems", tags=["problems", "questions"])
logger = logging.getLogger(__name__)


def convert_bsonid_to_string(obj: dict) -> dict:
    obj["_id"] = str(obj["_id"])
    obj["comments"] = [str(i) for i in obj["comments"]]
    return obj


@router.get("/", response_class=JSONResponse, status_code=status.HTTP_200_OK)
async def get_problems_ep(
    request: Request,
    subject: str | None = None,
    type: str | None = None,
    difficulty: str | None = None,
    exam: str | None = None,
):
    problems = await get_problems(subject, type, difficulty, exam)
    return JSONResponse(
        content={
            "problems": [
                convert_bsonid_to_string(problem.model_dump()) for problem in problems
            ]
        }
    )


@router.post(
    "/",
    response_class=JSONResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(is_admin)],
)
async def add_problem_ep(request: Request, problem: ProblemModel):
    op = await create_problem(**problem.model_dump())
    return JSONResponse(content={"message": f"Problem added with ID: {op}"})


@router.patch(
    "/{problem_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(is_admin)],
)
async def update_problem_ep(request: Request, problem_id: str, problem: ProblemModel):
    op = await update_problem(problem_id, **problem.model_dump())
    return JSONResponse(content={"message": f"Problem updated with ID: {op}"})


@router.get(
    "/{problem_id}", response_class=JSONResponse, status_code=status.HTTP_200_OK
)
async def get_problem_ep(request: Request, problem_id: str):
    problem = await get_problem(problem_id)
    return JSONResponse(
        content={"problem": convert_bsonid_to_string(problem.model_dump())}
    )


@router.delete(
    "/{problem_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(is_admin)],
)
async def delete_problem_ep(request: Request, problem_id: str):
    op = await delete_problem(problem_id)
    return JSONResponse(content={"message": f"Problem deleted with ID: {op}"})
