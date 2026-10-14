from fastapi import HTTPException

from app.schemes.jwt import ResponseJWTTokensSchema
from app.schemes.users import ResponseUserProfileSchema
from database import pool
from handler import handle_not_found, handle_unique
from security import get_hashed_password, get_jwt_tokens, is_password_correct


def register_user(
    first_name: str, last_name: str, email: str, age: int, password: str, connection
):
    if is_user_exists(email, connection):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = get_hashed_password(password)

    user_id = save_user_to_db(
        first_name, last_name, email, age, hashed_password, connection=connection
    )

    jwt_tokens = get_jwt_tokens({"user_id": user_id})

    return ResponseJWTTokensSchema(
        access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
    )


def get_user_profile(user_id: int, connection):
    raw_user_data = connection.execute(
        """
    SELECT first_name, last_name, email, age, balance FROM users WHERE id = %s;""",
        (user_id,),
    ).fetchone()

    processed_user_data = build_user_profile_data_response(raw_user_data)

    pool.putconn(connection)

    return processed_user_data


@handle_not_found
def build_user_profile_data_response(raw_user_profile):
    processed_user_profile = ResponseUserProfileSchema(
        first_name=raw_user_profile[0],
        last_name=raw_user_profile[1],
        email=raw_user_profile[2],
        age=raw_user_profile[3],
        balance=raw_user_profile[4],
    )
    return processed_user_profile


@handle_unique
def save_user_to_db(
    first_name: str,
    last_name: str,
    email: str,
    age: int,
    hashed_password: str,
    connection,
):
    user_id = connection.execute(
        """
    INSERT INTO users (first_name, last_name, email, age, password, balance)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id;""",
        (first_name, last_name, email, age, hashed_password, 0),
    ).fetchone()[0]

    pool.putconn(connection)

    return user_id


def get_raw_user_by_email(email: str, connection):
    user = connection.execute(
        """SELECT id, email, age, first_name, password FROM users WHERE email = %s;""",
        (email,),
    ).fetchone()

    return user


def login_user(email: str, password: str, connection):
    user = get_raw_user_by_email(email, connection)

    if user is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    hashed_password = user[4].encode()

    if is_password_correct(password.encode(), hashed_password):
        jwt_tokens = get_jwt_tokens({"user_id": user[0]})
        pool.putconn(connection)
        return ResponseJWTTokensSchema(
            access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
        )

    raise HTTPException(status_code=400, detail="Incorrect email or password")


def is_user_exists(email: str, connection):
    """
    Проверяет, существует ли пользователь с таким email.

    Args:
        email: Почта, по которой ищем пользователя.
        connection: Объект соединения для работы с базой данных

    Returns:
        - True, если пользователь найден.
        - False, если пользователь не найден.
    """

    user = get_raw_user_by_email(email, connection)

    if user is not None:
        return True

    return False
