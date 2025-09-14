from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from routers.auth_helpers import get_current_user, login_required
import crud, services.payment_service
from models import User

router = APIRouter(prefix="/customer", tags=["customer"], dependencies=[Depends(login_required)])
templates = Jinja2Templates(directory="templates")

def flash(request: Request, message: str, category: str = "success"):
    if 'flash_messages' not in request.session:
        request.session['flash_messages'] = []
    request.session['flash_messages'].append((category, message))

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = crud.get_cart_items(db, customer_id=current_user.id)
    total = sum(item.product.price_usd * item.quantity for item in cart_items)
    
    currency = request.session.get('currency', 'USD')
    rates = request.session.get('currency_rates', {})
    conversion_rate = rates.get(currency, 1.0)
    
    context = {
        "request": request,
        "cart_items": cart_items,
        "total": total,
        "currency": currency,
        "conversion_rate": conversion_rate
    }
    return templates.TemplateResponse("customer/cart.html", context)

@router.post("/cart/add/{product_id}")
async def add_to_cart(request: Request, product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    crud.add_item_to_cart(db, customer_id=current_user.id, product_id=product_id)
    flash(request, "Item added to cart!", "success")
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)
    
@router.post("/cart/remove/{cart_item_id}")
async def remove_from_cart(request: Request, cart_item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    crud.remove_item_from_cart(db, cart_item_id=cart_item_id, customer_id=current_user.id)
    flash(request, "Item removed from cart.", "info")
    return RedirectResponse(url="/customer/cart", status_code=303)

@router.post("/checkout")
async def checkout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = crud.get_cart_items(db, customer_id=current_user.id)
    if not cart_items:
        flash(request, "Your cart is empty.", "warning")
        return RedirectResponse(url="/customer/cart", status_code=303)

    checkout_url = services.payment_service.create_checkout_session(cart_items)
    if "https://" in checkout_url:
        return RedirectResponse(url=checkout_url, status_code=303)
    else:
        flash(request, f"Could not initiate payment: {checkout_url}", "danger")
        return RedirectResponse(url="/customer/cart", status_code=303)

@router.get("/payment/success", response_class=HTMLResponse)
async def payment_success(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = crud.get_cart_items(db, customer_id=current_user.id)
    if not cart_items:
        flash(request, "No items in cart to process.", "warning")
        return RedirectResponse(url="/")
        
    order = crud.create_order(db, customer_id=current_user.id, cart_items=cart_items)
    crud.clear_customer_cart(db, customer_id=current_user.id)
    
    return templates.TemplateResponse("customer/payment_success.html", {"request": request, "order": order})
    
@router.get("/orders", response_class=HTMLResponse)
async def view_orders(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = crud.get_orders_by_customer(db, customer_id=current_user.id)
    context = {"request": request, "orders": orders}
    return templates.TemplateResponse("customer/orders.html", context)