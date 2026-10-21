import datetime
from fastapi import HTTPException
import jwt
from bcrypt import hashpw, gensalt, checkpw
from jwt import encode
from starlette import status

from app.config.main_config import settings
from database import pool

SECRET_KEY = settings.jwt_config.secret_key

ACCESS_TOKEN_TTL = settings.jwt_config.access_token_ttl_minute

REFRESH_TOKEN_TTL = settings.jwt_config.refresh_token_ttl_minute

ALGORITHM = settings.jwt_config.algorithm


def get_hashed_password(password: str):
    """
    Возвращает хешированыый пароль.

    Args:
        password: необработанный пароль, который нужной захэшировать.

    Returns:
        - Строку хешированного пароля.
    """

    hashed_password = hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")
    return hashed_password


def is_password_correct(password: bytes, hashed_password: bytes):
    """
    Проверяет совпадают ли пароли.

    Args:
        password: не хэшированный пароль, который нужно проверить.
        hashed_password: хешированный пароль, с которым будет сравнение и из которого будет взята соль для первого пароля.

    Returns:
        - True, если пароли совпадают.
        - False, если пароли не совпадают.
    """

    return checkpw(password, hashed_password)


def get_jwt_tokens(token_body: dict) -> tuple[str, str]:
    """
    Возвращает пару jwt токенов: access_token, refresh_token.

    За основу тела токена берёт данные из token_body, но добавляет различные специальные поля под каждый токен.

    Args:
        token_body: словарь с полями, которые должны быть в каждом токене.

    Returns:
        - tuple, где первый элемент - access_token, а второй - refresh_token.
    """

    # Задаёт для токенов метки, чтобы в дальнейшем при проверке их различать.
    # Например, не пропускать запросы, которые отправляют в заголовке refresh токен, вместо access токена.
    access_token_body = token_body.copy()
    access_token_body["access_token"] = 1

    refresh_token = token_body.copy()
    refresh_token["refresh_token"] = 1

    # Создаём пару jwt токенов с разной информацией в теле.
    access_token = create_jwt_token(access_token_body, "access")
    refresh_token = create_jwt_token(refresh_token, "refresh")

    return access_token, refresh_token


def create_jwt_token(token_body, token_type):
    """
    Создаёт jwt токен с указаным телом, и в зависимости от token_type с разным ttl.

    Args:
        token_body: словарь с полями, которые должны быть в теле токена.
        token_type: тип токена, который нужно создать, от него зависит ttl, который будет у токена.

    Returns:
        - str объект, представляющий jwt токен.
    """

    token_ttl = ACCESS_TOKEN_TTL if token_type != "refresh" else REFRESH_TOKEN_TTL

    token_body["exp"] = datetime.datetime.now(
        tz=datetime.timezone.utc
    ) + datetime.timedelta(minutes=token_ttl)

    token = encode(token_body, SECRET_KEY, ALGORITHM)

    return token


def get_jwt_token_body(token: str):
    """
    Возвращает тело переданного токена.

    Расшифровывает токен и если он истёк или не валидна подпись, то выбрасывает ошибку.

    Args:
        token: токен, чьё тело нужно получить.

    Returns:
        - dict, где ключи это поля из тела токена.

    Raises:
        HTTPException:
            -  status_code=HTTP_401_UNAUTHORIZED, detail="Token expired", если токен просрочен.
            -  status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token", если у токена невалидная подпись.
    """

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


def is_token_exists_in_blacklist(token: str, connection):
    """
    Проверяет находится ли токен в blacklist.

    Args:
        token: jwt токен, который нужно проверить.
        connection: объект соединения для работы с БД.

    Returns:
        - True, если хотя бы в одном из списков blacklist присутствует заданный токен.
        - False, если ни в одном списке нету данного токена.
    """

    is_exists_in_access_token_blacklist = connection.execute(
        """
        SELECT EXISTS(
            SELECT * FROM access_token_blacklist WHERE access_token=%s
            )
        """,
        (token,),
    ).fetchone()[0]

    is_exists_in_refresh_token_blacklist = connection.execute(
        """
        SELECT EXISTS(
            SELECT * FROM refresh_token_blacklist WHERE refresh_token=%s
            )
        """,
        (token,),
    ).fetchone()[0]

    pool.putconn(connection)

    return is_exists_in_access_token_blacklist or is_exists_in_refresh_token_blacklist
