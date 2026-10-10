from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import Response

from app.schemes.shop_carts import ResponseShopCartSchema
from app.services.shop_carts import add_product_to_cart, get_processed_user_active_cart
from dependencies import get_user_id_from_access_token, get_connection

router = APIRouter()


@router.get("/carts", tags=["shop_cart"])
def get_cart(
    user_id: int = Depends(get_user_id_from_access_token),
    connection=Depends(get_connection),
) -> ResponseShopCartSchema:
    cart = get_processed_user_active_cart(user_id, connection)

    return cart


@router.post("/carts", tags=["shop_cart"])
def add_book_to_cart(
    book_id: int,
    response: Response,
    user_id: int = Depends(get_user_id_from_access_token),
    connection=Depends(get_connection),
):
    add_product_to_cart(book_id, user_id, connection=connection)

    response.status_code = status.HTTP_201_CREATED

    return response
