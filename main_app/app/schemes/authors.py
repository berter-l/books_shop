from pydantic import BaseModel, EmailStr

from app.schemes.books import ResponseOneBookSchema
from app.schemes.users import LoginUserSchema


class AuthorRegistrationSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str


class ResponseOneAuthorSchema(BaseModel):
    author_id: int
    first_name: str
    last_name: str
    email: EmailStr


class ResponseAuthorsSchema(BaseModel):
    authors: list[ResponseOneAuthorSchema]


class AuthorWithBooksSchema(BaseModel):
    author: ResponseOneAuthorSchema
    books: list[ResponseOneBookSchema]


class LoginAuthorsSchema(LoginUserSchema):
    pass
