from app.schemes.shop_carts import CartItem, ResponseShopCartSchema
from database import pool
from handler import handle_not_found, handle_foreign_key


def add_product_to_cart(book_id: int, user_id: int, connection):
    """Добавляет товар в активную корзину пользователя"""

    connection.execute("""BEGIN""")
    try:
        cart = get_active_cart(user_id, connection)

        if cart is None:
            cart_id = create_cart_for_user(user_id, connection)
        else:
            cart_id = cart[0]

        save_cart_item_to_db(book_id, user_id, cart_id, connection=connection)

        connection.execute("""COMMIT""")
    except:
        connection.execute("""ROLLBACK""")
        raise

    pool.putconn(connection)

    return None


def get_active_cart(user_id: int, connection):
    """Возвращает, ещё не использованную для оформления заказа корзину пользователя."""

    active_cart = connection.execute(
        """SELECT id, user_id, is_order_placed FROM carts WHERE user_id = %s AND is_order_placed = %s""",
        (user_id, False),
    ).fetchone()

    return active_cart


def create_cart_for_user(user_id: int, connection):
    """Создаёт активную корзину для пользователя."""

    cart_id = connection.execute(
        """INSERT INTO carts (user_id)
           VALUES (%s)
           RETURNING id
            """,
        (user_id,),
    ).fetchone()[0]

    return cart_id


def get_items_from_active_cart(cart_id: int, connection):
    """Возвращает необработанные данные о товарах из активной корзины пользователя."""

    cart_items = connection.execute(
        """SELECT bk.title title, SUM(bk.price) total_amount_item, COUNT(bk.id) quantity, bk.id book_id
           FROM cart_items ci
           JOIN books bk
           ON ci.book_id = bk.id
           WHERE cart_id = %s
           GROUP BY bk.title, bk.id
           """,
        (cart_id,),
    ).fetchall()

    return cart_items


@handle_not_found
def get_processed_user_active_cart(user_id: int, connection):
    """
    Вернуть обработанные данные корзины пользователя.

    Args:
        user_id: ID пользователя, чью корзину хотим получить.
        connection: Объект соединения для работы с базой данных.


    Returns:
        Объект типа ResponseShopCartSchema, содержащий список товаров в корзине и их общую стоимость.

    """

    cart_id = get_active_cart(user_id, connection)[0]

    raw_cart_items_data = get_items_from_active_cart(cart_id, connection)

    processed_cart_items_data = build_cart_items_data_response(raw_cart_items_data)

    total_amount = sum([item.price for item in processed_cart_items_data])

    return ResponseShopCartSchema(
        items=processed_cart_items_data, total_amount=total_amount
    )


@handle_not_found
def build_cart_items_data_response(raw_cart_items_data):
    """
    Формируй объекты схемы для отдельных товаров в корзине.

    Args:
        raw_cart_items_data: Необработанные данные о товарах корзины
            в виде list[tuple].

    Returns:
        list[CartItem]: Список объектов товаров корзины.

    Raises:
        HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found."): Если данные о товарах корзины
         равны None.
    """

    processed_cart_items_data = []

    for raw_cart_item in raw_cart_items_data:
        processed_cart_items_data.append(
            CartItem(
                book_name=raw_cart_item[0],
                price=raw_cart_item[1],
                quantity=raw_cart_item[2],
            )
        )

    return processed_cart_items_data


@handle_foreign_key
def save_cart_item_to_db(book_id: int, user_id: int, cart_id: int, connection):
    """Сохраняет товар из корзины в базу данных"""

    connection.execute(
        """INSERT INTO cart_items (book_id, user_id, cart_id)
           VALUES (%s, %s, %s)""",
        (book_id, user_id, cart_id),
    )


def is_cart_exists(user_id: int, connection):
    """
    Определи существует ли активная корзина.

    Проверяет существует ли у пользователя корзина, которая не была использована
    для оформления заказа.

    Args:
         user_id: ID пользователя, у которого проверяем наличие корзины
         connection: Объект соединения для работы с базой данных
    Returns:
        Возвращает bool объект.
     """

    cart_exists = connection.execute(
        """SELECT EXISTS (SELECT * FROM carts WHERE user_id = %s AND is_order_placed = %s)""",
        (user_id, False),
    ).fetchone()[0]

    return cart_exists


def update_cart_status(cart_id: int, connection):
    """
    Измени статус корзины.

    Изменяет статус корзины, делая её не активной, после того,
    как она была использована в оформлении заказа.
    """

    connection.execute(
        """UPDATE carts SET is_order_placed = %s WHERE id = %s""",
        (True, cart_id),
    )
    return None
