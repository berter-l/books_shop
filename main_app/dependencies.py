from fastapi import HTTPException, Header, Depends
from starlette import status

from database import pool
from security import get_jwt_token_body, ACCESS_TOKEN_TTL, is_token_exists_in_blacklist
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
    connection = get_connection()
    try:
        if is_token_exists_in_blacklist(token, connection):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        # Ищем id пользователя в кэше по его токену, если находим, то сразу возвращаем.
        user_id = get_value_from_cache_by_token(token)
        if user_id is not None:
            return user_id

        # Если токен валидный и ещё не сохранён, то расшифровываем его и сохраняем в кэш user_id из тела токена.
        # Для того, чтобы каждый раз не тратить ресурсы на расшифровку токена и сразу пропускать такой запрос.
        token_body = get_jwt_token_body(token)

        user_id = token_body.get("user_id", None)
        token_type = token_body.get("access_token", None)

        if user_id is None or token_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        save_token_to_cache(token, user_id, ttl=ACCESS_TOKEN_TTL)

        return user_id
    except HTTPException:
        raise


def get_author_id_from_access_token(
    token: str = Header(alias="Authorization-token"), connection=Depends(get_connection)
):
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
    try:
        # Если получить соединение через Depends, то
        # FastApi кэширует его на весь оставшийся запрос для подобных вызовов Depends.
        # То есть, если Depends(get_connection) выполнится один раз, то результат его работы
        # закэшируется для последующих вызовов этой зависимости при обработке данного запроса.
        # Может возникнуть ситуация, что в начале запроса получил соединение поработал и отправил в пул его,
        # а все последующие зависимости в цепочке будут использовать закэшированный объект соединения,
        # который был уже отправлен в пул и при попытке вернуть в пул уже отправленное соединение, возникнет ошибка.
        connection = get_connection()

        if is_token_exists_in_blacklist(token, connection):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        # Ищем id автора в кэше по его токену, если находим, то сразу возвращаем.
        author_id = get_value_from_cache_by_token(token)
        if author_id is not None:
            return author_id

        # Если токен валидный и ещё не сохранён, то расшифровываем его и сохраняем в кэш user_id из тела токена.
        # Для того, чтобы каждый раз не тратить ресурсы на расшифровку токена и сразу пропускать такой запрос.
        token_body = get_jwt_token_body(token)

        author_id = token_body.get("author_id", None)
        token_type = token_body.get("access_token", None)

        if author_id is None or token_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        save_token_to_cache(token, author_id, ttl=ACCESS_TOKEN_TTL)

        return author_id
    except HTTPException:
        raise


def check_authorization_admin_token(
    token: str = Header(alias="Authorization-admin-token"),
):
    """
    Проверяет правильный ли был передан токен и совпадает ли он с true токеном из БД.

    Args:
        token: токен, который будет проверяться.

    Returns:
        None.

    Raises:
        HTTPException:
            - status_code=
    """

    connection = get_connection()

    true_token = connection.execute("""SELECT token FROM admins""").fetchone()

    if true_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    if token != true_token[0]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="token invalid"
        )

    return None
