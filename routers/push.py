"""
MyGreenGarden V7.0 — Routes notifications push Web Push.
Gestion des abonnements (subscribe / unsubscribe) depuis le navigateur.
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from routers.auth import is_authenticated
from services import push_service

router = APIRouter(prefix="/push")


class SubscriptionPayload(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_label: str = ""


@router.post("/subscribe")
async def subscribe(request: Request, payload: SubscriptionPayload, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return JSONResponse({"error": "Non authentifié"}, status_code=401)
    sub = push_service.subscribe(
        db,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth,
        device_label=payload.device_label,
    )
    return {"message": "Abonnement enregistré", "id": sub.id}


@router.post("/unsubscribe")
async def unsubscribe(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated(request):
        return JSONResponse({"error": "Non authentifié"}, status_code=401)
    data = await request.json()
    removed = push_service.unsubscribe(db, endpoint=data.get("endpoint", ""))
    return {"removed": removed}


@router.post("/test")
async def test_push(request: Request, db: Session = Depends(get_db)):
    """Envoie une notification test à tous les appareils abonnés."""
    if not is_authenticated(request):
        return JSONResponse({"error": "Non authentifié"}, status_code=401)
    count = push_service.send_push_notification(
        db,
        title="MyGreenGarden — Test",
        body="Les notifications push fonctionnent correctement ✓",
    )
    return {"sent": count}
