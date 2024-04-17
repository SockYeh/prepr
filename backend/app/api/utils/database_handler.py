import os
import asyncio
import logging
import pydantic
from pymongo import errors
from bson.objectid import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv, find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from email_validator import validate_email, EmailNotValidError

load_dotenv(find_dotenv())

connection_str = os.environ["MONGO_CONNECTION_STR"]
client = None
logger = logging.getLogger(__name__)


async def open_db() -> None:
    global client, users_db, problems_db, comments_db
    client = AsyncIOMotorClient(connection_str)
    users_db = client.users
    problems_db = client.problems
    comments_db = client.comments


async def close_db() -> None:
    client.close()  # pyright: ignore


def convert_to_bson_id(bson_id: str) -> ObjectId:
    """Converts a string to a BSON object id."""
    return ObjectId(bson_id)


def switch_id_to_pydantic(data: dict) -> dict:
    """Switches the id key to _id for pydantic models."""
    data["id"] = str(data["_id"])
    del data["_id"]
    return data


class ProblemModel(pydantic.BaseModel):
    id: str

    exam: str
    difficulty: str
    type: str
    subject: str
    category: str

    question: str
    options: list[str] | None
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

    @pydantic.field_validator("id")
    @classmethod
    def validate_id(cls, v):
        try:
            ObjectId(v)
        except InvalidId:
            raise ValueError("Invalid id")
        return v

    model_config = {"arbitrary_types_allowed": True}


class ProblemsModel(pydantic.BaseModel):
    problems_solved: list[ProblemModel]
    problems_attempted: list[ProblemModel]
    problems_bookmarked: list[ProblemModel]

    model_config = {"arbitrary_types_allowed": True}


class RankingModel(pydantic.BaseModel):
    rating: int
    rank: int

    model_config = {"arbitrary_types_allowed": True}


class GoogleData(pydantic.BaseModel):
    google_id: str
    access_token: str
    refresh_token: str


class UserModel(pydantic.BaseModel):
    id: str
    username: str
    email: str
    profile_picture: str
    problems: list[str] = []
    ranking: RankingModel = RankingModel(rating=0, rank=0)
    is_google: bool
    google_data: GoogleData

    @pydantic.field_validator("id")
    @classmethod
    def validate_id(cls, v):
        try:
            ObjectId(v)
        except InvalidId:
            raise ValueError("Invalid id")
        return v

    model_config = {"arbitrary_types_allowed": True}


class CommentModel(pydantic.BaseModel):
    id: str
    user: str
    comment: str
    problem: str
    likes: int = 0

    model_config = {"arbitrary_types_allowed": True}


async def create_user_db() -> None:
    await client.drop_database("users")  # pyright: ignore
    auth_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["username", "email", "is_google"],
            "properties": {
                "username": {
                    "bsonType": "string",
                    "description": "Username of the user",
                },
                "email": {
                    "bsonType": "string",
                    "description": "Email of the user",
                },
                "profile_picture": {
                    "bsonType": "string",
                    "description": "Profile picture path of the user",
                },
                "problems": {
                    "bsonType": "object",
                    "description": "Object containing all problem related data of the user",
                    "properties": {
                        "problems_solved": {
                            "bsonType": "array",
                            "description": "List of ids of problems solved by the user",
                            "items": {
                                "bsonType": "objectId",
                            },
                        },
                        "problems_attempted": {
                            "bsonType": "array",
                            "description": "List of ids of problems attempted by the user",
                            "items": {
                                "bsonType": "objectId",
                            },
                        },
                        "problems_bookmarked": {
                            "bsonType": "array",
                            "description": "List of ids of problems bookmarked by the user",
                            "items": {
                                "bsonType": "objectId",
                            },
                        },
                    },
                },
                "ranking": {
                    "bsonType": "object",
                    "description": "Object containing ranking related data of the user",
                    "properties": {
                        "rating": {
                            "bsonType": "int",
                            "description": "Rating of the user",
                        },
                        "rank": {
                            "bsonType": "int",
                            "description": "Rank of the user",
                        },
                    },
                },
                "is_google": {
                    "bsonType": "bool",
                    "description": "True if the user is registered using Google",
                },
                "google_data": {
                    "bsonType": "object",
                    "description": "Object containing Google related data of the user",
                    "properties": {
                        "google_id": {
                            "bsonType": "string",
                            "description": "Google account ID of the user",
                        },
                        "access_token": {
                            "bsonType": "string",
                            "description": "Access token of the user",
                        },
                        "refresh_token": {
                            "bsonType": "string",
                            "description": "Refresh token of the user",
                        },
                    },
                },
            },
        },
    }

    try:
        await users_db.create_collection("auth_details")
    except Exception as e:
        logger.error(e)
    logger.info("Collection created successfully")

    await users_db.command("collMod", "auth_details", validator=auth_validator)

    await users_db.auth_details.create_index("username", unique=True)
    await users_db.auth_details.create_index("email", unique=True)
    logger.info("Username and Email index created successfully")


async def create_problems_db() -> None:
    await client.drop_database("problems")  # pyright: ignore
    problems_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "exam",
                "difficulty",
                "type",
                "subject",
                "category",
                "question",
                "options",
                "correct_answers",
            ],
            "properties": {
                "exam": {
                    "bsonType": "string",
                    "description": "Exam for which the problem is",
                },
                "difficulty": {
                    "bsonType": "string",
                    "description": "Difficulty level of the problem",
                },
                "type": {
                    "bsonType": "string",
                    "description": "Type of the problem",
                },
                "subject": {
                    "bsonType": "string",
                    "description": "Subject of the problem",
                },
                "category": {
                    "bsonType": "string",
                    "description": "Category of the problem",
                },
                "question": {
                    "bsonType": "string",
                    "description": "Question of the problem",
                },
                "options": {
                    "bsonType": "array",
                    "description": "Options of the problem",
                    "items": {
                        "bsonType": "string",
                    },
                },
                "correct_answers": {
                    "bsonType": "array",
                    "description": "Correct answers of the problem",
                    "items": {
                        "bsonType": "string",
                    },
                },
                "comments": {
                    "bsonType": "array",
                    "description": "Comments on the problem",
                    "items": {
                        "bsonType": "objectId",
                    },
                },
            },
        },
    }

    try:
        await problems_db.create_collection("problems")
    except Exception as e:
        logger.error(e)
    logger.info("Collection created successfully")

    await problems_db.command("collMod", "problems", validator=problems_validator)


async def create_comments_db() -> None:
    await client.drop_database("comments")  # pyright: ignore
    comments_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user", "comment", "problem"],
            "properties": {
                "user": {
                    "bsonType": "objectId",
                    "description": "User who commented",
                },
                "comment": {
                    "bsonType": "string",
                    "description": "Comment by the user",
                },
                "problem": {
                    "bsonType": "objectId",
                    "description": "Problem on which the comment is",
                },
                "likes": {
                    "bsonType": "int",
                    "description": "Likes on the comment",
                },
            },
        },
    }

    try:
        await comments_db.create_collection("comments")
    except Exception as e:
        logger.error(e)
    logger.info("Collection created successfully")

    await comments_db.command("collMod", "comments", validator=comments_validator)


async def create_google_user(
    username: str, email: str, profile_picture: str, google_data: dict
) -> bool:
    """Creates a user with Google data."""
    try:
        await users_db.auth_details.insert_one(
            {
                "username": username,
                "email": email,
                "profile_picture": profile_picture,
                "is_google": True,
                "google_data": google_data,
            }
        )
        return True
    except errors.DuplicateKeyError:
        return False


async def get_user_by_id(user_id: str, is_google_id: bool = False) -> UserModel:
    """Gets a user by their id."""
    if is_google_id:
        user = await users_db.auth_details.find_one({"google_data.google_id": user_id})
    else:
        user = await users_db.auth_details.find_one(
            {"_id": convert_to_bson_id(user_id)}
        )
    if not user:
        raise ValueError("User not found")
    op = switch_id_to_pydantic(user)

    return UserModel(**op)


async def update_user_session(user_id: str, access_token: str) -> bool:
    """Updates the session data of a user."""
    await users_db.auth_details.update_one(
        {"_id": convert_to_bson_id(user_id)},
        {"$set": {"google_data.access_token": access_token}},
    )
    return True


async def create_problem(
    exam: str,
    difficulty: str,
    type: str,
    subject: str,
    category: str,
    question: str,
    correct_answers: list[str],
    options: list[str] = [],
) -> ObjectId:
    """Creates a problem."""
    problem = {
        "exam": exam,
        "difficulty": difficulty,
        "type": type,
        "subject": subject,
        "category": category,
        "question": question,
        "options": options,
        "correct_answers": correct_answers,
    }
    result = await problems_db.problems.insert_one(problem)
    return result.inserted_id


async def get_problems(
    subject: str | None = None,
    type: str | None = None,
    difficulty: str | None = None,
    exam: str | None = None,
) -> list[ProblemModel]:
    """Gets problems based on the filters. All problems if no filters are provided."""
    query = {}
    if subject:
        query["subject"] = subject
    if type:
        query["type"] = type
    if difficulty:
        query["difficulty"] = difficulty
    if exam:
        query["exam"] = exam
    problems = problems_db.problems.find(query)
    op = [switch_id_to_pydantic(problem) async for problem in problems]
    return [ProblemModel(**problem) for problem in op]


async def update_problem(problem_id: str, **kwargs) -> bool:
    """Updates a problem."""
    await problems_db.problems.update_one(
        {"_id": convert_to_bson_id(problem_id)}, {"$set": kwargs}
    )
    return True


async def get_problem(problem_id: str) -> ProblemModel:
    """Gets a problem by its id."""
    problem = await problems_db.problems.find_one(
        {"_id": convert_to_bson_id(problem_id)}
    )
    if not problem:
        raise ValueError("Problem not found")
    op = switch_id_to_pydantic(problem)
    return ProblemModel(**op)


async def delete_problem(problem_id: str) -> bool:
    """Deletes a problem."""
    await problems_db.problems.delete_one({"_id": convert_to_bson_id(problem_id)})
    return True


async def create_comment(user: str, comment: str, problem: str) -> ObjectId:
    """Creates a comment."""
    commentd = {
        "user": convert_to_bson_id(user),
        "comment": comment,
        "problem": convert_to_bson_id(problem),
        "likes": 0,
    }
    result = await comments_db.comments.insert_one(commentd)
    return result.inserted_id


async def get_comments(problem_id: str) -> list[CommentModel]:
    """Gets comments on a problem."""
    comments = comments_db.comments.find({"problem": convert_to_bson_id(problem_id)})
    op = [switch_id_to_pydantic(comment) async for comment in comments]
    return [CommentModel(**comment) for comment in op]


async def like_comment(comment_id: str) -> bool:
    """Likes a comment."""
    await comments_db.comments.update_one(
        {"_id": convert_to_bson_id(comment_id)}, {"$inc": {"likes": 1}}
    )
    return True


async def delete_comment(comment_id: str) -> bool:
    """Deletes a comment."""
    await comments_db.comments.delete_one({"_id": convert_to_bson_id(comment_id)})
    return True


async def get_user_comments(user_id: str) -> list[CommentModel]:
    """Gets comments by a user."""
    comments = comments_db.comments.find({"user": convert_to_bson_id(user_id)})
    op = [switch_id_to_pydantic(comment) async for comment in comments]
    return [CommentModel(**comment) for comment in op]


async def get_comment(comment_id: str) -> CommentModel:
    """Gets a comment by its id."""
    comment = await comments_db.comments.find_one(
        {"_id": convert_to_bson_id(comment_id)}
    )
    if not comment:
        raise ValueError("Comment not found")
    op = switch_id_to_pydantic(comment)
    return CommentModel(**op)


async def dislike_comment(comment_id: str) -> bool:
    """Dislikes a comment."""
    await comments_db.comments.update_one(
        {"_id": convert_to_bson_id(comment_id)}, {"$inc": {"likes": -1}}
    )
    return True


async def update_comment(comment_id: str, **kwargs) -> bool:
    """Updates a comment."""
    await comments_db.comments.update_one(
        {"_id": convert_to_bson_id(comment_id)}, {"$set": kwargs}
    )
    return True
