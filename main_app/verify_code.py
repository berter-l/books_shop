from redis import Redis
from app.config.main_config import settings

REDIS_HOST = settings.redis_config.host

REDIS_PORT = settings.redis_config.port

verify_code_redis_client = Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True
)


def get_verify_code_from_cache(user_email: str):
    """
    Возвращает код подтверждения из кэша, для заданной почты.

    Args:
        user_email: почта, по которой нужно получить код подтверждения.

    Returns:
        - Объект str, представляющий код подтверждения из 6 цифр, если почта существует в кэше.
        - None, если почты нет в кэше.
    """

    verify_code = verify_code_redis_client.get(user_email)

    return verify_code


def save_verify_code_to_cache(user_email: str, verify_code: str):
    """
    Сохраняет почту пользователя и код подтверждения для этой почты в кэше.

    Args:
        user_email: почта, для которой сохраняется код подтверждения.
        verify_code: код подверждения.

    Returns:
        None.
    """

    verify_code_redis_client.set(user_email, verify_code, ex=120)

    return None
