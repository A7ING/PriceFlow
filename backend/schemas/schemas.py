from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PriceHistoryResponse(BaseModel):
    price: float
    checked_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    url: str


class ProductCreate(ProductBase):
    pass


class ProductResponse(BaseModel):
    id: int
    name: str
    url: str
    current_price: float | None = None
    image_url: str | None = None
    added_at: datetime
    history: list[PriceHistoryResponse] = []
    model_config = ConfigDict(from_attributes=True)


class SettingsUpdate(BaseModel):
    update_freq: str
    notify_drop: bool
    notify_rise: bool
    notify_method: str
    contact_info: str | None = None


class SettingsResponse(BaseModel):
    update_freq: str
    notify_drop: bool
    notify_rise: bool
    notify_method: str
    contact_info: str | None = None
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str = Field(..., pattern=r"^[a-zA-Z0-9_]+$", min_length=3, max_length=20)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
