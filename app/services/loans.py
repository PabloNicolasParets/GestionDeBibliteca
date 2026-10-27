from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Loan

LOAN_PERIOD_DAYS = 7


def due_date_for(loan_date: date | None = None) -> date:
    return (loan_date or date.today()) + timedelta(days=LOAN_PERIOD_DAYS)


def active_loans_by_book(db: Session) -> dict[int, Loan]:
    loans = db.scalars(
        select(Loan).where(Loan.returned_date.is_(None), Loan.book_id.is_not(None))
    ).all()
    return {loan.book_id: loan for loan in loans if loan.book_id is not None}


def list_loans(db: Session) -> list[Loan]:
    return list(
        db.scalars(
            select(Loan)
            .options(joinedload(Loan.book))
            .order_by(Loan.returned_date.is_(None).desc(), Loan.due_date, Loan.id.desc())
        ).all()
    )


def get_loan(db: Session, loan_id: int) -> Loan | None:
    return db.get(Loan, loan_id)


def create_loan(
    db: Session,
    book_id: int,
    book_name: str,
    borrower_name: str,
    borrower_dni: str,
) -> Loan | None:
    if db.scalar(
        select(Loan.id).where(Loan.book_id == book_id, Loan.returned_date.is_(None))
    ) is not None:
        return None
    loan_date = date.today()
    loan = Loan(
        book_id=book_id,
        book_name=book_name,
        borrower_name=borrower_name,
        borrower_dni=borrower_dni,
        loan_date=loan_date,
        due_date=due_date_for(loan_date),
    )
    db.add(loan)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(
            select(Loan.id).where(
                Loan.book_id == book_id, Loan.returned_date.is_(None)
            )
        ) is not None:
            return None
        raise
    db.refresh(loan)
    return loan


def return_loan(db: Session, loan: Loan) -> None:
    loan.returned_date = date.today()
    db.commit()
