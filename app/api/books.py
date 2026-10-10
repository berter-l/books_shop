from fastapi import APIRouter, Depends, HTTPException

from app.schemes.books import ResponseOneBookSchema, CreateBooksSchema
from app.services.books import (
    get_processed_books_data,
    create_book as service_create_book,
)
from dependencies import get_connection, get_author_id_from_access_token

router = APIRouter()


@router.get("/books", tags=["books"])
def get_books(
    page: int,
    limit: int,
    connection=Depends(get_connection),
) -> list[ResponseOneBookSchema]:

    books = get_processed_books_data(page, limit, connection)

    return books


@router.post("/books", tags=["books"])
def create_books(
    book_data: CreateBooksSchema,
    connection=Depends(get_connection),
    author_id: int = Depends(get_author_id_from_access_token),
):
    service_create_book(
        book_data.title, book_data.price, book_data.count, author_id, connection
    )

    return None
