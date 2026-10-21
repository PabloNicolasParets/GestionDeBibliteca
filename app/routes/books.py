from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Book
from app.services import books as book_service
from app.services import categories as category_service

router = APIRouter(prefix="/libros", tags=["libros"])
templates = Jinja2Templates(directory="app/templates")


def render_form(
    request: Request,
    book: Book,
    categories,
    error: str = "",
    code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="books/form.html",
        context={"book": book, "categories": categories, "error": error},
        status_code=code,
    )


@router.get("")
def book_list(
    request: Request,
    q: str = "",
    categoria: int | None = None,
    aviso: str = "",
    db: Session = Depends(get_db),
):
    notices = {"eliminado": "Libro eliminado.", "actualizado": "Libro actualizado.", "creado": "Libro creado."}
    return templates.TemplateResponse(
        request=request,
        name="books/list.html",
        context={
            "books": book_service.list_books(db, q.strip(), categoria),
            "categories": category_service.list_categories(db),
            "search": q,
            "selected_category": categoria,
            "notice": notices.get(aviso, ""),
        },
    )


@router.get("/nuevo")
def new_book(request: Request, db: Session = Depends(get_db)):
    categories = category_service.list_categories(db)
    if not categories:
        return RedirectResponse("/categorias/nueva", status_code=status.HTTP_303_SEE_OTHER)
    return render_form(request, Book(name="", additional_info=""), categories)


@router.post("")
def create_book(
    request: Request,
    name: str = Form(...),
    category_id: str = Form(...),
    additional_info: str = Form(""),
    db: Session = Depends(get_db),
):
    categories = category_service.list_categories(db)
    book = Book(name=name.strip(), additional_info=additional_info.strip())
    if not book.name:
        return render_form(request, book, categories, "Escribe el nombre del libro.", 422)
    if len(book.name) > 180:
        return render_form(request, book, categories, "El nombre admite hasta 180 caracteres.", 422)
    try:
        selected_category = category_service.get_category(db, int(category_id))
    except ValueError:
        selected_category = None
    if selected_category is None:
        return render_form(request, book, categories, "Selecciona una categoría válida.", 422)
    book_service.create_book(db, book.name, selected_category.id, book.additional_info)
    return RedirectResponse("/libros?aviso=creado", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{book_id}/editar")
def edit_book(book_id: int, request: Request, db: Session = Depends(get_db)):
    book = book_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return render_form(request, book, category_service.list_categories(db))


@router.post("/{book_id}/editar")
def update_book(
    book_id: int,
    request: Request,
    name: str = Form(...),
    category_id: str = Form(...),
    additional_info: str = Form(""),
    db: Session = Depends(get_db),
):
    book = book_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    book.name = name.strip()
    book.additional_info = additional_info.strip()
    categories = category_service.list_categories(db)
    if not book.name:
        return render_form(request, book, categories, "Escribe el nombre del libro.", 422)
    if len(book.name) > 180:
        return render_form(request, book, categories, "El nombre admite hasta 180 caracteres.", 422)
    try:
        selected_category = category_service.get_category(db, int(category_id))
    except ValueError:
        selected_category = None
    if selected_category is None:
        return render_form(request, book, categories, "Selecciona una categoría válida.", 422)
    book_service.update_book(db, book, book.name, selected_category.id, book.additional_info)
    return RedirectResponse("/libros?aviso=actualizado", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{book_id}/eliminar")
def remove_book(book_id: int, db: Session = Depends(get_db)):
    book = book_service.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    book_service.delete_book(db, book)
    return RedirectResponse("/libros?aviso=eliminado", status_code=status.HTTP_303_SEE_OTHER)