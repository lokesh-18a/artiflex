# main.py - THE FINAL TEST

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import os

# --- CONFIGURATION ---
# We are hard-coding the secret key. No .env file. No complications.
SECRET_KEY = "a-temporary-but-valid-secret-key-for-testing"
if not SECRET_KEY:
    raise SystemExit("Secret Key is missing.")

# --- APP CREATION ---
app = FastAPI()

# --- MIDDLEWARE INSTALLATION ---
# This is the only middleware we are adding.
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# --- THE TEST ROUTE ---
# This is the only route in the entire application.
@app.get("/")
async def root(request: Request):
    try:
        # We will try to access the session.
        # This is the line that has been crashing.
        request.session["test_data"] = "hello"
        
        # If the line above works, we return a success message.
        return HTMLResponse("<h1>Session OK. The framework is working.</h1>")

    except Exception as e:
        # If it crashes, we return the error message directly.
        return HTMLResponse(f"<h1>CRITICAL FAILURE</h1><p>{e}</p><p>Traceback: {e.__traceback__}</p>")