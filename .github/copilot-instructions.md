# Instrucciones del proyecto

- Aplicación web para gestionar categorías y libros de una biblioteca, con backend Python y FastAPI.
- Mantén la separación existente entre rutas, servicios, modelos, plantillas y persistencia.
- Usa SQLAlchemy 2 y conserva SQLite como base de datos predeterminada para desarrollo.
- Las categorías tienen descripción, color hexadecimal e información adicional; los libros tienen nombre, categoría e información adicional.
- No permitas eliminar una categoría que todavía tenga libros asociados.
- Conserva validación en servidor, respuestas comprensibles en español y pruebas para cambios de comportamiento.
- Ejecuta `python -m pytest` después de modificar reglas de negocio o rutas.