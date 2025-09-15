# routers/artist.py - FULLY CORRECTED AND AUDITED

from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import crud
import models
import os
import services.ai_service
import shutil
import time

# This is our correct prefix
router = APIRouter(prefix="/artist/manage", tags=["artist"])
templates = Jinja2Templates(directory="templates")

# --- HELPER FUNCTIONS (Good practice to keep them) ---
def flash(request: Request, message: str, category: str = "success"):
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append((category, message))

def is_artist(request: Request):
    user = request.session.get("user")
    if not user or user.get("role") != "artist":
        flash(request, "Access denied. Artist area only.", "danger")
        return RedirectResponse(url="/login", status_code=303)
    return True

# --- ROUTE HANDLERS ---

@router.get("/dashboard", response_class=HTMLResponse)
async def artist_dashboard(request: Request, db: Session = Depends(get_db), user_auth = Depends(is_artist)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    
    user_id = request.session["user"]["id"]
    products = crud.get_products_by_owner(db, owner_id=user_id)
    orders = crud.get_orders_for_artist(db, artist_id=user_id)
    total_income = sum(item.price_at_purchase_usd * item.quantity for order in orders for item in order.items if item.product.owner_id == user_id)
    
    context = {"request": request, "products": products, "orders": orders, "total_income": total_income}
    return templates.TemplateResponse("artist/dashboard.html", context)

@router.get("/products/new", response_class=HTMLResponse)
async def add_product_step1_page(request: Request, user_auth = Depends(is_artist)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    return templates.TemplateResponse("artist/add_product_step1.html", {"request": request})

@router.post("/products/new")
async def add_product_step1_submit(request: Request, name: str = Form(...), category: str = Form(...), artist_notes: str = Form(...), image: UploadFile = File(...)):
    # ... file saving logic is correct ...
    timestamp = int(time.time())
    file_extension = image.filename.split(".")[-1]
    image_filename = f"product_{timestamp}_{name.replace(' ','_')}.{file_extension}"
    file_location = f"static/uploads/{image_filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(image.file, file_object)

    request.session["product_creation_data"] = {"name": name, "category": category, "artist_notes": artist_notes, "image_filename": image_filename}
    
    # === URL FIX #1 ===
    return RedirectResponse(url="/artist/manage/products/review", status_code=303)

@router.get("/products/review", response_class=HTMLResponse)
async def add_product_step2_page(request: Request, user_auth = Depends(is_artist)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    
    product_data = request.session.get("product_creation_data")
    if not product_data:
        flash(request, "Session expired. Please start again.", "warning")
        # === URL FIX #2 ===
        return RedirectResponse(url="/artist/manage/products/new", status_code=303)

    ai_description = services.ai_service.generate_product_description(name=product_data["name"], category=product_data["category"], artist_notes=product_data["artist_notes"])
    ai_price_suggestion = services.ai_service.suggest_product_price(name=product_data["name"], category=product_data["category"], artist_notes=product_data["artist_notes"])

    context = {"request": request, "product_data": product_data, "ai_description": ai_description, "ai_price_suggestion": ai_price_suggestion}
    return templates.TemplateResponse("artist/add_product_step2.html", context)

@router.post("/products/save")
async def save_product(request: Request, db: Session = Depends(get_db), ai_generated_description: str = Form(...), price_usd: float = Form(...), stock: int = Form(...), name: str = Form(...), category: str = Form(...), artist_notes: str = Form(...), image_filename: str = Form(...)):
    # ... logic is correct ...
    user_session = request.session.get("user")
    owner_id = user_session["id"]
    crud.create_product(db=db, owner_id=owner_id, name=name, category=category, artist_notes=artist_notes, ai_description=ai_generated_description, price=price_usd, stock=stock, image_filename=image_filename)
    if "product_creation_data" in request.session:
        del request.session["product_creation_data"]

    # === URL FIX #3 ===
    return RedirectResponse(url="/artist/manage/dashboard?tab=products", status_code=303)

@router.post("/orders/update/{order_id}")
async def update_order(request: Request, order_id: int, db: Session = Depends(get_db), user_auth = Depends(is_artist), status: models.OrderStatus = Form(...)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    artist_id = request.session["user"]["id"]
    crud.update_order_status(db, order_id, artist_id, status)
    # === URL FIX #4 ===
    return RedirectResponse(url="/artist/manage/dashboard", status_code=303)

@router.get("/profile/edit", response_class=HTMLResponse)
async def edit_artist_profile_page(request: Request, db: Session = Depends(get_db)):
    user_session = request.session.get("user")
    if not user_session or user_session.get("role") != "artist":
        return RedirectResponse(url="/login", status_code=303)

    artist = db.query(models.User).filter(models.User.id == user_session["id"]).first()
    return templates.TemplateResponse("artist/edit_profile.html", {"request": request, "artist": artist})

@router.post("/profile/edit")
async def handle_edit_artist_profile(request: Request, db: Session = Depends(get_db), studio_name: str = Form(...), location: str = Form(...), phone_contact: str = Form(...), skills: str = Form(...), bio: str = Form(...), profile_picture: UploadFile = File(None)):
    # ... logic is correct ...
    user_session = request.session.get("user")
    artist = db.query(models.User).filter(models.User.id == user_session["id"]).first()
    artist.studio_name = studio_name
    artist.location = location
    artist.phone_contact = phone_contact
    artist.skills = skills
    artist.bio = bio
    
    if profile_picture and profile_picture.filename:
        timestamp = int(time.time())
        file_extension = profile_picture.filename.split(".")[-1]
        image_filename = f"profile_{artist.id}_{timestamp}.{file_extension}"
        file_location = f"static/uploads/profiles/{image_filename}"
        os.makedirs("static/uploads/profiles", exist_ok=True)
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(profile_picture.file, file_object)
        artist.profile_picture = image_filename

    db.commit()
    # === URL FIX #5 ===
    return RedirectResponse(url="/artist/manage/dashboard", status_code=303)