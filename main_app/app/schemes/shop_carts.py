from pydantic import BaseModel


class CartItem(BaseModel):
    quantity: int
    book_name: str
    price: float


class ResponseShopCartSchema(BaseModel):
    items: list[CartItem]
    total_amount: float
