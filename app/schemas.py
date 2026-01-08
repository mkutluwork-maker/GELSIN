from pydantic import BaseModel, Field
from typing import List
from .models import UserRole, OrderStatus

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=72)  # bcrypt limit yok ama kisa tutmak iyi
    role: UserRole

class RestaurantCreate(BaseModel):
    name: str
    address: str

class MenuItemCreate(BaseModel):
    name: str
    price: float

class OrderItemCreate(BaseModel):
    menu_item_id: int
    qty: int = Field(ge=1, le=50)

class OrderCreate(BaseModel):
    restaurant_id: int
    address_text: str
    items: List[OrderItemCreate]
    mock_payment_success: bool = True

class OrderItemOut(BaseModel):
    id: int
    menu_item_id: int
    name_snapshot: str
    price_snapshot: float
    qty: int
    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    address_text: str
    status: OrderStatus
    total: float
    items: List[OrderItemOut]
    class Config:
        from_attributes = True
