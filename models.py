from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class UserRole(str, enum.Enum):
    ARTIST = "artist"
    CUSTOMER = "customer"

# models.py - Update the User model

class User(Base):
    __tablename__ = 'users'
    # --- Existing fields ---
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # --- NEW ARTIST PROFILE FIELDS ---
    profile_picture = Column(String, nullable=True, default='default_avatar.png') # Filename
    studio_name = Column(String, nullable=True)
    bio = Column(String, nullable=True) # This is the description
    skills = Column(String, nullable=True) # We'll store this as a comma-separated string, e.g., "Pottery,Glazing,Sculpting"
    location = Column(String, nullable=True) # e.g., "City, Country"
    phone_contact = Column(String, nullable=True)
    average_rating = Column(Float, default=0.0) # For the future rating system
    
    # --- Existing relationships ---
    products = relationship("Product", back_populates="owner")
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True)
    artist_notes = Column(String)
    ai_generated_description = Column(String)
    price_usd = Column(Float, nullable=False)
    stock = Column(Integer, default=1)
    image_filename = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))
    
    owner = relationship("User", back_populates="products")

class OrderStatus(str, enum.Enum):
    PENDING = "Pending"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELED = "Canceled"

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount_usd = Column(Float)

    shipping_address_line1 = Column(String)
    shipping_city = Column(String)
    shipping_postal_code = Column(String)
    shipping_country = Column(String)
    payment_method = Column(String) # Will store "COD" or "Online"
    
    customer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    price_at_purchase_usd = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, default=1)

    product = relationship("Product")