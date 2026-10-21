from pydantic import BaseModel


class ResponseJWTTokensSchema(BaseModel):
    access_token: str
    refresh_token: str


class UpdateAccessTokenSchema(BaseModel):
    refresh_token: str


class AddToBlackListTokensSchema(BaseModel):
    access_token: str
    refresh_token: str


class AddToBlackListJWTTokensSchema(ResponseJWTTokensSchema):
    pass
