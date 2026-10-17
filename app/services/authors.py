from fastapi import HTTPException
from starlette import status

from app.schemes.authors import (
    ResponseOneAuthorSchema,
    ResponseAuthorsSchema,
    AuthorWithBooksSchema,
)
from app.schemes.jwt import ResponseJWTTokensSchema
from app.services.books import get_books_by_author_id, build_books_data_response
from database import pool
from handler import handle_not_found, handle_unique
from security import get_hashed_password, get_jwt_tokens, is_password_correct


def get_processed_author_with_books(author_id: int, connection):
    """
    Возвращает данные об авторе и его книгах.

    Управляет транзакцией: открывает и откатывает все изменения, если произошла ошибка, или сохраняет изменения.
    Управляет соединением: получает открытое соединение и в конце в любом случае закрывает.

    Args:
        author_id: ID, для которого нужно вернуть его данные и данные о его книгах.
        connection: объект соединения для работы с БД.

    Returns:
        Объект AuthorWithBooksSchema с атрибутами (author - ResponseOneAuthorSchema, books - list[ResponseOneBookSchema]).
    """

    connection.execute("""BEGIN""")
    try:
        raw_books_data = get_books_by_author_id(
            author_id, connection, auto_return_to_pool=False
        )

        raw_author_data = get_author_by_id(
            author_id, connection, auto_return_to_pool=False
        )

        processed_author_with_books_data = build_author_with_books_response(
            raw_books_data, raw_author_data
        )
        connection.execute("""COMMIT""")

        pool.putconn(connection)

        return processed_author_with_books_data

    except:
        connection.execute("""ROLLBACK""")
        pool.putconn(connection)


def get_authors(connection):
    """
    Возвращает необработанные данные об авторах.

    Args:
        connection: объект соединения для работы с БД.

    Returns:
        - list[tuple], где tuple представляет одну запись из БД.
        - None, если авторов нету.
    """

    raw_authors_data = connection.execute(f"""
        SELECT id, first_name, last_name, email FROM authors;
        """).fetchall()

    pool.putconn(connection)

    return raw_authors_data


def get_author_by_id(author_id: int, connection, auto_return_to_pool=True):
    """
    Возвращает необработанные данные об авторе, по его ID.

    Args:
        author_id: ID автора, чьи данные нужно получить.
        connection: объект соединения для работы с БД.
        auto_return_to_pool: Флаг, если True (по умолчанию), то функция вернёт соединение в пул сама, если False,
         то соединение должна вернуть, вызывающая функция.

    Returns:
        - Объект tuple представляющий одну запись с данными об авторе, из БД.
        - None, если автора с таким ID нету в БД.
    """

    raw_author_data = connection.execute(
        f"""
        SELECT id, first_name, last_name, email FROM authors WHERE id = %s;""",
        (author_id,),
    ).fetchone()

    if auto_return_to_pool:
        pool.putconn(connection)

    return raw_author_data


def register_author(first_name, last_name, email, password, connection):
    """
    Регестрирует автора.

    Args:
        first_name: имя автора.
        last_name: фамилия автора.
        email: почта автора.
        password: необработанный пароль автора.
        connection: объект соединения для работы с БД.

    Returns:
        - объект ResponseJWTTokensSchema с атрибутами (access_token, refresh_token), представляющий jwt токены.

    Raises:
        HTTPException:
            - status_code=HTTP_409_CONFLICT, detail="Email already registered", если автор с такой почтой уже существует.
    """

    if is_author_exists(email, connection):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    hashed_password = get_hashed_password(password)

    author_id = save_author_data_to_db(
        first_name, last_name, email, hashed_password, connection=connection
    )

    jwt_tokens = get_jwt_tokens({"author_id": author_id})

    return ResponseJWTTokensSchema(
        access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
    )


def build_author_with_books_response(
    raw_books_data, raw_author_data
) -> AuthorWithBooksSchema:
    """
    Формирует объект с обработанными данными о книгах автора.

    Args:
        raw_books_data: необработанные данные о книгах автора.
        raw_author_data: необработанные данные об авторе.

    Returns:
        - Объект AuthorWithBooksSchema с атрибутами (author - ResponseOneAuthorSchema, books - list[ResponseOneBookSchema]).
    """

    processed_author = build_author_data_response(raw_author_data)

    processed_books = build_books_data_response(raw_books_data)

    return AuthorWithBooksSchema(author=processed_author, books=processed_books)


@handle_not_found
def build_authors_response(raw_authors_data: list[tuple]) -> ResponseAuthorsSchema:
    """
    Формирует, обработанные объекты, представляющие данные авторов.

    Args:
        raw_authors_data: необработанные данные авторов, где каждый tuple - отдельная запись в БД.

    Returns:
        -Объект ResponseAuthorsSchema с атрибутом authors, в котором хранятся объекты
          ResponseOneAuthorSchema с атрибутами(author_id, first_name, last_name, email)

    Raises:
        HTTPException:
            -  status_code=HTTP_404_NOT_FOUND, detail="Not found.", если переданный аргумент = None.
    """

    processed_authors = []

    for row in raw_authors_data:
        processed_author = ResponseOneAuthorSchema(
            author_id=row[0], first_name=row[1], last_name=row[2], email=row[3]
        )
        processed_authors.append(processed_author)

    return ResponseAuthorsSchema(authors=processed_authors)


@handle_not_found
def build_author_data_response(raw_author_data) -> ResponseOneAuthorSchema:
    """
    Формирует объект, представляющий обработанные данные автора.

    Args:
        raw_author_data: необработанные данные об авторе, представленные как объект tuple где каждый элемент это отдельное поле из БД.

    Returns:
        - Объект ResponseOneAuthorSchema содержащий атрибуты(author_id, first_name, last_name, email)

    Raises:
        HTTPException:
            -  status_code=HTTP_404_NOT_FOUND, detail="Not found.", если переданный аргумент = None.
    """

    return ResponseOneAuthorSchema(
        author_id=raw_author_data[0],
        first_name=raw_author_data[1],
        last_name=raw_author_data[2],
        email=raw_author_data[3],
    )


def get_processed_author_by_id(author_id: int, connection):
    """
    Возвращает обработанные данные для заданного автора.

    Args:
        author_id: ID автора, чьи данные нужно получить.
        connection: объект соединения для работы с БД.

    Returns:
        - Объект ResponseOneAuthorSchema, представляющий обработанные данные автора, с атрибутами(author_id, first_name, last_name, email).
    """

    raw_author_data = get_author_by_id(author_id, connection)

    processed_author_data = build_author_data_response(raw_author_data)

    return processed_author_data


def get_processed_authors_data(connection):
    """
    Возвращает обработанные данные об авторах.

    Args:
        connection: объект соединения, для работы с БД.

    Returns:
        - Возвращает list[ResponseOneAuthorSchema] где в каждом объекте из списка есть атрибуты (author_id, first_name, last_name, email).
    """

    raw_authors_data = get_authors(connection)

    processed_authors = build_authors_response(raw_authors_data)

    return processed_authors


@handle_unique
def save_author_data_to_db(
    first_name, last_name, email, hashed_password, connection
) -> int:
    """
    Сохраняет данные об авторе в БД.

    Args:
        first_name: Имя автора.
        last_name: Фамилия автора.
        email: Почта автора.
        hashed_password: Хешированный пароль.
        connection: объект соединения для работы с БД.

    Returns:
        author_id - ID записи об авторе в БД.

    Raises:
        HTTPException:
            -  status_code=HTTP_409_CONFLICT, detail="Already exists.", если автор с такой почтой уже существует.
    """

    author_id = connection.execute(
        f"""
               INSERT INTO authors (first_name, last_name, email, password)
               VALUES(%s, %s, %s, %s)
               RETURNING id;
               """,
        (first_name, last_name, email, hashed_password),
    ).fetchone()[0]

    pool.putconn(connection)

    return author_id


def get_author_by_email(email, connection):
    """
    Возвращает необработанные данные автора.

    Args:
        email: Почта по которой, ищет автора.
        connection: Объект соединения для работы с базой данных.

    Returns:
        - Объект tuple, который представляет необработанные данные автора.
        - None, если автора с такой почтой не существует.
    """

    author = connection.execute(
        """SELECT id, password, email FROM authors WHERE email = %s;""", (email,)
    ).fetchone()

    return author


def login_author(email, password, connection):
    """
    Аутентифицирует автора по email, password.

    Выдаёт jwt токены, если введеные данные оказались верными.
    Возвращает соединение с БД в пул, в любом случае.

    Args:
        email: почта, по которой будет искаться автор для дальнейшей проверки.
        password: введеный пароль, который будет использован для сравнения с хешированным паролем из БД.
        connection: объект соединения для работы с БД.

    Returns:
        - объект ResponseJWTTokensSchema с атрибутами (access_token, refresh_token), представляющий jwt токены.

    Raises:
        HTTPException:
            - status_code=400, detail="Incorrect email or password".
    """

    author = get_author_by_email(email, connection)
    if author is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    hashed_password = author[
        1
    ].encode()  # Переводим в байты, т.к метод для проверки паролей работает только с ними.

    if is_password_correct(password.encode(), hashed_password):
        jwt_tokens = get_jwt_tokens({"author_id": author[0]})
        pool.putconn(connection)
        return ResponseJWTTokensSchema(
            access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
        )

    pool.putconn(connection)
    raise HTTPException(status_code=400, detail="Incorrect email or password")


def is_author_exists(email: str, connection) -> bool:
    """
    Проверяет существует ли автор в базе данных.

    Args:
        email: Почта, по которой проверяем, существует ли пользователь.
        connection: Объект соединения для работы с базой данных.

    Returns:
        - False, если автора с такой почтой нету.
        - True, если автор с такой почтой существует.
    """

    author = get_author_by_email(email, connection)
    if author is not None:
        return True
    return False
