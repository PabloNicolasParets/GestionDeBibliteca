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