from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role(str, Enum):
    DATA_ENTRY = "data_entry"
    ADMIN = "admin"
    ROUTER = "router"
    SALES = "sales"


class LeadStatus(str, Enum):
    NEW = "new"
    ROUTED = "routed"
    VISITED = "visited"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_leads: Mapped[list["Lead"]] = relationship(back_populates="data_entry", foreign_keys="Lead.data_entry_id")
    assigned_leads: Mapped[list["Lead"]] = relationship(back_populates="sales", foreign_keys="Lead.sales_id")


class Lead(Base):
    __tablename__ = "leads"
    id: Mapped[int] = mapped_column(primary_key=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    store_name: Mapped[str] = mapped_column(String(160), index=True)
    block: Mapped[str] = mapped_column(String(40), index=True)
    floor: Mapped[int] = mapped_column(Integer, default=1, index=True)
    stall: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    store_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    pic_name: Mapped[str] = mapped_column(String(120))
    pic_position: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(40))
    shipment_type: Mapped[str] = mapped_column(String(30))
    expedition: Mapped[str] = mapped_column(String(80))
    top_country: Mapped[str | None] = mapped_column(String(80), nullable=True)
    top_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    potential_kg: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(30), default=LeadStatus.NEW.value, index=True)
    visit_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    visit_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_entry_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    sales_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_entry: Mapped[User] = relationship(back_populates="created_leads", foreign_keys=[data_entry_id])
    sales: Mapped[User | None] = relationship(back_populates="assigned_leads", foreign_keys=[sales_id])
