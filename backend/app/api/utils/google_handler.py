import aiohttp, os, logging
from dotenv import load_dotenv, find_dotenv
from .database_handler import get_user_by_id, update_user_session

load_dotenv(find_dotenv())

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

logger = logging.getLogger(__name__)


class GoogleError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


async def refresh_token(userid: str) -> str:
    user = await get_user_by_id(userid)
    refresh_token = user.google_data.refresh_token
    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    async with aiohttp.ClientSession() as session:
        r = await session.post("https://oauth2.googleapis.com/token", data=payload)
        response = await r.json()
        access_token = response["access_token"]
        e = await update_user_session(userid, access_token)
        if e:
            return access_token
        raise GoogleError("Could not update the user session.")
