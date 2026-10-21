from fastapi import APIRouter, Depends, Header

from ..schemes.admins import ResponseAllUsersOrders
from dependencies import get_connection
from ..services.admins import (
    get_processed_users_orders,
    update_order_status as service_update_order_status,
)
from dependencies import check_authorization_admin_token

router = APIRouter()


@router.get("/admins/user-orders", tags=["admins"])
def get_users_orders(
    connection=Depends(get_connection), token=Depends(check_authorization_admin_token)
) -> ResponseAllUsersOrders:
    processed_users_orders = get_processed_users_orders(connection)

    return processed_users_orders


@router.post("/admins/orders/{order_id}", tags=["admins"])
def update_order_status(
    order_id: int,
    connection=Depends(get_connection),
    token=Depends(check_authorization_admin_token),
):
    service_update_order_status(connection, order_id)
