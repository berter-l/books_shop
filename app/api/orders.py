from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import Response

from app.services.orders import place_an_order
from dependencies import get_user_id_from_access_token, get_connection

router = APIRouter()


@router.post("/orders", tags=["orders"])
def create_order(
    response: Response,
    user_id: int = Depends(get_user_id_from_access_token),
    connection=Depends(get_connection),
):
    place_an_order(user_id, connection)

    response.status_code = status.HTTP_201_CREATED

    return response
