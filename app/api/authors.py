from fastapi import APIRouter, Depends

from app.schemes.authors import (
    AuthorRegistrationSchema,
    ResponseAuthorsSchema,
    AuthorWithBooksSchema,
    LoginAuthorsSchema,
)
from app.schemes.jwt import ResponseJWTTokensSchema
from app.services.authors import (
    get_processed_authors_data,
    register_author as service_register_author,
    get_author_with_books as service_get_author_with_books,
    get_processed_author_by_id,
    login_author as service_login_author,
)
from dependencies import get_connection, get_author_id_from_access_token

router = APIRouter()


@router.post("/authors", tags=["authors"])
def register_author(
    registration_details: AuthorRegistrationSchema, connection=Depends(get_connection)
) -> ResponseJWTTokensSchema:
    jwt_tokens = service_register_author(
        registration_details.first_name,
        registration_details.last_name,
        registration_details.email,
        registration_details.password,
        connection=connection,
    )

    return jwt_tokens


@router.get("/authors", tags=["authors"])
def get_authors(
    connection=Depends(get_connection),
) -> ResponseAuthorsSchema:
    authors = get_processed_authors_data(connection=connection)

    return authors


@router.get("/authors/{author_id}", tags=["authors"])
def get_author_by_id(author_id: int, connection=Depends(get_connection)):
    author = get_processed_author_by_id(author_id, connection=connection)
    return author


@router.get("/authors/{author_id}/books", tags=["authors"])
def get_author_with_books(
    author_id: int = Depends(get_author_id_from_access_token),
    connection=Depends(get_connection),
) -> AuthorWithBooksSchema:

    author = service_get_author_with_books(author_id, connection=connection)
    return author


@router.post("/authors/login", tags=["authors"])
def login_author(login_details: LoginAuthorsSchema, connection=Depends(get_connection)):
    jwt_tokens = service_login_author(
        login_details.email, login_details.password, connection=connection
    )
    return jwt_tokens
