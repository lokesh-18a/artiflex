from sqlalchemy.orm import Session
import models, schemas
from passlib.context import CryptContext
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User CRUD ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Product CRUD ---
def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).order_by(models.Product.id.desc()).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products_by_owner(db: Session, owner_id: int):
    return db.query(models.Product).filter(models.Product.owner_id == owner_id).all()

def create_product(db: Session, name: str, category: str, artist_notes: str, ai_description: str, price: float, stock: int, image_filename: str, owner_id: int):
    db_product = models.Product(
        name=name,
        category=category,
        artist_notes=artist_notes,
        ai_generated_description=ai_description,
        price_usd=price,
        stock=stock,
        image_filename=image_filename,
        owner_id=owner_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# --- Cart CRUD ---
def get_cart_items(db: Session, customer_id: int):
    return (
        db.query(models.CartItem)
        .options(joinedload(models.CartItem.product)) # <--- THIS IS THE FIX
        .filter(models.CartItem.customer_id == customer_id)
        .all()
    )

def add_item_to_cart(db: Session, customer_id: int, product_id: int):
    # Check if item already in cart, if so, increment quantity
    db_item = db.query(models.CartItem).filter_by(customer_id=customer_id, product_id=product_id).first()
    if db_item:
        db_item.quantity += 1
    else:
        db_item = models.CartItem(customer_id=customer_id, product_id=product_id, quantity=1)
        db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def remove_item_from_cart(db: Session, cart_item_id: int, customer_id: int):
    db_item = db.query(models.CartItem).filter_by(id=cart_item_id, customer_id=customer_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()

def clear_customer_cart(db: Session, customer_id: int):
    db.query(models.CartItem).filter(models.CartItem.customer_id == customer_id).delete()
    db.commit()

# --- Order CRUD ---
def create_order(db: Session, customer_id: int, cart_items: List[models.CartItem]):
    total = sum(item.product.price_usd * item.quantity for item in cart_items)
    db_order = models.Order(customer_id=customer_id, total_amount_usd=total)
    db.add(db_order)
    db.commit()
    
    for item in cart_items:
        db_order_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase_usd=item.product.price_usd
        )
        # Decrement stock
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.stock -= item.quantity
        db.add(db_order_item)
    
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders_by_customer(db: Session, customer_id: int):
    return db.query(models.Order).filter(models.Order.customer_id == customer_id).order_by(models.Order.created_at.desc()).all()

def get_orders_for_artist(db: Session, artist_id: int):
    return db.query(models.Order).join(models.OrderItem).join(models.Product).filter(models.Product.owner_id == artist_id).distinct().order_by(models.Order.created_at.desc()).all()

def update_order_status(db: Session, order_id: int, artist_id: int, new_status: models.OrderStatus):
    # Security check: ensure the artist owns a product in this order
    order_to_update = db.query(models.Order).join(models.OrderItem).join(models.Product).filter(models.Order.id == order_id, models.Product.owner_id == artist_id).first()
    if order_to_update:
        order_to_update.status = new_status
        db.commit()
        return order_to_update
    return None

def get_products_by_category(db: Session, category_name: str):
    return db.query(models.Product).filter(models.Product.category == category_name).all()
# crud.py - Add these new functions

from sqlalchemy import func
from sqlalchemy.orm import joinedload # Make sure this is imported

# ... existing functions ...

def get_trending_products(db: Session, limit: int = 4):
    """
    Gets products ordered by the number of times they have been sold.
    """
    return (
        db.query(models.Product)
        .join(models.OrderItem)
        .group_by(models.Product.id)
        .order_by(func.sum(models.OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )

def get_all_categories(db: Session):
    """
    Gets a distinct list of all category names.
    """
    return db.query(models.Product.category).distinct().all()

def get_all_artists(db: Session, limit: int = 8):
    """
    Gets a list of all users with the 'artist' role.
    """
    return (
        db.query(models.User)
        .filter(models.User.role == models.UserRole.ARTIST)
        .options(joinedload(models.User.products)) # Optional: load products for performance
        .limit(limit)
        .all()
    )