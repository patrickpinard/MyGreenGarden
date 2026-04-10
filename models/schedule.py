"""
Modèle SQLAlchemy — Planification des arrosages.
Nouveauté V7 : arrosages à heures fixes en plus du déclenchement par seuil.
"""
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class WateringSchedule(Base):
    __tablename__ = "watering_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Zone : 1 ou 2
    zone: Mapped[int] = mapped_column(Integer)

    # Libellé affiché dans l'interface
    label: Mapped[str] = mapped_column(String(100), default="")

    # Heure et minute du déclenchement (format 24h)
    hour: Mapped[int] = mapped_column(Integer)      # 0-23
    minute: Mapped[int] = mapped_column(Integer)    # 0-59

    # Durée en secondes
    duration: Mapped[int] = mapped_column(Integer, default=300)

    # Jours actifs : chaîne de 7 chars "1111111" = tous les jours
    # Index 0=lundi, 1=mardi, ..., 6=dimanche
    days: Mapped[str] = mapped_column(String(7), default="1111111")

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self) -> dict:
        day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        active_days = [day_names[i] for i, d in enumerate(self.days) if d == "1"]
        return {
            "id": self.id,
            "zone": self.zone,
            "label": self.label,
            "hour": self.hour,
            "minute": self.minute,
            "time_str": f"{self.hour:02d}:{self.minute:02d}",
            "duration": self.duration,
            "days": self.days,
            "active_days": active_days,
            "enabled": self.enabled,
        }
