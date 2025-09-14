from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import crud

# Dependency to get the current user from the session
def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_session = request.session.get("user")
    if not user_session:
        return None
    user = crud.get_user_by_email(db, email=user_session["email"])
    return user

# Dependency to protect routes
def login_required(request: Request):
    if "user" not in request.session:
        # Store the intended URL in the session to redirect after login
        request.session["next_url"] = str(request.url)
        # Add a flash message
        if 'flash_messages' not in request.session:
            request.session['flash_messages'] = []
        request.session['flash_messages'].append(('warning', 'You need to be logged in to view this page.'))
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return True