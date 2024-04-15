import os
import asyncio
import logging
import pydantic
from pymongo import errors
from bson.objectid import ObjectId
from dotenv import load_dotenv, find_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from email_validator import validate_email, EmailNotValidError

load_dotenv(find_dotenv())

connection_str = os.environ["MONGO_CONNECTION_STR"]
client = None
logger = logging.getLogger(__name__)


async def open_db() -> None:
    global client, users_db
    client = AsyncIOMotorClient(connection_str)
    users_db = client.users


async def close_db() -> None:
    client.close()  # pyright: ignore


def convert_to_bson_id(bson_id: str) -> ObjectId:
    """Converts a string to a BSON object id."""
    return ObjectId(bson_id)


def switch_id_to_pydantic(data: dict) -> dict:
    """Switches the id key to _id for pydantic models."""
    data["id"] = data["_id"]
    del data["_id"]
    return data


class ProblemModel(pydantic.BaseModel):
    id: str
    difficulty: str
    question: str
    options: list[str] | None
    correct_answers: list[str]

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

    @pydantic.validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ["easy", "medium", "hard"]:
            raise ValueError("Invalid difficulty")
        return v


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
    id: ObjectId
    username: str
    email: str
    profile_picture: str
    problems: list[ObjectId] = []
    ranking: RankingModel = RankingModel(rating=0, rank=0)
    is_google: bool
    google_data: GoogleData

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
