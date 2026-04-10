"""
MyGreenGarden V7.0 — Routes des pages HTML (Jinja2).
Toutes les pages protégées nécessitent une session valide.
Starlette >= 0.36 : TemplateResponse(request, name, context)
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from routers.auth import is_authenticated, require_admin
from models.config_entry import ConfigEntry
from models.schedule import WateringSchedule
from services.state import garden_state
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals["owner_name"] = settings.owner_name


def _auth_or_redirect(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    return None


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "dashboard.html", {
        "state": garden_state.to_dict(),
        "page": "dashboard",
    })


@router.get("/capteurs", response_class=HTMLResponse)
async def sensors_page(request: Request):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "sensors.html", {
        "state": garden_state.to_dict(),
        "page": "capteurs",
    })


@router.get("/actionneurs", response_class=HTMLResponse)
async def actuators_page(request: Request):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "actuators.html", {
        "state": garden_state.to_dict(),
        "page": "actionneurs",
    })


@router.get("/graphiques", response_class=HTMLResponse)
async def graphs_page(request: Request):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "graphs.html", {
        "page": "graphiques",
    })


@router.get("/parametres", response_class=HTMLResponse)
async def parameters_page(request: Request, db: Session = Depends(get_db)):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    cfg_rows = db.query(ConfigEntry).all()
    config = {r.key: {"value": r.typed_value(), "description": r.description, "type": r.type}
              for r in cfg_rows}
    return templates.TemplateResponse(request, "parameters.html", {
        "config": config,
        "page": "parametres",
    })


@router.get("/evenements", response_class=HTMLResponse)
async def events_page(request: Request):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "events.html", {"page": "evenements"})


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    redir = require_admin(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "admin.html", {
        "page": "admin",
        "simulation_mode": settings.simulation_mode,
    })


@router.get("/info", response_class=HTMLResponse)
async def info_page(request: Request):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    return templates.TemplateResponse(request, "info.html", {"page": "info"})


@router.get("/planification", response_class=HTMLResponse)
async def schedules_page(request: Request, db: Session = Depends(get_db)):
    redir = _auth_or_redirect(request)
    if redir:
        return redir
    schedules = db.query(WateringSchedule).order_by(WateringSchedule.zone, WateringSchedule.hour).all()
    return templates.TemplateResponse(request, "schedules.html", {
        "schedules": [s.to_dict() for s in schedules],
        "page": "planification",
    })
