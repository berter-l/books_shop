from datetime import timedelta, datetime, timezone

from celery import Celery
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo="postgres://shop:1234@shop-postgres:5432/shop_db",
    min_size=10,
    max_size=15,
    kwargs={"autocommit": True},
)


main_celery_app = Celery(broker="amqp://guest:guest@rabbitmq:5672/")


main_celery_app.conf.beat_schedule = {
    "delete_expired_access_tokens": {
        "task": "delete_expired_access_tokens_from_db",
        "schedule": timedelta(minutes=5),
    },
    "delete_expired_refresh_tokens": {
        "task": "delete_expired_refresh_tokens_from_db",
        "schedule": timedelta(minutes=10),
    },
}


# Параметр который указывает, что все задачи, начинающиеся с delete_expired_ отправляются в очередь expired_tokens.
main_celery_app.conf.task_routes = {"delete_expired_*": {"queue": "expired_tokens"}}


@main_celery_app.task(name="delete_expired_access_tokens_from_db")
def delete_expired_access_tokens_from_db():
    now = datetime.now(tz=timezone.utc) - timedelta(minutes=5)

    connection = pool.getconn()
    connection.execute(
        """DELETE FROM access_token_blacklist WHERE created_at < %s """, (now,)
    )

    pool.putconn(connection)

    return None


@main_celery_app.task(name="delete_expired_refresh_tokens_from_db")
def delete_expired_refresh_tokens_from_db():
    now = datetime.now(tz=timezone.utc) - timedelta(minutes=5)

    connection = pool.getconn()
    connection.execute(
        """DELETE FROM refresh_token_blacklist WHERE created_at < %s """, (now,)
    )

    pool.putconn(connection)

    return None
