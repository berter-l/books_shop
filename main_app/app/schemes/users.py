from pydantic import BaseModel, EmailStr, PositiveInt

from app.schemes.orders import ResponseOrderDetailSchema


class UserRegistrationSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    age: PositiveInt
    password: str


class ResponseUserProfileSchema(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    age: int
    balance: float


class ResponseUserOrdersSchema(BaseModel):
    orders: list[ResponseOrderDetailSchema]


class LoginUserSchema(BaseModel):
    email: EmailStr
    password: str
