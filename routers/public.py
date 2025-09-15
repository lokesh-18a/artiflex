# routers/public.py - THE CLEAN AND FINAL VERSION

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import crud
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Fetch all data for our dynamic homepage using the new CRUD functions
    trending_products = crud.get_trending_products(db, limit=8)
    # The CRUD function returns a list of tuples, e.g., [('Pottery',), ('Woodwork',)]
    # We need to extract the first item from each tuple.
    categories = [category[0] for category in crud.get_all_categories(db) if category[0]]
    top_artists = crud.get_all_artists(db, limit=8)

    user = request.session.get("user")
    context = {
        "request": request,
        "user": user,
        "trending_products": trending_products,
        "categories": categories,
        "top_artists": top_artists,
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
    products = crud.get_products_by_category(db, category_name=category_name)
    user = request.session.get("user")
    
    context = {
        "request": request,
        "user": user,
        "products": products,
        "category_name": category_name,
        "currency": "INR",
        "conversion_rate": 83.0
    }
    return templates.TemplateResponse("public/category_page.html", context)


@router.get("/artist/{artist_id}", response_class=HTMLResponse)
async def view_artist_profile(request: Request, artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(models.User).filter(models.User.id == artist_id, models.User.role == models.UserRole.ARTIST).first()
    if not artist:
        return HTMLResponse("Artist not found", status_code=404)
    
    products = crud.get_products_by_owner(db, owner_id=artist_id)
    user = request.session.get("user")
    
    context = {
        "request": request,
        "user": user,
        "artist": artist,
        "products": products,
        "currency": "INR",
        "conversion_rate": 83.0
    }
    return templates.TemplateResponse("public/artist_profile.html", context)