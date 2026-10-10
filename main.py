import uvicorn
from fastapi import FastAPI

from database import pool, create_all_tables
from app.api.authors import router as authors_router
from app.api.users import router as users_router
from app.api.books import router as books_router
from app.api.shop_carts import router as shop_card_router
from app.api.orders import router as orders_router

app = FastAPI()

app.include_router(authors_router)
app.include_router(users_router)
app.include_router(books_router)
app.include_router(shop_card_router)
app.include_router(orders_router)


if __name__ == "__main__":
    create_all_tables()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
