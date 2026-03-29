from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime

class StoreNameEnum(str, Enum):
    AMAZON = "amazon"
    NEWEGG = "newegg"
    BESTBUY = "bestbuy"
    FLIPKART = "flipkart"

class NotificationTypeEnum(str, Enum):
    DISCORD = "discord"
    EMAIL = "email"

class TrackRequest(BaseModel):
    product_url: str
    target_price: float = Field(gt=0)
    notification_type: NotificationTypeEnum
    contact_info: str
    user_id: str

class TrackedItemResponse(BaseModel):
    item_id: str
    user_id: str
    product_url: str
    product_name: str
    product_image_url: str
    store: StoreNameEnum
    current_price: float
    target_price: float
    notification_type: NotificationTypeEnum
    contact_info: str
    created_at: str
    updated_at: str

class PriceHistoryEntry(BaseModel):
    item_id: str
    timestamp: str
    price: float

class TrendingDealResponse(BaseModel):
    item_id: str
    product_name: str
    product_image_url: str
    product_url: str
    store: StoreNameEnum
    previous_price: float
    current_price: float
    drop_percentage: float

class ApiResponse(BaseModel):
    data: Optional[object] = None
    message: str
    success: bool

def generate_item_id() -> str:
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"
