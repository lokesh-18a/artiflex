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

@router.post("/checkout-initialize") # This is the new target for the cart button
async def checkout_initialize(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = crud.get_cart_items(db, customer_id=current_user.id)
    if not cart_items:
        flash(request, "Your cart is empty.", "warning")
        return RedirectResponse(url="/customer/cart", status_code=303)

    # Call Stripe to get a "payment intent" or a checkout session ID.
    # We will store this ID in the session to confirm payment later.
    checkout_session = services.payment_service.create_checkout_session(cart_items)
    
    # IMPORTANT: The payment_service needs a small change to return the session object, not just the URL.
    if checkout_session and checkout_session.id:
        # Success! Store the ID and redirect to our address form.
        request.session["stripe_checkout_id"] = checkout_session.id
        return RedirectResponse(url="/customer/checkout-details", status_code=303)
    else:
        # Handle Stripe API failure
        flash(request, "Could not connect to payment service. Please try again.", "danger")
        return RedirectResponse(url="/customer/cart", status_code=303)
    
@router.get("/orders", response_class=HTMLResponse)
async def view_orders(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    orders = crud.get_orders_by_customer(db, customer_id=current_user.id)
    context = {"request": request, "orders": orders}
    return templates.TemplateResponse("customer/orders.html", context)

@router.get("/checkout-details", response_class=HTMLResponse)
async def checkout_details_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Verify that the user has a valid stripe session from the previous step
    if "stripe_checkout_id" not in request.session:
        flash(request, "Invalid checkout session. Please start again from your cart.", "warning")
        return RedirectResponse(url="/customer/cart", status_code=303)

    cart_items = crud.get_cart_items(db, customer_id=current_user.id)
    total = sum(item.product.price_usd * item.quantity for item in cart_items)
    
    context = {
        "request": request,
        "cart_items": cart_items,
        "total": total,
        "currency": "INR",
        "conversion_rate": 83.0
    }
    # This renders the same 'checkout_page.html' from before.
    return templates.TemplateResponse("customer/checkout_page.html", context)

@router.post("/place-order")
async def place_order(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    address: str = Form(...),
    country: str = Form(...),
    city: str = Form(...),
    zip: str = Form(...),
    paymentMethod: str = Form(...) # "COD" or "Online"
):
    # Verify we still have a valid checkout session
    if "stripe_checkout_id" not in request.session:
        flash(request, "Your payment session has expired. Please try again.", "warning")
        return RedirectResponse(url="/customer/cart", status_code=303)

    cart_items = crud.get_cart_items(db, customer_id=current_user.id)
    if not cart_items:
        return RedirectResponse(url="/", status_code=303)

    shipping_details = {
        "address": address, "country": country, "city": city,
        "zip": zip, "paymentMethod": paymentMethod
    }

    # Create the order in the database
    order = crud.create_order(
        db, 
        customer_id=current_user.id, 
        cart_items=cart_items,
        shipping_details=shipping_details
    )
    
    # Clean up
    crud.clear_customer_cart(db, customer_id=current_user.id)
    del request.session["stripe_checkout_id"]
    
    flash(request, f"Your order #{order.id} has been placed successfully!", "success")
    return RedirectResponse(url="/customer/orders", status_code=303)