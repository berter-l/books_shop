from app.schemes.admins import ResponseAllUsersOrders
from app.services.orders import get_raw_orders
from .orders import build_user_orders_data_response
from .users import send_email_task, get_user_email_by_order_id
from database import pool


def get_processed_users_orders(connection) -> ResponseAllUsersOrders:
    """
    Возвращает все обработанные заказы, всех пользователей.

    Returns:
        - Объект ResponseAllUsersOrders, представляющий все заказы пользователей, с атрибутом orders, в котором список объектов ResponseOrderBase.

    Raises:
        HTTPException:
            - status_code=HTTP_404_NOT_FOUND, detail="Not found.", если данные, о заказах пользователей равны None.
    """

    raw_orders = get_raw_orders(connection)

    processed_orders = build_user_orders_data_response(raw_orders)

    return ResponseAllUsersOrders(orders=processed_orders)


def update_order_status(connection, order_id: int):
    """
    Обновляет статус заказа, меняя его на "доставлено".

    Получает почту пользователя, связанного с этим заказом.
    Отправляет письмо на почту заказчика с уведомлением о доставке заказа.

    Args:
        connection: объект соединения для работы с БД.
        order_id: ID заказа чей статус нужно изменить.

    Returns:
        - None.
    """

    user_email = get_user_email_by_order_id(order_id, connection)

    connection.execute(
        """
        UPDATE orders
        SET status = 'delivered'
        WHERE id = %s
        """,
        (order_id,),
    )

    pool.putconn(connection)
    send_email_task(user_email, "Ваш заказ доставлен.")

    return None
