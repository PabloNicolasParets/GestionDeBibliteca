from contextlib import asynccontextmanager
from pathlib import Path
import os
import secrets

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import engine, get_db
from app.models import Base
from app.routes import auth, books, categories, loans
from app.services.users import ensure_default_users

ROOT = Path(__file__).resolve().parent


def create_app(database_engine: Engine = engine) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        Base.metadata.create_all(bind=database_engine)
        with Session(database_engine) as db:
            ensure_default_users(db)
        yield

    application = FastAPI(title="Biblioteca", lifespan=lifespan)
    application.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET") or secrets.token_urlsafe(32),
        same_site="lax",
        https_only=os.getenv("SESSION_HTTPS_ONLY", "").lower() in {"1", "true", "yes"},
        max_age=60 * 60 * 8,
    )
    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    application.include_router(auth.router)
    application.include_router(categories.router)
    application.include_router(books.router)
    application.include_router(loans.router)

    if database_engine is not engine:
        test_session_factory = sessionmaker(bind=database_engine, autoflush=False, autocommit=False)

        def override_get_db():
            with test_session_factory() as db:
                yield db

        application.dependency_overrides[get_db] = override_get_db

    @application.get("/")
    def home():
        return RedirectResponse("/libros", status_code=303)

    return application


app = create_app()