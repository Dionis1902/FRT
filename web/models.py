from pydantic import BaseModel


class SmallAccountInfo(BaseModel):
    user_id: int
    first_name: str
    last_name: str | None
    username: str | None
    county_code: str
    phone_number: str
    is_premium: bool
    in_live_task: bool


class AccountInfo(SmallAccountInfo):
    session_string: str
    bio: str | None
    photos: list[str]
    proxy: str | None
    spam_block: int


class UpdateAccount(BaseModel):
    first_name: str
    last_name: str | None
    username: str | None
    bio: str | None


class BaseBody(BaseModel):
    tab_id: str
