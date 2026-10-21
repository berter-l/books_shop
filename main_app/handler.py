from fastapi import HTTPException
from psycopg import errors
from starlette import status

from database import pool


def handle_not_found(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except TypeError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Not found."
            )

    return wrapper


def handle_unique(func):
    def wrapper(*args, connection):
        try:
            result = func(*args, connection=connection)
            return result

        except errors.UniqueViolation:
            pool.putconn(connection)

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Already exists."
            )

    return wrapper


def handle_foreign_key(func):
    def wrapper(*args, connection):
        try:
            result = func(*args, connection=connection)
            return result

        except errors.ForeignKeyViolation:
            pool.putconn(connection)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Such a book does not exist.",
            )

    return wrapper
