"""
MyGreenGarden V7.0 — État global de la serre.
Singleton partagé entre les services et les routes FastAPI.
Remplace les variables globales de app.py V6.
"""
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class GardenState:
    """État courant de tous les capteurs et actionneurs."""

    # ── Capteurs ──────────────────────────────────────────────────────────────
    temp_inside:   float = 0.0
    temp_outside:  float = 0.0
    moisture_zone1: float = 0.0
    moisture_zone2: float = 0.0
    moisture_zone1_label: str = ""
    moisture_zone2_label: str = ""
    wind_speed:    float = 0.0
    cpu_temp:      float = 0.0
    cpu_usage:     float = 0.0

    # ── Actionneurs (états logiques) ──────────────────────────────────────────
    fan_on:        bool = False
    light_on:      bool = False
    window_open:   bool = False
    valve1_open:   bool = False
    valve2_open:   bool = False

    # ── Modes auto/manuel ─────────────────────────────────────────────────────
    fan_auto:        bool = True
    window_auto:     bool = True
    watering_auto_z1: bool = True
    watering_auto_z2: bool = True

    # ── Compteurs arrosages consécutifs (détection panne capteur) ─────────────
    watering_count_z1: int = 0
    watering_count_z2: int = 0

    # ── Alertes actives ───────────────────────────────────────────────────────
    alerts: list = field(default_factory=list)   # liste de dicts {level, message}

    # ── Méta ──────────────────────────────────────────────────────────────────
    last_update: datetime | None = None
    startup_time: datetime = field(default_factory=datetime.now)

    # Thread-safety
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def update_sensors(self, **kwargs) -> None:
        with self._lock:
            for k, v in kwargs.items():
                if hasattr(self, k):
                    setattr(self, k, v)
            self.last_update = datetime.now()

    def add_alert(self, level: str, message: str) -> None:
        with self._lock:
            self.alerts.append({"level": level, "message": message, "time": datetime.now().isoformat()})
            # Garder max 10 alertes actives
            self.alerts = self.alerts[-10:]

    def clear_alerts(self) -> None:
        with self._lock:
            self.alerts = []

    def to_dict(self) -> dict:
        return {
            "sensors": {
                "temp_inside":           self.temp_inside,
                "temp_outside":          self.temp_outside,
                "moisture_zone1":        self.moisture_zone1,
                "moisture_zone2":        self.moisture_zone2,
                "moisture_zone1_label":  self.moisture_zone1_label,
                "moisture_zone2_label":  self.moisture_zone2_label,
                "wind_speed":            self.wind_speed,
                "cpu_temp":              self.cpu_temp,
                "cpu_usage":             self.cpu_usage,
            },
            "actuators": {
                "fan_on":      self.fan_on,
                "light_on":    self.light_on,
                "window_open": self.window_open,
                "valve1_open": self.valve1_open,
                "valve2_open": self.valve2_open,
            },
            "modes": {
                "fan_auto":          self.fan_auto,
                "window_auto":       self.window_auto,
                "watering_auto_z1":  self.watering_auto_z1,
                "watering_auto_z2":  self.watering_auto_z2,
            },
            "alerts": self.alerts,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }


# Instance singleton partagée dans toute l'application
garden_state = GardenState()
