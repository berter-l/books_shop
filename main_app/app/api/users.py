from fastapi import APIRouter, Depends

from ..schemes.jwt import (
    ResponseJWTTokensSchema,
    AddToBlackListJWTTokensSchema,
)
from ..schemes.orders import ResponseManyOrdersSchema
from ..schemes.users import (
    UserRegistrationSchema,
    ResponseUserProfileSchema,
    LoginUserSchema,
)
from ..services.orders import get_processed_user_orders
from ..services.users import (
    register_user as service_register_user,
    get_user_profile as service_get_user_profile,
    login_user as service_login_user,
    logout_user as service_logout_user,
    top_up_balance as service_top_up_balance,
    verify_email as service_verify_email,
    check_verify_code,
)
from dependencies import get_connection, get_user_id_from_access_token

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


@router.post("/users/verify-email", tags=["users"])
def verify_email(
    registration_details: UserRegistrationSchema, connection=Depends(get_connection)
):
    service_verify_email(registration_details.email, connection)
    return None


@router.post("/users/verify-code", tags=["users"])
def verify_code(registration_details: UserRegistrationSchema, code: str):
    check_verify_code(registration_details.email, code)
    return None


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


@router.post("/users/logout", tags=["users"])
def logout_user(
    logout_details: AddToBlackListJWTTokensSchema, connection=Depends(get_connection)
):
    service_logout_user(
        logout_details.access_token, logout_details.refresh_token, connection
    )

    return None


@router.post("/users/balance", tags=["users"])
def top_up_balance(
    amount: float,
    user_id: int = Depends(get_user_id_from_access_token),
    connection=Depends(get_connection),
):
    service_top_up_balance(amount, user_id, connection)
    return None
