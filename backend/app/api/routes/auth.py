import aiohttp, os, logging
from dotenv import load_dotenv, find_dotenv
from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from ..utils.database_handler import create_google_user, get_user_by_id, UserModel
from ..utils.session_handler import is_logged_in

load_dotenv(find_dotenv())

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/google", response_class=RedirectResponse)
async def google_login(request: Request) -> RedirectResponse:
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    )


@router.get("/google/callback", response_class=JSONResponse)
async def google_callback(request: Request, code: str):
    resp = JSONResponse(content={})
    payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with aiohttp.ClientSession() as session:
        r = await session.post("https://oauth2.googleapis.com/token", data=payload)
        response = await r.json()

        access_token = response["access_token"]
        refresh_token = response["refresh_token"]

        info = await session.get(
            f"https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        user_info = await info.json()
        pfp = user_info["picture"]
        email = user_info["email"]
        username = user_info["name"]
        _id = user_info["id"]

        op = await create_google_user(
            username,
            email,
            pfp,
            {
                "google_id": _id,
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
        )
        if op:
            logger.info(f"User {username} created successfully")
            resp.status_code = status.HTTP_201_CREATED
        else:
            logger.info(f"User login {username} successful")
            resp.status_code = status.HTTP_200_OK
        user = await get_user_by_id(_id, is_google_id=True)
        request.session["user_id"] = str(user.id)
        return resp


@router.get(
    "/logout", response_class=RedirectResponse, dependencies=[Depends(is_logged_in)]
)
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


@router.get("/me", response_class=JSONResponse, dependencies=[Depends(is_logged_in)])
async def get_me(request: Request):
    user = await get_user_by_id(request.session["user_id"])

    return JSONResponse(content=(user.model_dump()))
