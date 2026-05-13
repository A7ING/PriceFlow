from datetime import datetime
from db.database import Base
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    products = relationship("Product", back_populates="owner")
    settings = relationship("SystemSettings", back_populates="owner", uselist=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, unique=True, index=True)
    current_price = Column(Float, nullable=True)
    image_url = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="products")

    history = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    checked_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="history")


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    update_freq = Column(String, default="12h")
    notify_drop = Column(Boolean, default=True)
    notify_rise = Column(Boolean, default=False)
    notify_method = Column(String, default="email")
    contact_info = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="settings")
