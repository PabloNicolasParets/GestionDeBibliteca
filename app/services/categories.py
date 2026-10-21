from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Book, Category


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.description)).all())


def get_category(db: Session, category_id: int) -> Category | None:
    return db.get(Category, category_id)


def create_category(
    db: Session, description: str, color: str, additional_info: str
) -> Category:
    category = Category(
        description=description, color=color, additional_info=additional_info
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    category: Category,
    description: str,
    color: str,
    additional_info: str,
) -> Category:
    category.description = description
    category.color = color
    category.additional_info = additional_info
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> bool:
    book_count = db.scalar(
        select(func.count()).select_from(Book).where(Book.category_id == category.id)
    )
    if book_count:
        return False
    db.delete(category)
    db.commit()
    return True