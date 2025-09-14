from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from routers.auth_helpers import login_required
import crud, services.ai_service, shutil, time
from models import User, OrderStatus

router = APIRouter(prefix="/artist", tags=["artist"])
templates = Jinja2Templates(directory="templates")

def flash(request: Request, message: str, category: str = "success"):
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append((category, message))

def is_artist(request: Request):
    user = request.session.get("user")
    if not user or user.get("role") != "artist":
        flash(request, "Access denied. Artist area only.", "danger")
        return RedirectResponse(url="/", status_code=303)
    return True

@router.get("/dashboard", response_class=HTMLResponse)
async def artist_dashboard(request: Request, db: Session = Depends(get_db), user_auth = Depends(is_artist)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    
    user_id = request.session["user"]["id"]
    products = crud.get_products_by_owner(db, owner_id=user_id)
    orders = crud.get_orders_for_artist(db, artist_id=user_id)
    
    total_income = sum(item.price_at_purchase_usd * item.quantity for order in orders for item in order.items if item.product.owner_id == user_id)
    
    context = {
        "request": request, 
        "products": products, 
        "orders": orders,
        "total_income": total_income
    }
    return templates.TemplateResponse("artist/dashboard.html", context)

@router.get("/products/new", response_class=HTMLResponse)
async def add_product_step1_page(request: Request, user_auth = Depends(is_artist)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    return templates.TemplateResponse("artist/add_product_step1.html", {"request": request})

@router.post("/products/new")
async def add_product_step1_submit(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    artist_notes: str = Form(...),
    image: UploadFile = File(...)
):
    # Save the uploaded file
    timestamp = int(time.time())
    file_extension = image.filename.split(".")[-1]
    image_filename = f"product_{timestamp}_{name.replace(' ','_')}.{file_extension}"
    file_location = f"static/uploads/{image_filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(image.file, file_object)

    # Store data in session to pass to step 2
    request.session["product_creation_data"] = {
        "name": name,
        "category": category,
        "artist_notes": artist_notes,
        "image_filename": image_filename
    }
    return RedirectResponse(url="/artist/products/review", status_code=303)


@router.get("/products/review", response_class=HTMLResponse)
async def add_product_step2_page(request: Request, user_auth = Depends(is_artist)):
    if isinstance(user_auth, RedirectResponse): return user_auth
    
    product_data = request.session.get("product_creation_data")
    if not product_data:
        flash(request, "Session expired or invalid step. Please start again.", "warning")
        return RedirectResponse(url="/artist/products/new", status_code=303)

    # Call AI services
    ai_description = services.ai_service.generate_product_description(
        name=product_data["name"],
        category=product_data["category"],
        artist_notes=product_data["artist_notes"]
    )
    ai_price_suggestion = services.ai_service.suggest_product_price(
        name=product_data["name"],
        category=product_data["category"],
        artist_notes=product_data["artist_notes"]
    )

    context = {
        "request": request,
        "product_data": product_data,
        "ai_description": ai_description,
        "ai_price_suggestion": ai_price_suggestion
    }
    return templates.TemplateResponse("artist/add_product_step2.html", context)

@router.post("/products/save")
async def save_product(
    request: Request,
    db: Session = Depends(get_db),
    user_auth = Depends(is_artist),
    ai_generated_description: str = Form(...),
    price_usd: float = Form(...),
    stock: int = Form(...),
):
    if isinstance(user_auth, RedirectResponse): return user_auth
    
    product_data = request.session.pop("product_creation_data", None)
    if not product_data:
        flash(request, "Could not save product. Session data missing.", "danger")
        return RedirectResponse(url="/artist/products/new")

    owner_id = request.session["user"]["id"]
    crud.create_product(
        db=db,
        owner_id=owner_id,
        name=product_data["name"],
        category=product_data["category"],
        artist_notes=product_data["artist_notes"],
        image_filename=product_data["image_filename"],
        ai_description=ai_generated_description,
        price=price_usd,
        stock=stock
    )
    flash(request, f'Product "{product_data["name"]}" has been successfully listed!', "success")
    return RedirectResponse(url="/artist/dashboard", status_code=303)

@router.post("/orders/update/{order_id}")
async def update_order(request: Request, order_id: int, db: Session = Depends(get_db), user_auth = Depends(is_artist), status: OrderStatus = Form(...)):
    if isinstance(user_auth, RedirectResponse): return user_auth

    artist_id = request.session["user"]["id"]
    updated_order = crud.update_order_status(db, order_id, artist_id, status)
    if updated_order:
        flash(request, f"Order #{order_id} status updated to {status.value}.", "success")
    else:
        flash(request, "Failed to update order status.", "danger")
    
    return RedirectResponse(url="/artist/dashboard", status_code=303)