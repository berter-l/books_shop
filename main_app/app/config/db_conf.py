from pydantic import BaseModel


class DBConfig(BaseModel):
    port: int = 5432
    host: str = "shop-postgres"
    db_name: str = "shop_db"
    username: str = "shop"
    password: str = "1234"
    min_connections: int = 10
    max_connections: int = 100

    @property
    def db_url(self):
        return f"postgres://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
