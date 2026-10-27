from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import require_admin, template_context
from app.database import get_db
from app.models import Book, User
from app.services import books as book_service
from app.services import loans as loan_service

router = APIRouter(prefix="/prestamos", tags=["préstamos"])
templates = Jinja2Templates(directory="app/templates")


def render_loan_form(
    request: Request,
    book: Book,
    user: User,
    borrower_name: str = "",
    borrower_dni: str = "",
    error: str = "",
    code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="loans/form.html",
        context=template_context(
            request,
            user,
            book=book,
            borrower_name=borrower_name,
            borrower_dni=borrower_dni,
            due_date=loan_service.due_date_for(),
            error=error,
        ),
        status_code=code,
    )


@router.get("")
def loan_list(
    request: Request,
    aviso: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    notices = {
        "creado": "Préstamo registrado.",
        "devuelto": "Libro marcado como devuelto.",
        "ocupado": "Este libro ya tiene un préstamo activo.",
    }
    return templates.TemplateResponse(
        request=request,
        name="loans/list.html",
        context=template_context(
            request, user, loans=loan_service.list_loans(db), notice=notices.get(aviso, "")
        ),
    )


@router.get("/libros/{book_id}/nuevo")
def new_loan(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    book = book_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    if book_service.has_active_loan(db, book.id):
        return RedirectResponse("/prestamos?aviso=ocupado", status_code=303)
    return render_loan_form(request, book, user)


@router.post("/libros/{book_id}")
def create_loan(
    book_id: int,
    request: Request,
    borrower_name: str = Form(...),
    borrower_dni: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    book = book_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado.")
    name = borrower_name.strip()
    dni = borrower_dni.strip()
    if not name:
        return render_loan_form(
            request, book, user, name, dni, "Escribe el nombre de la persona.", 422
        )
    if len(name) > 120:
        return render_loan_form(
            request, book, user, name, dni, "El nombre admite hasta 120 caracteres.", 422
        )
    if not dni:
        return render_loan_form(
            request, book, user, name, dni, "Escribe el DNI de la persona.", 422
        )
    if len(dni) > 30:
        return render_loan_form(
            request, book, user, name, dni, "El DNI admite hasta 30 caracteres.", 422
        )
    loan = loan_service.create_loan(db, book.id, book.name, name, dni)
    if loan is None:
        return RedirectResponse("/prestamos?aviso=ocupado", status_code=303)
    return RedirectResponse("/prestamos?aviso=creado", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{loan_id}/devolver")
def return_book(
    loan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    loan = loan_service.get_loan(db, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado.")
    if loan.returned_date is None:
        loan_service.return_loan(db, loan)
    return RedirectResponse("/prestamos?aviso=devuelto", status_code=303)
