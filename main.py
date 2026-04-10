"""
MyGreenGarden V7.0 — Point d'entrée FastAPI.
Auteur  : Patrick Pinard
Date    : 2025
Version : 7.0
"""
import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from database import init_db, SessionLocal
from models.config_entry import ConfigEntry, DEFAULT_CONFIG
from models.schedule import WateringSchedule
from models.user import User

# ── Hardware ──────────────────────────────────────────────────────────────────
from hardware.sensors import Temperatures, MoistureSensor, Anemometer
from hardware.actuators import Light, Fan, WaterValve, SkyLight

# ── Services ──────────────────────────────────────────────────────────────────
from services.automation import run_automation_cycle, run_scheduled_watering
from services.scheduler_service import (
    scheduler, start_scheduler, stop_scheduler,
    add_automation_job, add_watering_schedule,
)
from services.state import garden_state

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import auth, pages, api, push

# ─── Logging ──────────────────────────────────────────────────────────────────
Path("data").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%d.%m.%Y %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data/mygreengarden.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("mygreengarden")


# ─── Initialisation DB (config par défaut) ────────────────────────────────────
def _seed_default_users(db) -> None:
    """Crée l'admin par défaut depuis .env si la table users est vide."""
    if db.query(User).count() == 0 and settings.pin_hash:
        from passlib.hash import bcrypt
        db.add(User(
            username=settings.owner_name,
            pin_hash=settings.pin_hash,
            role="admin",
        ))
        db.commit()
        logger.info(f"Utilisateur admin '{settings.owner_name}' créé depuis .env")


def _seed_default_config(db) -> None:
    """Insère les paramètres par défaut si la table config est vide."""
    if db.query(ConfigEntry).count() == 0:
        for key, (value, type_, description) in DEFAULT_CONFIG.items():
            db.add(ConfigEntry(key=key, value=value, type=type_, description=description))
        db.commit()
        logger.info("Paramètres par défaut insérés en DB")


def _load_watering_schedules(app, db) -> None:
    """Recharge les plannings d'arrosage depuis la DB au démarrage."""
    schedules = db.query(WateringSchedule).filter_by(enabled=True).all()
    for s in schedules:
        add_watering_schedule(
            s.id, s.zone, s.duration, s.hour, s.minute, s.days,
            run_scheduled_watering, app.state.actuators, SessionLocal,
        )
    logger.info(f"{len(schedules)} planning(s) d'arrosage chargé(s)")


def _get_automation_interval(db) -> int:
    cfg = db.query(ConfigEntry).filter_by(key="AUTOMATION_INTERVAL").first()
    return int(cfg.value) if cfg else 900


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"=== MyGreenGarden V7.0 démarrage ===")

    # 1. Base de données
    init_db()
    db = SessionLocal()
    _seed_default_config(db)
    _seed_default_users(db)

    # 2. Hardware — capteurs
    sensors = (
        Temperatures(),
        MoistureSensor(zone=1, adc_channel=0),
        MoistureSensor(zone=2, adc_channel=1),
        Anemometer(adc_channel=4),
    )
    app.state.sensors = sensors

    # 3. Hardware — actionneurs
    actuators = {
        "fan":    Fan(),
        "light":  Light(),
        "valve1": WaterValve(zone=1),
        "valve2": WaterValve(zone=2),
        "window": SkyLight(),
    }
    app.state.actuators = actuators

    # 4. Scheduler
    start_scheduler()
    interval = _get_automation_interval(db)
    add_automation_job(interval, run_automation_cycle, sensors, actuators, SessionLocal)
    _load_watering_schedules(app, db)
    db.close()

    logger.info(f"Automation démarrée — cycle toutes les {interval}s")
    logger.info(f"Mode simulation : {settings.simulation_mode}")
    logger.info("Serveur prêt — http://0.0.0.0:8000")

    yield  # ← l'application tourne ici

    # Shutdown propre
    logger.info("Arrêt en cours...")
    stop_scheduler()
    # Fermer toutes les vannes par sécurité
    for valve in [actuators["valve1"], actuators["valve2"]]:
        valve.close()
    logger.info("=== MyGreenGarden arrêté ===")


# ─── Application FastAPI ──────────────────────────────────────────────────────
app = FastAPI(
    title="MyGreenGarden V7.0",
    description="Gestion automatisée de serre — Patrick Pinard",
    version="7.0",
    docs_url="/docs" if settings.debug else None,   # Swagger uniquement en debug
    redoc_url=None,
    lifespan=lifespan,
)

# Middleware session (cookie signé)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    max_age=settings.session_timeout_hours * 3600,
    same_site="lax",
    https_only=False,  # mettre True si HTTPS activé
)

# Fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(api.router)
app.include_router(push.router)


# ─── Lancement direct ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
