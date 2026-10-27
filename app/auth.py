from typing import Any

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


def get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
    return user


def require_admin(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=303,
            detail="Inicia sesión para continuar.",
            headers={"Location": "/login"},
        )
    if user.role != "administrador":
        raise HTTPException(
            status_code=403, detail="Solo un administrador puede realizar esta acción."
        )
    return user


def template_context(
    request: Request, user: User | None, **context: Any
) -> dict[str, Any]:
    return {"request": request, "user": user, **context}
