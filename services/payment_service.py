import stripe
import os
from dotenv import load_dotenv
from typing import List
from models import CartItem

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = os.getenv("YOUR_DOMAIN")

def create_checkout_session(cart_items: List[CartItem]):
    try:
        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                    'unit_amount': int(item.product.price_usd * 100), # Price in cents
                },
                'quantity': item.quantity,
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/customer/payment/success',
            cancel_url=YOUR_DOMAIN + '/customer/cart',
        )
        return session.url
    except Exception as e:
        return str(e)