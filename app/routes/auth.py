from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_optional_user
from app.database import get_db
from app.models import User
from app.services import users as user_service

router = APIRouter(tags=["autenticación"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_page(
    request: Request, user: User | None = Depends(get_optional_user), error: str = ""
):
    if user is not None:
        return RedirectResponse("/libros", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request, "user": None, "error": error},
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = user_service.authenticate(db, username, password)
    if user is None:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "request": request,
                "user": None,
                "error": "El usuario o la contraseña no son correctos.",
            },
            status_code=401,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/libros", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/libros", status_code=303)
