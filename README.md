# Estante

Aplicación web en español para organizar categorías y libros de una biblioteca. Permite crear, consultar, modificar y eliminar registros; cada libro pertenece a una categoría. No se puede eliminar una categoría mientras tenga libros asociados.

## Requisitos

- Python 3.11 o posterior.

## Instalación en Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Ejecutar

```powershell
python -m uvicorn app.main:app --reload
```

Abre `http://127.0.0.1:8000`. La base de datos `biblioteca.db` se crea automáticamente en la carpeta del proyecto.

## Pruebas

```powershell
python -m pytest
```

## Funciones

- Categorías con descripción, color e información adicional.
- Libros con nombre, categoría e información adicional.
- Listados, creación, edición y eliminación con validación del lado del servidor.
- Búsqueda de libros por nombre y filtro por categoría.
- Protección contra la eliminación de categorías que estén en uso.
- Acceso de consulta público y permisos diferenciados para los roles `usuario` y `administrador`.
- Préstamos administrados por el administrador, con nombre y DNI de la persona y devolución prevista a siete días.

## Usuarios y permisos

La aplicación crea automáticamente estas dos cuentas fijas:

| Usuario | Contraseña | Permisos |
| --- | --- | --- |
| `usuario` | `usuario` | Consultar libros y categorías |
| `administrador` | `administrador` | Consultar, crear, editar y eliminar libros y categorías; gestionar préstamos |

No hay registro ni gestión de cuentas. Solo `administrador` puede modificar el catálogo.

El administrador puede registrar un préstamo desde el listado de libros. Cada préstamo guarda el nombre y DNI de la persona, calcula la devolución prevista a siete días y permite marcar el libro como devuelto. Un libro con préstamo pendiente no se puede prestar nuevamente ni eliminar.

Para mantener las sesiones válidas entre reinicios, configura una clave secreta estable en el entorno antes de iniciar la aplicación:

```powershell
$env:SESSION_SECRET = python -c "import secrets; print(secrets.token_urlsafe(48))"
```

En despliegues HTTPS, activa también la cookie segura:

```powershell
$env:SESSION_HTTPS_ONLY = "true"
```