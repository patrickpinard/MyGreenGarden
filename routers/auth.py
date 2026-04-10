"""
MyGreenGarden V7.0 — Authentification par code PIN.
Support multi-utilisateurs avec rôles admin/user.
Session signée via cookie (Starlette SessionMiddleware).
"""
import logging
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models.user import User
from models.event import Event

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals["owner_name"] = settings.owner_name

SESSION_KEY = "authenticated"


def is_authenticated(request: Request) -> bool:
    return request.session.get(SESSION_KEY) is True


def is_admin(request: Request) -> bool:
    if not is_authenticated(request):
        return False
    role = request.session.get("role")
    # Compat ascendante : sessions sans rôle (avant le système multi-utilisateurs) → admin
    return role == "admin" or role is None


def require_auth(request: Request) -> RedirectResponse | None:
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    return None


def require_admin(request: Request) -> RedirectResponse | None:
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    role = request.session.get("role")
    # Compat ascendante : sessions sans rôle → traiter comme admin
    if role is not None and role != "admin":
        return RedirectResponse("/dashboard", status_code=303)
    return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, pin: str = Form(...), db: Session = Depends(get_db)):
    matched_user = None

    # ── 1. Chercher dans la table users ──────────────────────────────────────
    users = db.query(User).filter_by(enabled=True).all()
    for u in users:
        try:
            if bcrypt.verify(pin, u.pin_hash):
                matched_user = u
                break
        except Exception:
            continue

    # ── 2. Fallback legacy : PIN unique dans .env (si aucun user en DB) ───────
    if matched_user is None and db.query(User).count() == 0:
        if settings.pin_hash:
            valid = bcrypt.verify(pin, settings.pin_hash)
        else:
            valid = pin == "1234"
        if valid:
            request.session[SESSION_KEY]  = True
            request.session["username"]   = settings.owner_name
            request.session["role"]       = "admin"
            logger.info(f"Auth legacy réussie — {settings.owner_name}")
            db.add(Event(level="INFO", category="AUTH",
                         message=f"Connexion — {settings.owner_name} (legacy)"))
            db.commit()
            return RedirectResponse("/dashboard", status_code=303)

    if matched_user:
        request.session[SESSION_KEY]  = True
        request.session["username"]   = matched_user.username
        request.session["role"]       = matched_user.role
        logger.info(f"Auth réussie — {matched_user.username} ({matched_user.role})")
        db.add(Event(level="INFO", category="AUTH",
                     message=f"Connexion — {matched_user.username} ({matched_user.role})"))
        db.commit()
        return RedirectResponse("/dashboard", status_code=303)

    logger.warning("Tentative d'authentification avec PIN incorrect")
    db.add(Event(level="WARNING", category="AUTH",
                 message="Tentative de connexion échouée (PIN incorrect)"))
    db.commit()
    return templates.TemplateResponse(
        request, "login.html",
        {"error": "Code PIN incorrect. Réessayez."},
        status_code=401,
    )


@router.post("/logout")
@router.get("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    username = request.session.get("username", "inconnu")
    db.add(Event(level="INFO", category="AUTH", message=f"Déconnexion — {username}"))
    db.commit()
    request.session.clear()
    logger.info(f"Déconnexion — {username}")
    return RedirectResponse("/login", status_code=303)
