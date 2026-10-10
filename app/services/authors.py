from fastapi import HTTPException

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


def get_author_with_books(author_id: int, connection):
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
    raw_authors_data = connection.execute(f"""
        SELECT id, first_name, last_name, email FROM authors;
        """).fetchall()

    pool.putconn(connection)

    return raw_authors_data


def get_author_by_id(author_id: int, connection, auto_return_to_pool=True):
    raw_author_data = connection.execute(
        f"""
        SELECT id, first_name, last_name, email FROM authors WHERE id = %s;""",
        (author_id,),
    ).fetchone()

    if auto_return_to_pool:
        pool.putconn(connection)

    return raw_author_data


def register_author(first_name, last_name, email, password, connection):
    if is_author_exists(email, connection):
        raise HTTPException(status_code=400, detail="Email already registered")

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

    processed_author = build_author_data_response(raw_author_data)

    processed_books = build_books_data_response(raw_books_data)

    return AuthorWithBooksSchema(author=processed_author, books=processed_books)


@handle_not_found
def build_authors_response(raw_authors_data) -> ResponseAuthorsSchema:
    processed_authors = []

    for row in raw_authors_data:
        processed_author = ResponseOneAuthorSchema(
            author_id=row[0], first_name=row[1], last_name=row[2], email=row[3]
        )
        processed_authors.append(processed_author)

    return ResponseAuthorsSchema(authors=processed_authors)


@handle_not_found
def build_author_data_response(raw_author_data) -> ResponseOneAuthorSchema:
    return ResponseOneAuthorSchema(
        author_id=raw_author_data[0],
        first_name=raw_author_data[1],
        last_name=raw_author_data[2],
        email=raw_author_data[3],
    )


def get_processed_author_by_id(author_id: int, connection):
    raw_author_data = get_author_by_id(author_id, connection)

    processed_author_data = build_author_data_response(raw_author_data)

    return processed_author_data


def get_processed_authors_data(connection):
    raw_authors_data = get_authors(connection)

    processed_authors = build_authors_response(raw_authors_data)

    return processed_authors


@handle_unique
def save_author_data_to_db(
    first_name, last_name, email, hashed_password, connection
) -> int:
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
    author = connection.execute(
        """SELECT id, password, email FROM authors WHERE email = %s;""", (email,)
    ).fetchone()

    return author


def login_author(email, password, connection):
    author = get_author_by_email(email, connection)
    if author is None:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    hashed_password = author[1].encode()

    if is_password_correct(password.encode(), hashed_password):
        jwt_tokens = get_jwt_tokens({"author_id": author[0]})
        pool.putconn(connection)
        return ResponseJWTTokensSchema(
            access_token=jwt_tokens[0], refresh_token=jwt_tokens[1]
        )

    raise HTTPException(status_code=400, detail="Incorrect email or password")


def is_author_exists(email: str, connection) -> bool:
    author = get_author_by_email(email, connection)

    if author is not None:
        return True

    return False