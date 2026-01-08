from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Enum as SAEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    RESTAURANT = "RESTAURANT"
    COURIER = "COURIER"
    ADMIN = "ADMIN"

class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), index=True)

    restaurant: Mapped[Optional["Restaurant"]] = relationship(back_populates="owner", uselist=False)
    courier_deliveries: Mapped[list["Delivery"]] = relationship(back_populates="courier")

class Restaurant(Base):
    __tablename__ = "restaurants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    address: Mapped[str] = mapped_column(String(300))
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)

    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    owner: Mapped["User"] = relationship(back_populates="restaurant")

    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant")
    orders: Mapped[list["Order"]] = relationship(back_populates="restaurant")

class MenuItem(Base):
    __tablename__ = "menu_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    price: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_items")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)

    address_text: Mapped[str] = mapped_column(String(400))
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), default=OrderStatus.CREATED, index=True)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    delivery: Mapped[Optional["Delivery"]] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), index=True)

    name_snapshot: Mapped[str] = mapped_column(String(160))
    price_snapshot: Mapped[float] = mapped_column(Float)
    qty: Mapped[int] = mapped_column(Integer)

    order: Mapped["Order"] = relationship(back_populates="items")

class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    courier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="delivery")
    courier: Mapped[Optional["User"]] = relationship(back_populates="courier_deliveries")
