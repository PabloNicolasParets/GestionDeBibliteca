from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Book, Loan


def list_books(db: Session, search: str = "", category_id: int | None = None) -> list[Book]:
    statement = select(Book).options(joinedload(Book.category))
    if search:
        statement = statement.where(Book.name.ilike(f"%{search}%"))
    if category_id is not None:
        statement = statement.where(Book.category_id == category_id)
    return list(db.scalars(statement.order_by(Book.name)).all())


def get_book(db: Session, book_id: int) -> Book | None:
    return db.scalar(
        select(Book).options(joinedload(Book.category)).where(Book.id == book_id)
    )


def create_book(
    db: Session, name: str, category_id: int, additional_info: str
) -> Book:
    book = Book(name=name, category_id=category_id, additional_info=additional_info)
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(
    db: Session, book: Book, name: str, category_id: int, additional_info: str
) -> Book:
    book.name = name
    book.category_id = category_id
    book.additional_info = additional_info
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: Book) -> None:
    db.delete(book)
    db.commit()


def has_active_loan(db: Session, book_id: int) -> bool:
    return db.scalar(
        select(Loan.id).where(Loan.book_id == book_id, Loan.returned_date.is_(None))
    ) is not None