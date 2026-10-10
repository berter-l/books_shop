from app.schemes.books import ResponseOneBookSchema
from database import pool
from handler import handle_not_found


def get_books_by_author_id(author_id: int, connection, auto_return_to_pool=True):

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
    processed_books = []

    for raw_book in raw_books_data:
        processed_books.append(
            ResponseOneBookSchema(
                title=raw_book[0], price=raw_book[1], count=raw_book[2]
            )
        )

    return processed_books


def get_raw_books_data(page: int, limit: int, connection):
    raw_books_data = connection.execute(
        """
        SELECT title, price, count FROM books OFFSET %s LIMIT %s
        """,
        ((page - 1) * limit, limit),
    ).fetchall()

    return raw_books_data


def get_processed_books_data(page: int, limit: int, connection):
    raw_books_data = get_raw_books_data(page=page, limit=limit, connection=connection)

    processed_books_data = build_books_data_response(raw_books_data)

    return processed_books_data


def create_book(title, price, count, author_id, connection):
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
    book_price = connection.execute(
        """SELECT price FROM books WHERE book_id = %s""", (book_id,)
    ).fetchone()[0]

    return book_price


def get_raw_books_by_list_of_id(list_of_id: list[int], connection):
    raw_books_data = connection.execute(
        """SELECT id, title, price, count FROM books WHERE id = ANY(%s)""",
        (list_of_id,),
    )

    return raw_books_data
