from app.schemes.books import ResponseOneBookSchema
from database import pool
from handler import handle_not_found


def get_books_by_author_id(author_id: int, connection, auto_return_to_pool=True):
    """
    Возвращает книги определенного автора.

    Args:
        author_id: ID автора, чьи книги нужно получить.
        connection: Объект соединения для работы с базой данных
        auto_return_to_pool: Флаг, который определяет функция сама вернёт соединение в пул, или
          внешняя функция вернёт в пул соединений,

    Returns:
         - Возвращает list[tuple], где tuple представляет одну строку из таблицы БД, с данными о книге автора.
         - None, если у данного автора нету книг.

    """

    raw_books_data = connection.execute(
        """
        SELECT title, price, count FROM books WHERE author_id = %s
        """,
        (author_id,),
    ).fetchall()

    if auto_return_to_pool:
        pool.putconn(connection)

    return raw_books_data


@handle_not_found
def build_books_data_response(raw_books_data) -> list[ResponseOneBookSchema]:
    """
    Возвращает сформированные из необработанных записей из БД, объекты ResponseOneBookSchema.

    Args:
        raw_books_data: Необработанные записи о книгах из БД.

    Returns:
        Возаращает list[ResponseOneBookSchema], где ResponseOneBookSchema объект содержащий данные об одной книге
         (title, price, count).

    Raises:
        HTTPException:
            -  status_code=HTTP_404_NOT_FOUND, detail="Not found.", если книг не существует.

    """
    processed_books = []

    for raw_book in raw_books_data:
        processed_books.append(
            ResponseOneBookSchema(
                title=raw_book[0], price=raw_book[1], count=raw_book[2]
            )
        )

    return processed_books


def get_raw_books_data(page: int, limit: int, connection):
    """
    Возвращает, определенное количество записей из БД, с необработанными данными, о книгах.

    Args:
        page: Какую страницу с книгами, нужно вернуть.
        limit: Сколько записей вернётся для 1 страницы.
        connection: Объект соединения для работы с базой данных

    Returns:
        - list[tuple], где tuple - одна необработанная запись из БД.
        - None, если записей на определенной странице нету.
    """

    raw_books_data = connection.execute(
        """
        SELECT title, price, count FROM books OFFSET %s LIMIT %s
        """,
        ((page - 1) * limit, limit),
    ).fetchall()

    return raw_books_data


def get_processed_books_data(page: int, limit: int, connection):
    """
    Возвращает обработанные данные о книгах.

    Args:
        page: Какую страницу с книгами, нужно вернуть.
        limit: Сколько записей вернётся для 1 страницы.
        connection: Объект соединения для работы с базой данных

    Returns:
        - list[ResponseOneBookSchema], где в каждом ResponseOneBookSchema объекте хранятся: title, price, count.

    Raises:
        HTTPException:
            - status_code=HTTP_404_NOT_FOUND, detail="Not found.", если книг на определенной странице нету.
    """

    raw_books_data = get_raw_books_data(page=page, limit=limit, connection=connection)

    processed_books_data = build_books_data_response(raw_books_data)

    return processed_books_data


def create_book(title, price, count, author_id, connection):
    """
    Создаёт запись о книге в таблице books.

    Args:
        title: Название книги.
        price: Цена книги в рублях.
        count: Число книг, которые в наличие на складе.
        author_id: ID автора с которым будет связана данная книга.
        connection: Объект соединения для работы с базой данных.

    Returns:
        None.

    """
    connection.execute(
        """
        INSERT INTO books (title, price, count, author_id)
        VALUES (%s, %s, %s, %s)
        """,
        (title, price, count, author_id),
    )

    pool.putconn(connection)

    return None


def get_price_by_book_id(book_id: int, connection):
    """
    Возвращает цену книги в рублях.

    Args:
        book_id: ID книги, цену которой нужно вернуть.
        connection: connection: Объект соединения для работы с базой данных.

    Returns:
        - Возвращает float объект, если книга существует.
        - None, если книги не существует.
    """

    book_price = connection.execute(
        """SELECT price FROM books WHERE book_id = %s""", (book_id,)
    ).fetchone()[0]

    return book_price


def get_raw_books_by_list_of_id(list_of_id: list[int], connection):
    """
    Возвращает, только те, необработанные записи с данными о книгах, у которых id присутствует в list_of_id.

    Args:
        list_of_id: список id, только с этими id будут браться записи.
        connection: connection: Объект соединения для работы с базой данных.
    Returns:
        - list[tuple], где tuple - одна необработанная запись из БД.
        - None, если записей с такими id не существует.
    """

    raw_books_data = connection.execute(
        """SELECT id, title, price, count FROM books WHERE id = ANY(%s)""",
        (list_of_id,),
    ).fetchall()

    return raw_books_data


def update_data_number_of_books_in_stock(
    books_id: list[int], books_count_in_cart: list[int], connection
):
    """
    Обновляет число книг, которые есть в наличие на складе.

    Args:
        books_id: список id книг, количичество которых нужно обновить.
        books_count_in_cart: Список, в котором каждый элемент - допустимое число, на которое уменьшится
         количество экземляров книги на складе.
        connection: Объект соединения для работы с базой данных

    Returns:
        None.

    """
    rows_to_update = []

    # Формируем список значений, которые будут попарно подставляться за место (%s, %s)
    for book_id, book_count_in_cart in zip(books_id, books_count_in_cart):
        rows_to_update.append(book_id)
        rows_to_update.append(book_count_in_cart)

    # Динамически формируем sql запрос для обновления данных о количестве книг в наличие.
    # Выполняем сформированный запрос.
    values_rows = ", ".join(["(%s, %s)"] * len(books_id))
    update_query = f"""
           UPDATE books AS bk
           SET count = bk.count - bk_c.column2
           FROM (VALUES {values_rows}) AS bk_c
           WHERE bk.id = bk_c.column1
        """
    connection.execute(update_query, rows_to_update)

    return None
