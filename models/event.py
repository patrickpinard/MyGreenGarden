"""
Modèle SQLAlchemy — Journal d'événements.
Remplace la liste en mémoire + fichier .log de V6.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Niveaux : INFO, WARNING, ERROR, ALERT
    level: Mapped[str] = mapped_column(String(10), default="INFO")

    # Catégories : SYSTEM, SENSOR, ACTUATOR, WATERING, ALERT, AUTH
    category: Mapped[str] = mapped_column(String(20), default="SYSTEM")

    message: Mapped[str] = mapped_column(String(500))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "date": self.timestamp.strftime("%-d.%-m"),
            "time": self.timestamp.strftime("%H:%M:%S"),
            "level": self.level,
            "category": self.category,
            "message": self.message,
        }
