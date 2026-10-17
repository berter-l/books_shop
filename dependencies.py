from fastapi import HTTPException, Header
from starlette import status

import security
from database import pool
from security import get_jwt_token_body
from session import get_value_from_cache_by_token, save_token_to_cache


def get_connection():
    """
    Возвращает объект соединения для работы с БД.

    Returns:
        - Объект соединения
    """

    connection = pool.getconn()
    return connection


def get_user_id_from_access_token(token: str = Header(alias="Authorization-token")):
    """
    Возвращает id пользователя из переданного в заголовке "Authorization-token" access токена.

    Returns:
        ID пользователя из токена.

    Raises:
        HTTPException:
            - status_code=HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", если в токене отсутствует user_id.
            - status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token", если у токена неверная подпись.
            - status_code=HTTP_401_UNAUTHORIZED, detail="Token expired", если у токена истёк срок годности.
    """

    # Ищем id пользователя в кэше по его токену, если находим, то сразу возвращаем.
    user_id = get_value_from_cache_by_token(token)
    if user_id is not None:
        return user_id

    # Если токен валидный и ещё не сохранён, то расшифровываем его и сохраняем в кэш user_id из тела токена.
    # Для того, чтобы каждый раз не тратить ресурсы на расшифровку токена и сразу пропускать такой запрос.
    token_body = get_jwt_token_body(token)

    user_id = token_body.get("user_id", None)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    save_token_to_cache(token, user_id, ttl=security.ACCESS_TOKEN_TTL)

    return user_id


def get_author_id_from_access_token(token: str = Header(alias="Authorization-token")):
    """
    Возвращает id автора из переданного в заголовке "Authorization-token" access токена.

    Returns:
        ID автора из токена.

    Raises:
        HTTPException:
            - status_code=HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", если в токене отсутствует author_id.
            - status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token", если у токена неверная подпись.
            - status_code=HTTP_401_UNAUTHORIZED, detail="Token expired", если у токена истёк срок годности.
    """

    # Ищем id автора в кэше по его токену, если находим, то сразу возвращаем.
    author_id = get_value_from_cache_by_token(token)
    if author_id is not None:
        return author_id

    # Если токен валидный и ещё не сохранён, то расшифровываем его и сохраняем в кэш user_id из тела токена.
    # Для того, чтобы каждый раз не тратить ресурсы на расшифровку токена и сразу пропускать такой запрос.
    token_body = get_jwt_token_body(token)

    author_id = token_body.get("author_id", None)

    if author_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    save_token_to_cache(token, author_id, ttl=security.ACCESS_TOKEN_TTL)

    return author_id
