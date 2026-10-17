from fastapi import APIRouter, Depends

from app.schemes.jwt import ResponseJWTTokensSchema
from app.schemes.orders import ResponseManyOrdersSchema
from app.services.orders import get_processed_user_orders
from app.services.users import (
    register_user as service_register_user,
    get_user_profile as service_get_user_profile,
    login_user as service_login_user,
)
from app.schemes.users import (
    UserRegistrationSchema,
    ResponseUserProfileSchema,
    ResponseUserOrdersSchema,
    LoginUserSchema,
)
from dependencies import get_connection, get_user_id_from_access_token
from session import redis_client

router = APIRouter()


@router.post("/users", tags=["users"])
def register_user(
    registration_details: UserRegistrationSchema, connection=Depends(get_connection)
) -> ResponseJWTTokensSchema:
    jwt_tokens = service_register_user(
        registration_details.first_name,
        registration_details.last_name,
        registration_details.email,
        registration_details.age,
        registration_details.password,
        connection,
    )
    return jwt_tokens


@router.get("/users/me", tags=["users"])
def get_user_profile(
    user_id: int = Depends(get_user_id_from_access_token),
    connection=Depends(get_connection),
) -> ResponseUserProfileSchema:
    user_profile = service_get_user_profile(user_id, connection)

    return user_profile


@router.get("/users/orders", tags=["users"])
def get_user_orders(
    user_id: int = Depends(get_user_id_from_access_token),
    connection=Depends(get_connection),
) -> ResponseManyOrdersSchema:

    orders = get_processed_user_orders(user_id, connection)

    return orders


@router.post("/users/login", tags=["users"])
def login_user(
    login_details: LoginUserSchema, connection=Depends(get_connection)
) -> ResponseJWTTokensSchema:
    jwt_tokens = service_login_user(
        login_details.email, login_details.password, connection
    )
    return jwt_tokens
