import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.models import Base


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    application = create_app(test_engine)
    with TestClient(application) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_category_and_book_crud(client):
    response = client.post(
        "/categorias",
        data={"description": "Narrativa", "color": "#52796F", "additional_info": "Ficción"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Narrativa" in response.text

    response = client.post(
        "/libros",
        data={"name": "La casa", "category_id": "1", "additional_info": "Edición revisada"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "La casa" in response.text

    response = client.post(
        "/libros/1/editar",
        data={"name": "La casa azul", "category_id": "1", "additional_info": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "La casa azul" in response.text

    protected_delete = client.post("/categorias/1/eliminar", follow_redirects=True)
    assert "no se puede eliminar" in protected_delete.text.lower()

    deleted_book = client.post("/libros/1/eliminar", follow_redirects=True)
    assert "La casa azul" not in deleted_book.text

    updated_category = client.post(
        "/categorias/1/editar",
        data={"description": "Clásicos", "color": "#A34B35", "additional_info": ""},
        follow_redirects=True,
    )
    assert "Clásicos" in updated_category.text

    deleted_category = client.post("/categorias/1/eliminar", follow_redirects=True)
    assert "Clásicos" not in deleted_category.text


def test_invalid_category_color_is_rejected(client):
    response = client.post(
        "/categorias",
        data={"description": "Historia", "color": "verde", "additional_info": ""},
    )
    assert response.status_code == 422
    assert "formato hexadecimal" in response.text


def test_book_requires_existing_category(client):
    response = client.post(
        "/libros",
        data={"name": "Sin categoría", "category_id": "999", "additional_info": ""},
    )
    assert response.status_code == 422
    assert "categoría válida" in response.text