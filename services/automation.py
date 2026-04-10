"""
MyGreenGarden V7.0 — Logique d'automatisation principale.
Remplace la fonction WateringAndAerate() de V6.
Gère : ventilation, arrosage par seuil, lucarne, mode nuit, alertes.
"""
import logging
import psutil
from datetime import datetime, time as dtime
from sqlalchemy.orm import Session

from services.state import garden_state
from services.email_service import send_alert_email
from models.measurement import Measurement
from models.event import Event
from models.config_entry import ConfigEntry

logger = logging.getLogger(__name__)


def _get_config(db: Session) -> dict:
    """Charge tous les paramètres depuis la DB."""
    rows = db.query(ConfigEntry).all()
    return {r.key: r.typed_value() for r in rows}


def _is_night_mode(cfg: dict) -> bool:
    """Détermine si on est en période nocturne."""
    if not cfg.get("NIGHT_MODE_ENABLED", False):
        return False
    now_t = datetime.now().time()
    try:
        h_start, m_start = map(int, cfg["NIGHT_START"].split(":"))
        h_end,   m_end   = map(int, cfg["NIGHT_END"].split(":"))
        start = dtime(h_start, m_start)
        end   = dtime(h_end,   m_end)
    except Exception:
        return False
    # Gère le cas où la nuit chevauche minuit (ex: 22:00 → 07:00)
    if start > end:
        return now_t >= start or now_t < end
    return start <= now_t < end


def _read_cpu_stats() -> tuple[float, float]:
    """Retourne (temp_cpu_°C, usage_cpu_%)."""
    try:
        temps = psutil.sensors_temperatures()
        if temps and "cpu_thermal" in temps:
            cpu_temp = temps["cpu_thermal"][0].current
        elif temps and "coretemp" in temps:
            cpu_temp = temps["coretemp"][0].current
        else:
            cpu_temp = 0.0
    except Exception:
        cpu_temp = 0.0
    cpu_usage = psutil.cpu_percent(interval=0.5)
    return round(cpu_temp, 1), round(cpu_usage, 1)


def _log_event(db: Session, message: str, level: str = "INFO", category: str = "SYSTEM") -> None:
    event = Event(level=level, category=category, message=message)
    db.add(event)
    db.commit()
    logger.info(f"[{level}] {message}")


def run_automation_cycle(
    db: Session,
    sensors,   # sensors_bundle (tuple de capteurs)
    actuators, # actuators_bundle (dict d'actionneurs)
) -> None:
    """
    Cycle principal d'automatisation — appelé par APScheduler toutes les N secondes.
    sensors  : (Temperatures, MoistureSensor_z1, MoistureSensor_z2, Anemometer)
    actuators: {"fan": Fan, "valve1": WaterValve, "valve2": WaterValve,
                "light": Light, "window": SkyLight}
    """
    temps_sensor, moist1, moist2, anemo = sensors
    cfg = _get_config(db)
    night = _is_night_mode(cfg)

    period = "nuit" if night else "jour"
    _log_event(db, f"Démarrage cycle automation ({period})", "INFO", "SYSTEM")

    # ── 1. Lecture capteurs ───────────────────────────────────────────────────
    try:
        temp_reading = temps_sensor.read()
        m1, m1_label = moist1.read()
        m2, m2_label = moist2.read()
        wind = anemo.read()
        cpu_temp, cpu_usage = _read_cpu_stats()
    except Exception as e:
        _log_event(db, f"Erreur lecture capteurs: {e}", "ERROR", "SENSOR")
        return

    # Mise à jour état global
    garden_state.update_sensors(
        temp_inside=temp_reading.inside,
        temp_outside=temp_reading.outside,
        moisture_zone1=m1,
        moisture_zone2=m2,
        moisture_zone1_label=m1_label,
        moisture_zone2_label=m2_label,
        wind_speed=wind,
        cpu_temp=cpu_temp,
        cpu_usage=cpu_usage,
    )

    _log_event(
        db,
        f"T°int={temp_reading.inside}°C  T°ext={temp_reading.outside}°C  "
        f"Sol Z1={m1:.0f}%  Sol Z2={m2:.0f}%  Vent={wind}km/h",
        "INFO", "SENSOR"
    )

    # ── 2. Seuils actifs selon mode nuit/jour ─────────────────────────────────
    if night:
        temp_max  = cfg.get("NIGHT_TEMP_MAX",       25.0)
        temp_min  = cfg.get("NIGHT_TEMP_MIN",        18.0)
        moist_th1 = cfg.get("NIGHT_MOISTURE_ZONE_1", 55.0)
        moist_th2 = cfg.get("NIGHT_MOISTURE_ZONE_2", 55.0)
    else:
        temp_max  = cfg.get("TEMP_MAX_THRESHOLD",    35.0)
        temp_min  = cfg.get("TEMP_MIN_THRESHOLD",    30.0)
        moist_th1 = cfg.get("MOISTURE_THRESHOLD_ZONE_1", 65.0)
        moist_th2 = cfg.get("MOISTURE_THRESHOLD_ZONE_2", 65.0)

    watering_t1 = cfg.get("WATERING_TIME_ZONE_1", 300)
    watering_t2 = cfg.get("WATERING_TIME_ZONE_2", 300)
    wind_limit  = cfg.get("WINDSPEED_LIMIT",       40.0)

    # ── 3. Contrôle température → ventilateurs ────────────────────────────────
    fan = actuators["fan"]
    if garden_state.fan_auto:
        if temp_reading.inside > temp_max and not garden_state.fan_on:
            fan.on()
            garden_state.fan_on = True
            _log_event(db, f"Ventilateurs ON (T°={temp_reading.inside}°C > {temp_max}°C)", "INFO", "ACTUATOR")
        elif temp_reading.inside < temp_min and garden_state.fan_on:
            fan.off()
            garden_state.fan_on = False
            _log_event(db, f"Ventilateurs OFF (T°={temp_reading.inside}°C < {temp_min}°C)", "INFO", "ACTUATOR")

    # ── 4. Contrôle vent → alerte (lucarne non installée) ────────────────────
    if wind > wind_limit:
        msg = f"Vent fort : {wind} km/h (limite {wind_limit} km/h)"
        _log_event(db, msg, "WARNING", "ALERT")
        garden_state.add_alert("warning", msg)

    # ── 5. Arrosage par seuil d'humidité (zones indépendantes) ───────────────────
    if garden_state.watering_auto_z1:
        valve1 = actuators["valve1"]
        if m1 < moist_th1:
            garden_state.watering_count_z1 += 1
            _log_event(
                db,
                f"Arrosage zone 1 — humidité {m1:.0f}% < seuil {moist_th1:.0f}%  "
                f"(cycle #{garden_state.watering_count_z1})",
                "INFO", "WATERING"
            )
            garden_state.valve1_open = True
            valve1.water(watering_t1)
            garden_state.valve1_open = False

            if garden_state.watering_count_z1 >= 3:
                alert_msg = (
                    f"ALERTE : {garden_state.watering_count_z1} arrosages consécutifs zone 1 "
                    f"— vérifier la sonde humidité !"
                )
                _log_event(db, alert_msg, "ERROR", "ALERT")
                garden_state.add_alert("error", alert_msg)
                send_alert_email("⚠️ MyGreenGarden — Arrosage zone 1 anormal", alert_msg)
        else:
            garden_state.watering_count_z1 = 0

    if garden_state.watering_auto_z2:
        valve2 = actuators["valve2"]
        if m2 < moist_th2:
            garden_state.watering_count_z2 += 1
            _log_event(
                db,
                f"Arrosage zone 2 — humidité {m2:.0f}% < seuil {moist_th2:.0f}%  "
                f"(cycle #{garden_state.watering_count_z2})",
                "INFO", "WATERING"
            )
            garden_state.valve2_open = True
            valve2.water(watering_t2)
            garden_state.valve2_open = False

            if garden_state.watering_count_z2 >= 3:
                alert_msg = (
                    f"ALERTE : {garden_state.watering_count_z2} arrosages consécutifs zone 2 "
                    f"— vérifier la sonde humidité !"
                )
                _log_event(db, alert_msg, "ERROR", "ALERT")
                garden_state.add_alert("error", alert_msg)
                send_alert_email("⚠️ MyGreenGarden — Arrosage zone 2 anormal", alert_msg)
        else:
            garden_state.watering_count_z2 = 0

    # ── 6. Sauvegarde mesure en DB ────────────────────────────────────────────
    measurement = Measurement(
        timestamp=datetime.utcnow(),
        temp_inside=temp_reading.inside,
        temp_outside=temp_reading.outside,
        moisture_zone1=m1,
        moisture_zone2=m2,
        wind_speed=wind,
        cpu_temp=cpu_temp,
        cpu_usage=cpu_usage,
        fan_on=garden_state.fan_on,
        light_on=garden_state.light_on,
        window_open=garden_state.window_open,
        valve1_open=False,
        valve2_open=False,
    )
    db.add(measurement)
    db.commit()


def run_scheduled_watering(zone: int, duration: int, actuators: dict, db: Session) -> None:
    """
    Arrosage planifié (déclenché par APScheduler à heure fixe).
    Indépendant du mode auto/manuel.
    """
    valve = actuators[f"valve{zone}"]
    _log_event(db, f"Arrosage planifié zone {zone} — {duration}s", "INFO", "WATERING")
    if zone == 1:
        garden_state.valve1_open = True
    else:
        garden_state.valve2_open = True
    valve.water(duration)
    if zone == 1:
        garden_state.valve1_open = False
    else:
        garden_state.valve2_open = False
    _log_event(db, f"Arrosage planifié zone {zone} terminé", "INFO", "WATERING")
