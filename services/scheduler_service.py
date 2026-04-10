"""
MyGreenGarden V7.0 — Service APScheduler.
Gère le cycle automation (toutes les N secondes) et les arrosages planifiés.
Remplace le Thread Loop de V6.
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="Europe/Zurich")


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler démarré")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler arrêté")


def add_automation_job(interval_seconds: int, func, sensors, actuators, db_factory) -> None:
    """
    Ajoute le job d'automation principal (lecture capteurs + contrôle).
    db_factory : callable qui retourne une session DB.
    """
    def _run():
        db = db_factory()
        try:
            func(db, sensors, actuators)
        except Exception as e:
            logger.error(f"Erreur cycle automation: {e}", exc_info=True)
        finally:
            db.close()

    # Supprimer l'ancien job si existant
    if scheduler.get_job("automation"):
        scheduler.remove_job("automation")

    scheduler.add_job(
        _run,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id="automation",
        name="Cycle automation serre",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(f"Job automation enregistré — intervalle {interval_seconds}s")


def add_watering_schedule(
    schedule_id: int,
    zone: int,
    duration: int,
    hour: int,
    minute: int,
    days: str,         # "1111111" = lun→dim
    func,
    actuators,
    db_factory,
) -> None:
    """Ajoute un arrosage planifié comme job APScheduler."""
    job_id = f"watering_{schedule_id}"

    # Convertir la chaîne de jours en format APScheduler
    # Jours APScheduler : mon, tue, wed, thu, fri, sat, sun
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    active = [day_names[i] for i, d in enumerate(days) if d == "1"]
    if not active:
        logger.warning(f"Planning {schedule_id} ignoré — aucun jour sélectionné")
        return
    days_str = ",".join(active)

    def _run():
        db = db_factory()
        try:
            func(zone=zone, duration=duration, actuators=actuators, db=db)
        except Exception as e:
            logger.error(f"Erreur arrosage planifié zone {zone}: {e}", exc_info=True)
        finally:
            db.close()

    scheduler.add_job(
        _run,
        trigger=CronTrigger(hour=hour, minute=minute, day_of_week=days_str),
        id=job_id,
        name=f"Arrosage planifié zone {zone}",
        replace_existing=True,
        max_instances=1,
    )
    logger.info(f"Arrosage planifié zone {zone} à {hour:02d}:{minute:02d} ({days_str})")


def remove_watering_schedule(schedule_id: int) -> None:
    job_id = f"watering_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Planning {schedule_id} supprimé")


def list_jobs() -> list[dict]:
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]
