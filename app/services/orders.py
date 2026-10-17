from fastapi import HTTPException
from starlette import status

from app.schemes.orders import (
    ResponseManyOrdersSchema,
    ResponseOrderBase,
)
from app.services.books import (
    get_raw_books_by_list_of_id,
    update_data_number_of_books_in_stock,
)
from app.services.shop_carts import (
    get_active_cart,
    get_items_from_active_cart,
    is_cart_exists,
    update_cart_status,
)
from database import pool
from handler import handle_not_found


def get_raw_orders_by_user_id(user_id, connection, auto_return_to_pool=True):
    """
    Получает необработанные данные о заказах, для заданного пользователя.

    Args:
        user_id: ID пользователя чьи заказы нужно получить.
        connection: Объект соединения для работы с БД.
        auto_return_to_pool: Флаг, если True (по умолчанию), то функция вернёт соединение в пул сама, если False,
         то соединение должна вернуть, вызывающая функция.

    Returns:
        - list[tuple], где tuple - отдельная запись из БД, если данные найдены.
        - None, если данные не найдены.
    """

    raw_orders_data = connection.execute(
        """SELECT id, total_amount, created_at, status FROM orders WHERE user_id = %s""",
        (user_id,),
    ).fetchall()

    if auto_return_to_pool:
        pool.putconn(connection)

    return raw_orders_data


def get_processed_user_orders(user_id: int, connection):
    """
    Возвращает обработанные данные о заказах, для заданного пользователя.

    Args:
        user_id: ID пользователя, обработанные данные заказов, которого нужно получить.
        connection: Объект соединения для работы с БД.

    Returns:
         - Возвращает объект ResponseManyOrdersSchema, с атрибутом orders, в котором хранятся объекты ResponseOrderBase.
    """

    raw_orders_data = get_raw_orders_by_user_id(
        user_id, connection, auto_return_to_pool=False
    )

    processed_orders = build_user_orders_data_response(raw_orders_data)

    return ResponseManyOrdersSchema(orders=processed_orders)


@handle_not_found
def build_user_orders_data_response(raw_orders_data: list[tuple]) -> list[ResponseOrderBase]:
    """
    Формирует объекты схемы для заказов пользователя.

    Args:
        raw_orders_data: Необработанные записи о заказах из БД, где tuple отдельная запись из БД.

    Returns:
        Возвращает список с ResponseOrderBase, где у каждого отдельного объекта есть атрибуты
         (order_id - ID заказа в БД,
         created_at - Полная дата, оформления заказа в формате ГГГГ-ММ-ДД:ЧЧ-ММ-СС,
         status - Статус: "Готов" или "В пути",
         total_amount - Общая сумма заказа в руб.)
    Raises:
        HTTPException:
            - status_code=HTTP_404_NOT_FOUND, detail="Not found.", если данные, о заказах пользователя равны None.
    """

    processed_orders = []

    for raw_order in raw_orders_data:
        processed_orders.append(
            ResponseOrderBase(
                order_id=raw_order[0],
                created_at=raw_order[2],
                status=raw_order[3],
                total_amount=raw_order[1],
            )
        )

    return processed_orders


def place_an_order(user_id, connection):
    """
    Оформляет заказ для заданного пользователя.

    Управляет транзакцией: открывает и откатывает все изменения в случае ошибки, или сохраняет все изменения,
    если всё хорошо.

    Блокирует строки с книгами (во время проверки их количества на складе) до завершения транзакции.

    Args:
        user_id: ID пользователя, для которого оформляем заказ.
        connection: Объект соединения для работы с БД.

    Returns:
        None.
    Raises:
        HTTPException:
            - status_code=HTTP_404_NOT_FOUND, detail="Cart not found", если у пользователя нету корзины для оформления заказа.
            - status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail="Order creation failed", если возникает непредвиденная ошибка.
    """

    connection.execute("""BEGIN""")
    try:
        if not is_cart_exists(user_id, connection):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
            )

        cart_id = get_active_cart(user_id, connection)[0]

        items = get_items_from_active_cart(cart_id, connection)

        books_id = [item[3] for item in items]  # Список id, по которым будут искаться книги.

        number_of_books_in_cart = [item[2] for item in items]

        check_enough_books_to_place_an_order(items, books_id, connection)  # Если книг на складе не хватает, то заказ не создается

        total_amount = sum([item[1] for item in items])

        save_order_to_db(user_id, cart_id, total_amount, connection)

        update_data_number_of_books_in_stock(
            books_id, number_of_books_in_cart, connection
        )

        update_cart_status(cart_id, connection)

        connection.execute("""COMMIT""")

    except HTTPException:
        connection.execute("""ROLLBACK""")
        raise

    except:
        connection.execute("""ROLLBACK""")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order creation failed",
        )

    finally:
        pool.putconn(connection)
        return None


def save_order_to_db(user_id: int, cart_id: int, total_amount: float, connection):
    """
    Сохраняет данные о заказе в БД.

    Args:
        user_id: ID пользователя чей заказ сохраняем.
        cart_id: ID корзины, которая была использована для создания это заказа.
        total_amount: Общая стоимость (в рублях), всех товаров из корзины.
        connection: Объект соединения для работы с базой данных.

    Returns:
        None.
    """

    connection.execute(
        """INSERT INTO orders(user_id, cart_id, total_amount)
           VALUES(%s, %s, %s)""",
        (user_id, cart_id, total_amount),
    )

    return None

def check_enough_books_to_place_an_order(cart_items_data, books_id, connection):
    """
    Проверяет, хватает ли книг на складе для оформления заказа.

    Для каждой книги из корзины, проверяет, достаточно ли на складе экземляров для того, чтобы оформить заказ.

    Args:
        cart_items_data: Данные о книгах в корзине.
        connection: Объект соединения для работы с базой данных.
        books_id: список id книг чьё наличие на складе будет проверяться.

    Returns:
        None.

    Raises:
        HTTPException:
            - status_code=HTTP_409_CONFLICT, detail="сообщение о всех книгах, для которых на складе, не хватает экземляров.
    """

    books_data = get_raw_books_by_list_of_id(books_id, connection)

    #  Если количество книг на складе недостаточно,
    #  то формируется сообщение об ошибке и добавляется в список.
    error_messages = []
    for item_data_from_cart, book_data_from_db in zip(cart_items_data, books_data):
        if item_data_from_cart[2] > book_data_from_db[3]:
            error_messages.append(
                f"The number of books titled {book_data_from_db[1]} exceeds the quantity in stock ({book_data_from_db[3]} books). "
            )

    if error_messages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=", ".join(error_messages),
        )

    return None
