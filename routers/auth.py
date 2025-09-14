# routers/auth.py - The Stable Pattern

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import crud, schemas, models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
async def login_user(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    user = crud.get_user_by_email(db, email=email)
    if not user or not crud.verify_password(password, user.hashed_password):
        # We will handle flash messages later. For now, just redirect.
        return RedirectResponse(url="/login", status_code=303)
    
    # This works because the middleware is correctly installed in main.py
    request.session["user"] = {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role.value}
    return RedirectResponse(url="/", status_code=303)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/register")
async def register_user(db: Session = Depends(get_db), email: str = Form(...), full_name: str = Form(...), password: str = Form(...), role: models.UserRole = Form(...)):
    user = crud.get_user_by_email(db, email=email)
    if user:
        return RedirectResponse(url="/register", status_code=303)
    
    user_create = schemas.UserCreate(email=email, full_name=full_name, password=password, role=role)
    crud.create_user(db=db, user=user_create)
    return RedirectResponse(url="/login", status_code=303)

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/", status_code=303)