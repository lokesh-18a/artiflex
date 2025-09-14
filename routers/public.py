# routers/public.py - The Stable Pattern

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import crud
from collections import defaultdict

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # This is the safe pattern we established
    user = request.session.get("user")
    products = crud.get_products(db, limit=30) # Fetch more products to have enough for categories
    # Group products by their category
    categorized_products = defaultdict(list)
    for product in products:
        if product.category: # Ensure product has a category
            categorized_products[product.category].append(product)
    # ==========================
    
    context = {
        "request": request,
        "user": user,
        "categorized_products": categorized_products, # Pass the new grouped dictionary
        "currency": "INR",
        "conversion_rate": 83.0
    }
    return templates.TemplateResponse("public/index.html", context)

@router.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    user = request.session.get("user")
    product = crud.get_product(db, product_id=product_id)
    if not product:
        return HTMLResponse("Product not found", status_code=404)
        
    context = {
        "request": request,
        "user": user,
        "product": product,
        "currency": "INR",
        "conversion_rate": 83.0
    }
    return templates.TemplateResponse("public/product_detail.html", context)

@router.get("/category/{category_name}", response_class=HTMLResponse)
async def view_category(request: Request, category_name: str, db: Session = Depends(get_db)):
    # This is a new CRUD function we need to create
    products = crud.get_products_by_category(db, category_name=category_name)
    
    user = request.session.get("user")
    context = {
        "request": request,
        "user": user,
        "products": products,
        "category_name": category_name, # Pass the name to the template
        "currency": "INR",
        "conversion_rate": 83.0
    }
    return templates.TemplateResponse("public/category_page.html", context)