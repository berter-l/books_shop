from fastapi import HTTPException
from starlette import status

from app.schemes.jwt import ResponseJWTTokensSchema
from app.schemes.users import ResponseUserProfileSchema
from database import pool
from handler import handle_not_found, handle_unique
from security import get_hashed_password, get_jwt_tokens, is_password_correct


def register_user(
    first_name: str, last_name: str, email: str, age: int, password: str, connection
):
    """
    Регистрирует пользователя с указанными данными.

    Получает и сохраняет хеш пароля.
    Получает и отдает jwt токены для аунтентификации.

    Args:
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        email: Почта пользователя.
        age: Возраст пользователя.
        password: Необработанный пароль пользователя.
        connection: Объект соединения для работы с БД.

    Returns:
        - Объект-схема ResponseJWTTokensSchema, с атрибутами (access_token, refresh_token).
    Raises:
        HTTPException:
            - status_code=HTTP_409_CONFLICT, detail="User already exists", если пользователь с такими данными уже существует.
    """
    if is_user_exists(email, connection):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    hashed_password = get_hashed_password(password)

    user_id = save_user_to_db(
        first_name, last_name, email, age, hashed_password, connection=connection
    )

    jwt_tokens = get_jwt_tokens({"user_id": user_id})

    return ResponseJWTTokensSchema(
        access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
    )


def get_user_profile(user_id: int, connection):
    """
    Возвращает обработанные данные о профиле пользователя.

    В конце возвращает в пул соединение.

    Args:
        user_id: ID пользователя чей профиль нужно получить.
        connection: Объект соединения для работы с БД.

    Returns:
        - ResponseUserProfileSchema, объект-схема профиля с полями (first_name, last_name, email, age, balance).
    """

    raw_user_data = connection.execute(
        """
    SELECT first_name, last_name, email, age, balance FROM users WHERE id = %s;""",
        (user_id,),
    ).fetchone()

    processed_user_data = build_user_profile_data_response(raw_user_data)

    pool.putconn(connection)

    return processed_user_data


@handle_not_found
def build_user_profile_data_response(raw_user_profile: tuple):
    """
    Формирует объект ResponseUserProfileSchema из необработанных данных о профиле пользователя.

    Args:
        raw_user_profile: объект tuple, представляющий необработанную запись из БД.

    Returns:
        - Объект ResponseUserProfileSchema с атрибутами (first_name, last_name, email, age, balance).

    Raises:
        HTTPException:
            - status_code=HTTP_404_NOT_FOUND, detail="User not found, если передано None, в качестве аргумента.
    """

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
    """
    Сохраняет данные о пользователе в БД.

    Args:
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        email: Почта пользователя.
        age: Возраст пользователя.
        hashed_password: Хеш пользовательского пароля.
        connection: Объект соединения для работы с БД.

    Returns:
        user_id - ID пользователя.
    """

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
    """
    Возвращает, необработанные данные о пользователе по его email.

    Args:
        email: Почта, по которой нужно получить пользователя.
        connection: Объект соединения для работы с БД.

    Returns:
        - Возвращает tuple, в котором необработанные данные пользователя.
        - None, если пользователь с таким email не существует.
    """

    user = connection.execute(
        """SELECT id, email, age, first_name, password FROM users WHERE email = %s;""",
        (email,),
    ).fetchone()

    return user


def login_user(email: str, password: str, connection):
    """
    Аутентифицирует пользователя по email и password.

    Args:
        email: Почта пользователя, которую нужно проверить.
        password: Пароль пользователя, который нужно проверить.
        connection: Объект соединения для работы с БД.

    Returns:
        - Объект-схема ResponseJWTTokensSchema, с атрибутами (access_token, refresh_token).
    Raises:
        HTTPException:
            - status_code=400, detail="Incorrect email or password", если почта или пароль не были подтверждены.
    """

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
