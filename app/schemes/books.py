from pydantic import BaseModel


class ResponseOneBookSchema(BaseModel):
    title: str
    price: float
    count: int


class CreateBooksSchema(BaseModel):
    title: str
    price: float
    count: int
