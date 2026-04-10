"""
Modèle SQLAlchemy — Abonnements notifications push (Web Push / VAPID).
Stocke les endpoints des appareils iOS/iPadOS/desktop abonnés.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Identifiant unique de l'appareil (user-agent hash ou label)
    device_label: Mapped[str] = mapped_column(String(100), default="")

    # Données Web Push API
    endpoint: Mapped[str] = mapped_column(String(500), unique=True)
    p256dh: Mapped[str] = mapped_column(String(200))   # clé publique du navigateur
    auth: Mapped[str] = mapped_column(String(100))      # secret d'authentification

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_label": self.device_label,
            "endpoint": self.endpoint,
            "created_at": self.created_at.isoformat(),
        }

    def subscription_info(self) -> dict:
        """Format attendu par pywebpush."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth,
            },
        }
