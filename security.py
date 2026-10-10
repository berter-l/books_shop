import datetime
from fastapi import HTTPException
import jwt
from bcrypt import hashpw, gensalt, checkpw
from jwt import decode, encode
from starlette import status

from app.config.main_config import Settings, settings

SECRET_KEY = settings.jwt_config.secret_key

ACCESS_TOKEN_TTL = settings.jwt_config.access_token_ttl_minute

REFRESH_TOKEN_TTL = settings.jwt_config.refresh_token_ttl_minute

ALGORITHM = settings.jwt_config.algorithm


def get_hashed_password(password: str):
    hashed_password = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")
    return hashed_password


def is_password_correct(password: bytes, hashed_password: bytes):
    return checkpw(password, hashed_password)


def get_jwt_tokens(token_body: dict) -> tuple[str, str]:
    access_token = create_jwt_token(token_body, "access")
    refresh_token = create_jwt_token(token_body, "refresh")

    return access_token, refresh_token


def create_jwt_token(token_body, token_type):
    token_ttl = ACCESS_TOKEN_TTL if token_type != "refresh" else REFRESH_TOKEN_TTL

    token_body["exp"] = datetime.datetime.now(
        tz=datetime.timezone.utc
    ) + datetime.timedelta(minutes=token_ttl)

    token = encode(token_body, SECRET_KEY, ALGORITHM)

    return token


def get_jwt_token_body(token: str):
    try:
        token_body = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return token_body

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
