from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.models import Base

ADMIN_PASSWORD = "administrador"


def login_as_admin(client: TestClient) -> None:
    response = client.post(
        "/login",
        data={"username": "administrador", "password": ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 303


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
    login_as_admin(client)
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
    login_as_admin(client)
    response = client.post(
        "/categorias",
        data={"description": "Historia", "color": "verde", "additional_info": ""},
    )
    assert response.status_code == 422
    assert "formato hexadecimal" in response.text


def test_book_requires_existing_category(client):
    login_as_admin(client)
    response = client.post(
        "/libros",
        data={"name": "Sin categoría", "category_id": "999", "additional_info": ""},
    )
    assert response.status_code == 422
    assert "categoría válida" in response.text


def test_guest_can_view_but_cannot_modify_catalog(client):
    listing = client.get("/libros")
    assert listing.status_code == 200
    assert "Universo Este" in listing.text
    assert "Parque educativo Este" in listing.text
    assert "Universo Este</span><br><span" in listing.text
    assert "styles.css?v=3" in listing.text
    assert "/static/universo-este-logo.png" in listing.text
    logo = client.get("/static/universo-este-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"] == "image/png"
    assert "Iniciar sesión" in listing.text
    assert "Nuevo libro" not in listing.text

    categories = client.get("/categorias")
    assert categories.status_code == 200
    assert "Universo Este" in categories.text
    assert "Parque educativo Este" in categories.text

    login = client.get("/login")
    assert login.status_code == 200
    assert "Universo Este" in login.text
    assert "Parque educativo Este" in login.text

    response = client.post(
        "/categorias",
        data={"description": "Narrativa", "color": "#52796F", "additional_info": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    response = client.get("/libros/nuevo", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_regular_user_cannot_modify_catalog(client):
    login_as_admin(client)
    client.post(
        "/categorias",
        data={"description": "Narrativa", "color": "#52796F", "additional_info": ""},
    )
    client.post(
        "/libros",
        data={"name": "La casa", "category_id": "1", "additional_info": ""},
    )
    client.post("/logout")
    response = client.post(
        "/login",
        data={"username": "usuario", "password": "usuario"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    listing = client.get("/categorias")
    assert listing.status_code == 200
    assert "Nueva categoría" not in listing.text
    assert "Editar" not in listing.text
    assert "Eliminar" not in listing.text
    book_listing = client.get("/libros")
    assert "Nuevo libro" not in book_listing.text
    assert "Editar" not in book_listing.text
    assert "Eliminar" not in book_listing.text

    denied_writes = [
        client.post(
            "/categorias",
            data={"description": "Narrativa", "color": "#52796F", "additional_info": ""},
        ),
        client.post(
            "/categorias/1/editar",
            data={"description": "Nueva", "color": "#52796F", "additional_info": ""},
        ),
        client.post("/categorias/1/eliminar"),
        client.post(
            "/libros",
            data={"name": "Otro libro", "category_id": "1", "additional_info": ""},
        ),
        client.post(
            "/libros/1/editar",
            data={"name": "Otro nombre", "category_id": "1", "additional_info": ""},
        ),
        client.post("/libros/1/eliminar"),
    ]
    assert [response.status_code for response in denied_writes] == [403] * 6

    assert client.get("/usuarios").status_code == 404


def test_only_two_fixed_accounts_can_log_in(client):
    user_login = client.post(
        "/login",
        data={"username": "usuario", "password": "usuario"},
        follow_redirects=False,
    )
    assert user_login.status_code == 303
    client.post("/logout")

    admin_login = client.post(
        "/login",
        data={"username": "administrador", "password": "administrador"},
        follow_redirects=False,
    )
    assert admin_login.status_code == 303
    client.post("/logout")

    invalid_login = client.post(
        "/login",
        data={"username": "otro", "password": "otro"},
        follow_redirects=False,
    )
    assert invalid_login.status_code == 401

    assert client.get("/usuarios").status_code == 404


def test_header_displays_username_without_role(client):
    login_as_admin(client)
    page = client.get("/libros")
    assert page.text.count("administrador") == 1
    assert "Administrador" not in page.text


def test_admin_can_register_and_return_a_loan(client):
    login_as_admin(client)
    client.post(
        "/categorias",
        data={"description": "Narrativa", "color": "#52796F", "additional_info": ""},
    )
    client.post(
        "/libros",
        data={"name": "La casa", "category_id": "1", "additional_info": ""},
    )

    form = client.get("/prestamos/libros/1/nuevo")
    assert form.status_code == 200
    assert "devolución será el" in form.text

    created = client.post(
        "/prestamos/libros/1",
        data={"borrower_name": "María Pérez", "borrower_dni": "12345678"},
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "María Pérez" in created.text
    assert "12345678" in created.text
    expected_due_date = (date.today() + timedelta(days=7)).strftime("%d/%m/%Y")
    assert expected_due_date in created.text

    books = client.get("/libros")
    assert f"Prestado hasta {expected_due_date}" in books.text
    assert "Prestar" not in books.text

    repeated_loan = client.post(
        "/prestamos/libros/1",
        data={"borrower_name": "Otra persona", "borrower_dni": "87654321"},
        follow_redirects=True,
    )
    assert "Este libro ya tiene un préstamo activo." in repeated_loan.text

    protected_delete = client.post("/libros/1/eliminar", follow_redirects=True)
    assert "No se puede eliminar un libro que tiene un préstamo activo." in protected_delete.text

    returned = client.post("/prestamos/1/devolver", follow_redirects=True)
    assert "Libro marcado como devuelto." in returned.text
    assert "Devuelto el" in returned.text
    assert "Prestar" in client.get("/libros").text


def test_only_admin_can_access_loan_operations(client):
    response = client.get("/prestamos", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    client.post(
        "/login",
        data={"username": "usuario", "password": "usuario"},
        follow_redirects=False,
    )
    assert client.get("/prestamos").status_code == 403
    assert client.get("/prestamos/libros/1/nuevo").status_code == 403
    assert client.post(
        "/prestamos/libros/1",
        data={"borrower_name": "Persona", "borrower_dni": "12345678"},
    ).status_code == 403
    assert client.post("/prestamos/1/devolver").status_code == 403


def test_loan_requires_name_and_dni(client):
    login_as_admin(client)
    client.post(
        "/categorias",
        data={"description": "Narrativa", "color": "#52796F", "additional_info": ""},
    )
    client.post(
        "/libros",
        data={"name": "La casa", "category_id": "1", "additional_info": ""},
    )

    missing_name = client.post(
        "/prestamos/libros/1",
        data={"borrower_name": " ", "borrower_dni": "12345678"},
    )
    assert missing_name.status_code == 422
    assert "Escribe el nombre" in missing_name.text

    missing_dni = client.post(
        "/prestamos/libros/1",
        data={"borrower_name": "María Pérez", "borrower_dni": " "},
    )
    assert missing_dni.status_code == 422
    assert "Escribe el DNI" in missing_dni.text