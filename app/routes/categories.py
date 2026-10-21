import re

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.services import categories as category_service

router = APIRouter(prefix="/categorias", tags=["categorias"])
templates = Jinja2Templates(directory="app/templates")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def render_form(request: Request, category: Category, error: str = "", code: int = 200):
    return templates.TemplateResponse(
        request=request,
        name="categories/form.html",
        context={"category": category, "error": error},
        status_code=code,
    )


@router.get("")
def category_list(request: Request, db: Session = Depends(get_db), aviso: str = "", error: str = ""):
    notices = {
        "eliminada": "Categoría eliminada.",
        "actualizada": "Categoría actualizada.",
        "creada": "Categoría creada.",
    }
    errors = {"en_uso": "No se puede eliminar una categoría que tiene libros asociados."}
    return templates.TemplateResponse(
        request=request,
        name="categories/list.html",
        context={
            "categories": category_service.list_categories(db),
            "notice": notices.get(aviso, ""),
            "error": errors.get(error, ""),
        },
    )


@router.get("/nueva")
def new_category(request: Request):
    return render_form(request, Category(description="", color="#52796F", additional_info=""))


@router.post("")
def create_category(
    request: Request,
    description: str = Form(...),
    color: str = Form(...),
    additional_info: str = Form(""),
    db: Session = Depends(get_db),
):
    category = Category(
        description=description.strip(), color=color.strip(), additional_info=additional_info.strip()
    )
    if not category.description:
        return render_form(request, category, "Escribe una descripción para la categoría.", 422)
    if len(category.description) > 120:
        return render_form(request, category, "La descripción admite hasta 120 caracteres.", 422)
    if not COLOR_PATTERN.fullmatch(category.color):
        return render_form(request, category, "El color debe tener formato hexadecimal, por ejemplo #52796F.", 422)
    category_service.create_category(db, category.description, category.color, category.additional_info)
    return RedirectResponse("/categorias?aviso=creada", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{category_id}/editar")
def edit_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return render_form(request, category)


@router.post("/{category_id}/editar")
def update_category(
    category_id: int,
    request: Request,
    description: str = Form(...),
    color: str = Form(...),
    additional_info: str = Form(""),
    db: Session = Depends(get_db),
):
    category = category_service.get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    category.description = description.strip()
    category.color = color.strip()
    category.additional_info = additional_info.strip()
    if not category.description:
        return render_form(request, category, "Escribe una descripción para la categoría.", 422)
    if len(category.description) > 120:
        return render_form(request, category, "La descripción admite hasta 120 caracteres.", 422)
    if not COLOR_PATTERN.fullmatch(category.color):
        return render_form(request, category, "El color debe tener formato hexadecimal, por ejemplo #52796F.", 422)
    category_service.update_category(db, category, category.description, category.color, category.additional_info)
    return RedirectResponse("/categorias?aviso=actualizada", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{category_id}/eliminar")
def remove_category(category_id: int, db: Session = Depends(get_db)):
    category = category_service.get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if not category_service.delete_category(db, category):
        return RedirectResponse("/categorias?error=en_uso", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse("/categorias?aviso=eliminada", status_code=status.HTTP_303_SEE_OTHER)