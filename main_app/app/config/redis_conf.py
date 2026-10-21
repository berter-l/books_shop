from pydantic import BaseModel


class RedisConfig(BaseModel):
    host: str = "shop-redis"
    port: int = 6379
