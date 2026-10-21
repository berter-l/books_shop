from pydantic_settings import BaseSettings

from app.config.jwt_token_conf import JWTConfig

from app.config.db_conf import DBConfig

from main_app.app.config.redis_conf import RedisConfig


class Settings(BaseSettings):
    jwt_config: JWTConfig = JWTConfig()
    db_config: DBConfig = DBConfig()
    redis_config: RedisConfig = RedisConfig()


settings = Settings()
