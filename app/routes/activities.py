from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import get_optional_user, template_context
from app.database import get_db
from app.models import User

router = APIRouter(tags=["actividades"])
templates = Jinja2Templates(directory="app/templates")

ACTIVITY_GROUPS = [
    {
        "name": "Actividades generales",
        "activities": [
            {
                "name": "Entrenamiento funcional (+15 años)",
                "schedules": [
                    ("Lunes, martes y jueves", "08:00–09:00"),
                    ("Lunes, miércoles y viernes", "17:00–18:30"),
                ],
            },
            {
                "name": "Flexibilidad (+15 años)",
                "schedules": [("Lunes a jueves", "09:00–10:00")],
            },
            {
                "name": "Entrenamiento funcional y actividad física (+15, mixto)",
                "schedules": [("Lunes a viernes", "08:00–09:00")],
            },
            {"name": "Ritmos y movimientos", "schedules": [("Viernes", "09:00–10:00")]},
            {
                "name": "Alegría y encuentro con música y movimiento",
                "schedules": [("Viernes", "10:00–12:30")],
            },
            {"name": "Newcom", "schedules": [("Martes", "10:00–12:00")]},
            {"name": "Gimnasia integral", "schedules": [("Lunes y martes", "12:00–13:00")]},
            {"name": "Círculo de mujeres", "schedules": [("Jueves", "10:00–12:00")]},
            {"name": "Lecturas al paso", "schedules": [("Miércoles", "10:00–11:00")]},
            {
                "name": "Club del bordado “Hilando comunidad” (+18 años)",
                "schedules": [("Martes", "15:30–17:30")],
            },
            {
                "name": "Mini club de lectura y bordado",
                "schedules": [("Miércoles", "14:00–15:00")],
            },
            {"name": "Latidos de corazón", "schedules": [("Lunes", "14:00–16:00")]},
            {"name": "Taller de arte (+15 años)", "schedules": [("Lunes", "16:00–17:00")]},
            {"name": "Arte, color y muralismo", "schedules": [("Lunes", "17:00–19:00")]},
            {
                "name": "Taller de expresividad artística, grabado, pintura y escultura",
                "schedules": [("Miércoles", "11:00–13:00")],
            },
            {
                "name": "Ensamble creativo: taller de arte y construcciones colectivas (12 a 17 años)",
                "schedules": [("Martes", "18:00–19:00")],
            },
            {
                "name": "Taller de vientos (8 a 16 años)",
                "schedules": [("Jueves", "15:30–17:00")],
            },
            {
                "name": "Taller de vientos (+18 años)",
                "schedules": [("Jueves", "17:00–18:30")],
            },
            {"name": "Hockey (6 a 9 años)", "schedules": [("Martes y jueves", "17:30–18:30")]},
            {"name": "Hockey (10 a 14 años)", "schedules": [("Martes y jueves", "16:00–17:30")]},
            {"name": "Hockey (+15 años)", "schedules": [("Martes y jueves", "14:00–16:00")]},
            {"name": "Atletismo", "schedules": [("Martes y jueves", "17:00–18:30")]},
            {
                "name": "Laboratorio de bicicletas",
                "schedules": [("Lunes y miércoles", "17:00–18:30")],
            },
            {"name": "Fútbol", "schedules": [("Viernes", "17:00–20:00")]},
            {
                "name": "Fútbol infantil (5 a 8 años)",
                "schedules": [("Martes", "17:00–19:00")],
            },
            {
                "name": "Taller de teatro (+7 años)",
                "schedules": [("Lunes", "14:00–17:00"), ("Jueves", "17:00–19:00")],
            },
            {
                "name": "Construcción y manipulación de títeres",
                "schedules": [("Jueves", "14:00–16:00")],
            },
            {"name": "Ludoteca musical", "schedules": [("Lunes", "17:00–18:30")]},
            {
                "name": "Recreación en cancha dividida",
                "schedules": [
                    ("Lunes y miércoles", "15:00–17:00"),
                    ("Viernes", "15:00–16:00"),
                ],
            },
            {
                "name": "Paddle",
                "schedules": [("Lunes, miércoles y viernes", "14:00–15:00")],
            },
            {
                "name": "Vóley para jóvenes y adultos",
                "schedules": [
                    ("Lunes y miércoles", "17:30–19:00"),
                    ("Viernes", "16:00–17:00"),
                ],
            },
            {
                "name": "Zumba",
                "schedules": [("Lunes y viernes", "16:00–17:00"), ("Martes", "14:00–15:00")],
            },
            {"name": "Baby ballet (3 a 8 años)", "schedules": [("Lunes", "17:00–18:00")]},
            {
                "name": "Folclore infantil (6 a 10 años)",
                "schedules": [("Lunes", "18:00–19:00")],
            },
            {
                "name": "Folclore adultos: canto y baile",
                "schedules": [("Martes", "15:30–17:00")],
            },
            {
                "name": "Comedia musical (6 a 12 años)",
                "schedules": [("Martes", "17:00–19:00")],
            },
            {
                "name": "Taller de música “Los Cántaros” (+16)",
                "schedules": [("Miércoles", "14:00–16:00")],
            },
            {
                "name": "Escuela primaria, modalidad adulto",
                "schedules": [
                    ("Lunes, martes, miércoles y viernes", "08:30–12:30"),
                    ("Lunes, martes, miércoles y viernes", "14:00–17:00"),
                ],
            },
            {
                "name": "CENMA, sede Parque Educativo",
                "schedules": [("Martes y miércoles", "14:00–17:00")],
            },
        ],
    },
    {
        "name": "Inglés",
        "activities": [
            {
                "name": "Taller de inglés (+18 años)",
                "schedules": [("Lunes", "09:00–10:30"), ("Miércoles", "09:00–10:30")],
            },
            {
                "name": "Jugando en inglés (3 y 4 años)",
                "schedules": [("Lunes", "10:30–11:00")],
            },
            {
                "name": "Jugando en inglés (5 años)",
                "schedules": [("Lunes", "11:00–11:40")],
            },
            {
                "name": "Apoyo escolar de inglés (nivel primario y secundario)",
                "schedules": [("Martes", "12:00–14:00"), ("Jueves", "10:00–12:00")],
            },
            {
                "name": "Aprendiendo inglés a través del arte (6 a 10 años)",
                "schedules": [("Martes", "16:00–18:00"), ("Viernes", "15:00–16:00")],
            },
            {
                "name": "Taller de inglés avanzado (+18 años)",
                "schedules": [("Miércoles", "10:45–12:00")],
            },
            {
                "name": "English club: taller para niños (7 a 12 años)",
                "schedules": [("Viernes", "16:00–18:00")],
            },
        ],
    },
    {
        "name": "Tecnoteca CREA",
        "activities": [
            {
                "name": "Informática básica para adultos mayores",
                "schedules": [("Martes y jueves", "08:30–10:00")],
            },
            {
                "name": "Informática avanzada para adultos mayores",
                "schedules": [("Martes y jueves", "10:30–12:00")],
            },
            {
                "name": "Programación y robótica",
                "schedules": [("Lunes y miércoles", "17:30–19:15")],
            },
            {
                "name": "Alfabetización inicial",
                "schedules": [("Martes y jueves", "17:30–19:15")],
            },
            {
                "name": "Streaming, creación de videos (8 a 15 años)",
                "schedules": [("Lunes", "17:30–19:00")],
            },
            {
                "name": "Streaming adaptado",
                "schedules": [("Miércoles", "14:00–16:00")],
            },
            {
                "name": "Espacio gaming: navegación libre",
                "schedules": [
                    ("Martes", "16:30–17:30"),
                    ("Miércoles", "16:30–17:30"),
                    ("Viernes", "16:30–18:00"),
                ],
            },
            {
                "name": "Taller de diseño e impresión 3D (8 a 14 años)",
                "schedules": [("Viernes", "18:00–19:15")],
            },
            {
                "name": "Punto digital / validación de app Mi Argentina",
                "schedules": [
                    ("Lunes", "16:30–17:00"),
                    ("Martes", "12:00–13:00 y 15:30–16:30"),
                    ("Miércoles", "10:00–11:00"),
                    ("Jueves", "12:00–13:00"),
                    ("Viernes", "15:30–16:30"),
                ],
            },
            {"name": "CIDI-VEDI", "schedules": [("Lunes a viernes", "10:30–12:00")]},
        ],
    },
]


@router.get("/actividades")
def activities_page(
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return templates.TemplateResponse(
        request=request,
        name="activities.html",
        context=template_context(request, user, activity_groups=ACTIVITY_GROUPS),
    )
