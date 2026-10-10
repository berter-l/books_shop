from pydantic_settings import BaseSettings

from app.config.jwt_token_conf import JWTConfig


class Settings(BaseSettings):
    jwt_config: JWTConfig = JWTConfig()


settings = Settings()
