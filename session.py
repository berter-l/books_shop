from redis import Redis

redis_client = Redis(host="shop-redis", port=6379, db=0, decode_responses=True)


def get_value_from_cache_by_token(token: str):
    """
    Возвращает значение из cache по ключу в виде токена.

    Args:
        token: токен чьё значение нужно достать.

    Returns:
        - None, если ключ не сущетсвует в cache.
        - id обладателя токена, если ключ существует.
    """

    return redis_client.get(token)


def save_token_to_cache(token: str, owner_id: int, ttl: int):
    """
    Сохраняет токен в cache, с определенным ttl, ключ-сам токен, а значение owner_id.

    Args:
        owner_id: ID владельца токена.
        token: Токен, который нужно сохранить.
        ttl: Время (в секундах), через которое нужно удалить этот токен из cache.

    Returns:
        - None.
    """

    redis_client.set(token, owner_id, ex=ttl)
    return None
