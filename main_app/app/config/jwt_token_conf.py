from pydantic import BaseModel


class JWTConfig(BaseModel):
    algorithm: str = "HS256"
    secret_key: str = "e36a3d58-682e-4e79-90b2-5f6380fcf22c"
    access_token_ttl_minute: int = 10
    refresh_token_ttl_minute: int = 60 * 24 * 7
