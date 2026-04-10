"""
MyGreenGarden V7.0 — API REST JSON.
Toutes les routes /api/* retournent du JSON.
Protégées par session (vérification via cookie).
"""
import asyncio
import logging
import os
import subprocess
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from routers.auth import is_authenticated, is_admin
from models.user import User
from services.state import garden_state
from services.scheduler_service import add_automation_job, scheduler
from models.measurement import Measurement
from models.event import Event
from models.config_entry import ConfigEntry
from models.schedule import WateringSchedule
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def _check_auth(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Non authentifié")


# ─── État global ──────────────────────────────────────────────────────────────

@router.get("/state")
async def get_state(request: Request):
    _check_auth(request)
    return JSONResponse(garden_state.to_dict())


@router.get("/status")
async def get_status(request: Request):
    """Statut rapide pour le polling AJAX (léger)."""
    _check_auth(request)
    s = garden_state
    return {
        "temp_inside":    s.temp_inside,
        "temp_outside":   s.temp_outside,
        "moisture_zone1": s.moisture_zone1,
        "moisture_zone2": s.moisture_zone2,
        "wind_speed":     s.wind_speed,
        "fan_on":         s.fan_on,
        "light_on":       s.light_on,
        "valve1_open":    s.valve1_open,
        "valve2_open":    s.valve2_open,
        "window_open":    s.window_open,
        "alerts":         s.alerts,
        "last_update":    s.last_update.isoformat() if s.last_update else None,
    }


# ─── Contrôle actionneurs ─────────────────────────────────────────────────────

@router.post("/actuator/fan")
async def control_fan(request: Request):
    _check_auth(request)
    data = await request.json()
    state = data.get("state")
    actuators = request.app.state.actuators
    fan = actuators["fan"]
    if state is True:
        fan.on()
        garden_state.fan_on = True
    elif state is False:
        fan.off()
        garden_state.fan_on = False
    else:
        fan.toggle()
        garden_state.fan_on = fan.state
    logger.info(f"Ventilateurs → {'ON' if garden_state.fan_on else 'OFF'} (manuel)")
    return {"fan_on": garden_state.fan_on}


@router.post("/actuator/light")
async def control_light(request: Request):
    _check_auth(request)
    data = await request.json()
    state = data.get("state")
    actuators = request.app.state.actuators
    light = actuators["light"]
    if state is True:
        light.on()
        garden_state.light_on = True
    elif state is False:
        light.off()
        garden_state.light_on = False
    else:
        light.toggle()
        garden_state.light_on = light.state
    return {"light_on": garden_state.light_on}


@router.post("/actuator/valve/{zone}")
async def control_valve(zone: int, request: Request, db: Session = Depends(get_db)):
    _check_auth(request)
    if zone not in (1, 2):
        raise HTTPException(400, "Zone invalide (1 ou 2)")
    data = await request.json()
    duration = data.get("duration", 30)   # durée en secondes (défaut 30s pour test manuel)
    actuators = request.app.state.actuators
    valve = actuators[f"valve{zone}"]

    import threading
    def _water():
        if zone == 1:
            garden_state.valve1_open = True
        else:
            garden_state.valve2_open = True
        valve.water(duration)
        if zone == 1:
            garden_state.valve1_open = False
        else:
            garden_state.valve2_open = False

    # Arrosage dans un thread séparé pour ne pas bloquer la réponse
    t = threading.Thread(target=_water, daemon=True)
    t.start()
    return {"message": f"Arrosage zone {zone} démarré ({duration}s)"}


@router.post("/actuator/valve/{zone}/stop")
async def stop_valve(zone: int, request: Request):
    _check_auth(request)
    if zone not in (1, 2):
        raise HTTPException(400, "Zone invalide")
    actuators = request.app.state.actuators
    valve = actuators[f"valve{zone}"]
    valve.close()
    if zone == 1:
        garden_state.valve1_open = False
    else:
        garden_state.valve2_open = False
    return {"message": f"Vanne zone {zone} fermée"}


@router.post("/mode/fan_auto")
async def toggle_fan_auto(request: Request):
    _check_auth(request)
    data = await request.json()
    garden_state.fan_auto = data.get("enabled", not garden_state.fan_auto)
    return {"fan_auto": garden_state.fan_auto}


@router.post("/mode/watering_auto_z1")
async def toggle_watering_auto_z1(request: Request):
    _check_auth(request)
    data = await request.json()
    garden_state.watering_auto_z1 = data.get("enabled", not garden_state.watering_auto_z1)
    return {"watering_auto_z1": garden_state.watering_auto_z1}


@router.post("/mode/watering_auto_z2")
async def toggle_watering_auto_z2(request: Request):
    _check_auth(request)
    data = await request.json()
    garden_state.watering_auto_z2 = data.get("enabled", not garden_state.watering_auto_z2)
    return {"watering_auto_z2": garden_state.watering_auto_z2}


@router.post("/mode/window_auto")
async def toggle_window_auto(request: Request):
    _check_auth(request)
    data = await request.json()
    garden_state.window_auto = data.get("enabled", not garden_state.window_auto)
    return {"window_auto": garden_state.window_auto}


# ─── Historique / Graphiques ──────────────────────────────────────────────────

PERIOD_HOURS = {"1h": 1, "6h": 6, "24h": 24, "7j": 168, "30j": 720}

@router.get("/history")
async def get_history(request: Request, period: str = "24h", db: Session = Depends(get_db)):
    _check_auth(request)
    hours = PERIOD_HOURS.get(period, 24)
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.query(Measurement)
        .filter(Measurement.timestamp >= since)
        .order_by(Measurement.timestamp.asc())
        .all()
    )
    return {
        "period": period,
        "count": len(rows),
        "data": [r.to_dict() for r in rows],
    }


@router.get("/history/export")
async def export_history(request: Request, period: str = "7j", db: Session = Depends(get_db)):
    """Export CSV de l'historique."""
    from fastapi.responses import Response
    _check_auth(request)
    hours = PERIOD_HOURS.get(period, 168)
    since = datetime.utcnow() - timedelta(hours=hours)
    rows = db.query(Measurement).filter(Measurement.timestamp >= since).order_by(Measurement.timestamp).all()

    lines = ["timestamp,temp_inside,temp_outside,moisture_zone1,moisture_zone2,wind_speed,cpu_temp"]
    for r in rows:
        lines.append(
            f"{r.timestamp},{r.temp_inside},{r.temp_outside},"
            f"{r.moisture_zone1},{r.moisture_zone2},{r.wind_speed},{r.cpu_temp}"
        )
    csv = "\n".join(lines)
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mygreengarden_{period}.csv"},
    )


# ─── Paramètres ───────────────────────────────────────────────────────────────

@router.get("/config")
async def get_config(request: Request, db: Session = Depends(get_db)):
    _check_auth(request)
    rows = db.query(ConfigEntry).all()
    return {r.key: {"value": r.typed_value(), "type": r.type, "description": r.description}
            for r in rows}


@router.post("/config")
async def save_config(request: Request, db: Session = Depends(get_db)):
    _check_auth(request)
    data = await request.json()
    for key, value in data.items():
        entry = db.query(ConfigEntry).filter_by(key=key).first()
        if entry:
            entry.value = str(value)
    db.commit()

    # Recharger l'intervalle si modifié
    if "AUTOMATION_INTERVAL" in data:
        new_interval = int(data["AUTOMATION_INTERVAL"])
        sensors = request.app.state.sensors
        actuators = request.app.state.actuators
        from services.automation import run_automation_cycle
        from database import SessionLocal
        add_automation_job(new_interval, run_automation_cycle, sensors, actuators, SessionLocal)

    return {"message": "Paramètres sauvegardés"}


# ─── Événements ───────────────────────────────────────────────────────────────

@router.get("/events")
async def get_events(
    request: Request,
    limit: int = 1000,
    level: str = None,
    category: str = None,
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(get_db),
):
    _check_auth(request)
    q = db.query(Event).order_by(Event.timestamp.desc())
    if level:
        q = q.filter(Event.level == level.upper())
    if category:
        q = q.filter(Event.category == category.upper())
    if date_from:
        try:
            q = q.filter(Event.timestamp >= datetime.fromisoformat(date_from.replace("Z", "+00:00").replace("+00:00", "")))
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(Event.timestamp < datetime.fromisoformat(date_to.replace("Z", "+00:00").replace("+00:00", "")))
        except ValueError:
            pass
    events = q.limit(limit).all()
    return {"events": [e.to_dict() for e in events]}


@router.delete("/events")
async def delete_events(request: Request, db: Session = Depends(get_db)):
    """Supprime tous les événements."""
    _check_auth(request)
    count = db.query(Event).delete()
    db.commit()
    logger.warning(f"Historique événements effacé ({count} entrées)")
    return {"deleted": count}


# ─── Planification arrosage ───────────────────────────────────────────────────

class ScheduleCreate(BaseModel):
    zone: int
    label: str = ""
    hour: int
    minute: int
    duration: int = 300
    days: str = "1111111"
    enabled: bool = True


@router.get("/schedules")
async def list_schedules(request: Request, db: Session = Depends(get_db)):
    _check_auth(request)
    rows = db.query(WateringSchedule).order_by(WateringSchedule.zone, WateringSchedule.hour).all()
    return {"schedules": [r.to_dict() for r in rows]}


@router.post("/schedules")
async def create_schedule(request: Request, payload: ScheduleCreate, db: Session = Depends(get_db)):
    _check_auth(request)
    s = WateringSchedule(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)

    # Enregistrer dans APScheduler
    from services.scheduler_service import add_watering_schedule
    from services.automation import run_scheduled_watering
    from database import SessionLocal
    actuators = request.app.state.actuators
    add_watering_schedule(
        s.id, s.zone, s.duration, s.hour, s.minute, s.days,
        run_scheduled_watering, actuators, SessionLocal
    )
    return s.to_dict()


class ScheduleUpdate(BaseModel):
    zone: int | None = None
    label: str | None = None
    hour: int | None = None
    minute: int | None = None
    duration: int | None = None
    days: str | None = None
    enabled: bool | None = None


@router.put("/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, request: Request, payload: ScheduleUpdate, db: Session = Depends(get_db)):
    _check_auth(request)
    s = db.query(WateringSchedule).filter_by(id=schedule_id).first()
    if not s:
        raise HTTPException(404, "Planning non trouvé")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    from services.scheduler_service import add_watering_schedule, remove_watering_schedule
    from services.automation import run_scheduled_watering
    from database import SessionLocal
    actuators = request.app.state.actuators
    remove_watering_schedule(s.id)
    if s.enabled:
        add_watering_schedule(
            s.id, s.zone, s.duration, s.hour, s.minute, s.days,
            run_scheduled_watering, actuators, SessionLocal
        )
    return s.to_dict()


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, request: Request, db: Session = Depends(get_db)):
    _check_auth(request)
    s = db.query(WateringSchedule).filter_by(id=schedule_id).first()
    if not s:
        raise HTTPException(404, "Planning non trouvé")
    db.delete(s)
    db.commit()
    from services.scheduler_service import remove_watering_schedule
    remove_watering_schedule(schedule_id)
    return {"message": "Planning supprimé"}


@router.patch("/schedules/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: int, request: Request, db: Session = Depends(get_db)):
    _check_auth(request)
    s = db.query(WateringSchedule).filter_by(id=schedule_id).first()
    if not s:
        raise HTTPException(404, "Planning non trouvé")
    s.enabled = not s.enabled
    db.commit()
    from services.scheduler_service import add_watering_schedule, remove_watering_schedule
    from services.automation import run_scheduled_watering
    from database import SessionLocal
    actuators = request.app.state.actuators
    if s.enabled:
        add_watering_schedule(
            s.id, s.zone, s.duration, s.hour, s.minute, s.days,
            run_scheduled_watering, actuators, SessionLocal
        )
    else:
        remove_watering_schedule(s.id)
    return {"id": s.id, "enabled": s.enabled}


# ─── Gestion utilisateurs ────────────────────────────────────────────────────

def _check_admin(request: Request):
    if not is_admin(request):
        raise HTTPException(status_code=403, detail="Accès admin requis")


class UserCreate(BaseModel):
    username: str
    pin: str          # PIN en clair, haché côté serveur
    role: str = "user"


@router.get("/users")
async def list_users(request: Request, db: Session = Depends(get_db)):
    _check_admin(request)
    return {"users": [u.to_dict() for u in db.query(User).order_by(User.username).all()]}


@router.post("/users")
async def create_user(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    _check_admin(request)
    if len(payload.pin) < 4 or not payload.pin.isdigit():
        raise HTTPException(400, "Le PIN doit contenir 4 chiffres")
    if payload.role not in ("admin", "user"):
        raise HTTPException(400, "Rôle invalide")
    if db.query(User).filter_by(username=payload.username).first():
        raise HTTPException(409, "Ce nom d'utilisateur existe déjà")
    from passlib.hash import bcrypt as _bcrypt
    u = User(username=payload.username, pin_hash=_bcrypt.hash(payload.pin), role=payload.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u.to_dict()


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    _check_admin(request)
    if request.session.get("username") and db.query(User).filter_by(
        id=user_id, username=request.session["username"]
    ).first():
        raise HTTPException(400, "Impossible de supprimer votre propre compte")
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "Utilisateur non trouvé")
    db.delete(u)
    db.commit()
    return {"message": "Utilisateur supprimé"}


@router.patch("/users/{user_id}/toggle")
async def toggle_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    _check_admin(request)
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "Utilisateur non trouvé")
    u.enabled = not u.enabled
    db.commit()
    return u.to_dict()


class UserUpdate(BaseModel):
    username: str | None = None
    role: str | None = None
    pin: str | None = None


@router.put("/users/{user_id}")
async def update_user(user_id: int, request: Request, payload: UserUpdate, db: Session = Depends(get_db)):
    _check_admin(request)
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "Utilisateur non trouvé")
    if payload.username is not None:
        if db.query(User).filter(User.username == payload.username, User.id != user_id).first():
            raise HTTPException(409, "Ce nom d'utilisateur existe déjà")
        u.username = payload.username
    if payload.role is not None:
        if payload.role not in ("admin", "user"):
            raise HTTPException(400, "Rôle invalide")
        u.role = payload.role
    if payload.pin is not None and payload.pin != "":
        if len(payload.pin) < 4 or not payload.pin.isdigit():
            raise HTTPException(400, "Le PIN doit contenir 4 chiffres")
        from passlib.hash import bcrypt as _bcrypt
        u.pin_hash = _bcrypt.hash(payload.pin)
    db.commit()
    db.refresh(u)
    return u.to_dict()


@router.put("/users/{user_id}/pin")
async def change_pin(user_id: int, request: Request, db: Session = Depends(get_db)):
    _check_admin(request)
    data = await request.json()
    pin = data.get("pin", "")
    if len(pin) < 4 or not pin.isdigit():
        raise HTTPException(400, "Le PIN doit contenir 4 chiffres")
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(404, "Utilisateur non trouvé")
    from passlib.hash import bcrypt as _bcrypt
    u.pin_hash = _bcrypt.hash(pin)
    db.commit()
    return {"message": "PIN mis à jour"}


# ─── Système ──────────────────────────────────────────────────────────────────

@router.post("/system/force_cycle")
async def force_cycle(request: Request, db: Session = Depends(get_db)):
    """Force l'exécution immédiate d'un cycle automation."""
    _check_auth(request)
    from services.automation import run_automation_cycle
    import threading
    sensors = request.app.state.sensors
    actuators = request.app.state.actuators
    def _run():
        run_automation_cycle(db, sensors, actuators)
    threading.Thread(target=_run, daemon=True).start()
    return {"message": "Cycle forcé démarré"}


@router.post("/system/clear_alerts")
async def clear_alerts(request: Request):
    _check_auth(request)
    garden_state.clear_alerts()
    return {"message": "Alertes effacées"}


@router.get("/system/vapid-public-key")
async def get_vapid_key():
    """Clé publique VAPID pour l'abonnement push côté navigateur."""
    return {"public_key": settings.vapid_public_key}


@router.get("/system/info")
async def system_info(request: Request):
    """Informations système : disque, mémoire, uptime, dernier démarrage."""
    _check_auth(request)
    import shutil, datetime

    result = {}

    # ── Disque ────────────────────────────────────────────────────────────────
    try:
        d = shutil.disk_usage('/')
        result['disk'] = {
            'total':   d.total,
            'used':    d.used,
            'free':    d.free,
            'percent': round(d.used / d.total * 100, 1),
        }
    except Exception:
        result['disk'] = None

    # ── Mémoire + boot via psutil ─────────────────────────────────────────────
    try:
        import psutil
        mem = psutil.virtual_memory()
        result['memory'] = {
            'total':     mem.total,
            'used':      mem.used,
            'available': mem.available,
            'percent':   mem.percent,
        }
        boot_dt = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime  = datetime.datetime.now() - boot_dt
        days, rem = divmod(int(uptime.total_seconds()), 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        result['boot_time']      = boot_dt.strftime('%d.%m.%Y %H:%M')
        result['uptime_seconds'] = int(uptime.total_seconds())
        result['uptime_str']     = (
            (f"{days}j " if days else "") +
            (f"{hours}h " if hours else "") +
            f"{minutes}min"
        )
    except ImportError:
        result['memory']         = None
        result['boot_time']      = None
        result['uptime_seconds'] = None
        result['uptime_str']     = None

    return result


@router.get("/hardware/test")
async def hardware_test(request: Request):
    """Lance un diagnostic complet du hardware et retourne les résultats."""
    _check_auth(request)
    from hardware import SIMULATION
    from hardware.probe import run_full_probe
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: run_full_probe(simulation=SIMULATION))


async def _delayed_command(cmd: list[str], delay: float = 2.0):
    """Attend que la réponse HTTP soit envoyée, puis exécute la commande système."""
    await asyncio.sleep(delay)
    subprocess.Popen(cmd)


@router.post("/system/reboot")
async def reboot(request: Request):
    _check_auth(request)
    logger.warning("Redémarrage du Raspberry Pi demandé")
    asyncio.create_task(_delayed_command(["sudo", "/usr/sbin/reboot"]))
    return {"message": "Redémarrage en cours..."}


@router.post("/system/shutdown")
async def shutdown(request: Request):
    _check_auth(request)
    logger.warning("Arrêt du Raspberry Pi demandé")
    asyncio.create_task(_delayed_command(["sudo", "/usr/sbin/shutdown", "-h", "now"]))
    return {"message": "Arrêt en cours..."}
