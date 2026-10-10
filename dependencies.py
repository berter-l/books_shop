from starlette import status

from database import pool
from fastapi import Depends, HTTPException, Header

from security import get_jwt_token_body


def get_connection():
    connection = pool.getconn()
    return connection


def get_user_id_from_access_token(token: str = Header(alias="Authorization-token")):

    token_body = get_jwt_token_body(token)

    user_id = token_body.get("user_id", None)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return user_id


def get_author_id_from_access_token(token: str = Header(alias="Authorization-token")):
    token_body = get_jwt_token_body(token)

    author_id = token_body.get("author_id", None)

    if author_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return author_id
