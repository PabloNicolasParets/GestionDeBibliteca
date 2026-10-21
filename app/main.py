from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.database import SessionLocal, engine, get_db
from app.models import Base
from app.routes import books, categories

ROOT = Path(__file__).resolve().parent


def create_app(database_engine: Engine = engine) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        Base.metadata.create_all(bind=database_engine)
        yield

    application = FastAPI(title="Biblioteca", lifespan=lifespan)
    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    application.include_router(categories.router)
    application.include_router(books.router)

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