"""
Modèle SQLAlchemy — Mesures des capteurs.
Remplace les listes Python + pickle de V6.
Historique illimité avec requêtes par période.
"""
from datetime import datetime
from sqlalchemy import Float, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Capteurs température
    temp_inside: Mapped[float] = mapped_column(Float, default=0.0)
    temp_outside: Mapped[float] = mapped_column(Float, default=0.0)

    # Capteurs humidité sol
    moisture_zone1: Mapped[float] = mapped_column(Float, default=0.0)
    moisture_zone2: Mapped[float] = mapped_column(Float, default=0.0)

    # Vitesse du vent
    wind_speed: Mapped[float] = mapped_column(Float, default=0.0)

    # Système
    cpu_temp: Mapped[float] = mapped_column(Float, default=0.0)
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0)

    # États actionneurs au moment de la mesure
    fan_on: Mapped[bool] = mapped_column(Boolean, default=False)
    light_on: Mapped[bool] = mapped_column(Boolean, default=False)
    window_open: Mapped[bool] = mapped_column(Boolean, default=False)
    valve1_open: Mapped[bool] = mapped_column(Boolean, default=False)
    valve2_open: Mapped[bool] = mapped_column(Boolean, default=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "temp_inside": self.temp_inside,
            "temp_outside": self.temp_outside,
            "moisture_zone1": self.moisture_zone1,
            "moisture_zone2": self.moisture_zone2,
            "wind_speed": self.wind_speed,
            "cpu_temp": self.cpu_temp,
            "cpu_usage": self.cpu_usage,
            "fan_on": self.fan_on,
            "light_on": self.light_on,
            "window_open": self.window_open,
            "valve1_open": self.valve1_open,
            "valve2_open": self.valve2_open,
        }
