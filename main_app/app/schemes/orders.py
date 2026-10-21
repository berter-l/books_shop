from datetime import datetime

from pydantic import BaseModel


class CreateOrderSchema(BaseModel):
    book_id: int


class ResponseOrderBase(BaseModel):
    order_id: int
    created_at: datetime
    status: str
    total_amount: float
    user_id: int


class ResponseOrderDetailSchema(ResponseOrderBase):
    book_name: str


class ResponseManyOrdersSchema(BaseModel):
    orders: list[ResponseOrderBase]
