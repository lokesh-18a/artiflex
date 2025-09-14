# main.py - The Final, Structured Version

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

from database import engine, Base
from routers import auth, public, artist, customer

# --- SETUP ---
load_dotenv()
Base.metadata.create_all(bind=engine)
app = FastAPI()

# --- MIDDLEWARE ---
# SessionMiddleware is installed here, making it available to all included routers.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise SystemExit("FATAL ERROR: SECRET_KEY not found in .env file.")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- STATIC FILES & ROUTERS ---
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(artist.router)
app.include_router(customer.router)