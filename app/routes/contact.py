from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_optional_user, template_context
from app.database import get_db
from app.models import User

router = APIRouter(tags=["contacto"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/contacto")
def contact_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context=template_context(request, user),
    )
