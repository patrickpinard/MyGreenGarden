"""
MyGreenGarden V7.0 — Service notifications push Web Push / VAPID.
Compatible iOS 16.4+ (iPhone 17 Pro, iPad), Android Chrome, Safari desktop.
"""
import json
import logging
from sqlalchemy.orm import Session
from models.push_subscription import PushSubscription
from config import settings

logger = logging.getLogger(__name__)


def _get_webpush():
    """Import lazy pour ne pas crasher si pywebpush n'est pas installé."""
    try:
        from pywebpush import webpush, WebPushException
        return webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush non installé — notifications push désactivées")
        return None, None


def send_push_notification(db: Session, title: str, body: str, icon: str = "/static/img/icon-192.png") -> int:
    """
    Envoie une notification push à tous les appareils abonnés.
    Retourne le nombre d'envois réussis.
    """
    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.debug("VAPID non configuré — notification ignorée")
        return 0

    webpush, WebPushException = _get_webpush()
    if webpush is None:
        return 0

    subscriptions = db.query(PushSubscription).all()
    success = 0
    to_delete = []

    payload = json.dumps({
        "title": title,
        "body":  body,
        "icon":  icon,
        "badge": "/static/img/badge-72.png",
        "data":  {"url": "/dashboard"},
    })

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=sub.subscription_info(),
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
            success += 1
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                # Abonnement expiré ou invalide → supprimer
                to_delete.append(sub.id)
                logger.info(f"Abonnement push expiré supprimé (id={sub.id})")
            else:
                logger.error(f"Erreur push vers {sub.device_label}: {e}")
        except Exception as e:
            logger.error(f"Erreur push inattendue: {e}")

    # Nettoyage abonnements invalides
    if to_delete:
        db.query(PushSubscription).filter(PushSubscription.id.in_(to_delete)).delete(
            synchronize_session=False
        )
        db.commit()

    logger.info(f"Push envoyé : {success}/{len(subscriptions)} appareils")
    return success


def subscribe(db: Session, endpoint: str, p256dh: str, auth: str, device_label: str = "") -> PushSubscription:
    """Enregistre ou met à jour un abonnement push."""
    sub = db.query(PushSubscription).filter_by(endpoint=endpoint).first()
    if sub:
        sub.p256dh = p256dh
        sub.auth   = auth
        sub.device_label = device_label or sub.device_label
    else:
        sub = PushSubscription(
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            device_label=device_label,
        )
        db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def unsubscribe(db: Session, endpoint: str) -> bool:
    """Supprime un abonnement push."""
    sub = db.query(PushSubscription).filter_by(endpoint=endpoint).first()
    if sub:
        db.delete(sub)
        db.commit()
        return True
    return False
