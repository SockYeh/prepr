import aiohttp, os, logging, pydantic
from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from ..utils.database_handler import (
    get_problems,
    create_problem,
    update_problem,
    get_problem,
    delete_problem,
)
from ..utils.session_handler import is_admin

load_dotenv(find_dotenv())

router = APIRouter(prefix="/problems", tags=["problems"])
logger = logging.getLogger(__name__)


class ProblemsForm(pydantic.BaseModel):
    exam: str
    difficulty: str
    type: str
    subject: str
    category: str

    question: str
    options: list[str] = []
    correct_answers: list[str]

    comments: list[str] = []

    @pydantic.field_validator("options")
    @classmethod
    def validate_options(cls, v):
        if not v:
            return v
        if len(v) != len(set(v)):
            raise ValueError("Options should be unique")
        if len(v) != 4:
            raise ValueError("Options should be exactly 4")
        return v

    @pydantic.model_validator(mode="after")
    @classmethod
    def validate_correct_option(cls, values):
        if not values.options:
            return values
        if any([x not in values.options for x in values.correct_answers]):
            raise ValueError("Correct answer not in options")
        return values

    @pydantic.field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ["easy", "medium", "hard"]:
            raise ValueError("Invalid difficulty")
        return v

    @pydantic.field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["single", "multiple", "integer"]:
            raise ValueError("Invalid type")
        return v

    @pydantic.field_validator("subject")
    @classmethod
    def validate_subject(cls, v):
        if v not in ["mathematics", "physics", "chemistry", "zoology", "botany"]:
            raise ValueError("Invalid subject")
        return v

    @pydantic.field_validator("exam")
    @classmethod
    def validate_exam(cls, v):
        if v not in ["jee", "neet"]:
            raise ValueError("Invalid exam")
        return v

    model_config = {"arbitrary_types_allowed": True}


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
        content={"problems": [(problem.model_dump()) for problem in problems]}
    )


@router.post(
    "/",
    response_class=JSONResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(is_admin)],
)
async def add_problem_ep(request: Request, problem: ProblemsForm):
    op = await create_problem(**problem.model_dump())
    return JSONResponse(content={"message": f"Problem added with ID: {op}"})


@router.patch(
    "/{problem_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(is_admin)],
)
async def update_problem_ep(request: Request, problem_id: str, problem: ProblemsForm):
    op = await update_problem(problem_id, **problem.model_dump())
    return JSONResponse(content={"message": f"Problem updated with ID: {op}"})


@router.get(
    "/{problem_id}", response_class=JSONResponse, status_code=status.HTTP_200_OK
)
async def get_problem_ep(request: Request, problem_id: str):
    problem = await get_problem(problem_id)
    return JSONResponse(content={"problem": (problem.model_dump())})


@router.delete(
    "/{problem_id}",
    response_class=JSONResponse,
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(is_admin)],
)
async def delete_problem_ep(request: Request, problem_id: str):
    op = await delete_problem(problem_id)
