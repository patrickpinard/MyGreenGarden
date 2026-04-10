"""
Modèle SQLAlchemy — Paramètres de configuration.
Remplace config.json de V6. Chaque paramètre est une ligne clé/valeur/type.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

# Valeurs par défaut — chargées à l'init si la table est vide
DEFAULT_CONFIG = {
    # Seuils température (mode jour)
    "TEMP_MAX_THRESHOLD":           ("35.0",  "float",  "Température max serre (°C) → ventilation ON"),
    "TEMP_MIN_THRESHOLD":           ("30.0",  "float",  "Température min serre (°C) → ventilation OFF"),
    # Seuils humidité sol
    "MOISTURE_THRESHOLD_ZONE_1":    ("65.0",  "float",  "Humidité sol zone 1 — seuil arrosage (%)"),
    "MOISTURE_THRESHOLD_ZONE_2":    ("65.0",  "float",  "Humidité sol zone 2 — seuil arrosage (%)"),
    # Durées arrosage
    "WATERING_TIME_ZONE_1":         ("300",   "int",    "Durée arrosage zone 1 (secondes)"),
    "WATERING_TIME_ZONE_2":         ("300",   "int",    "Durée arrosage zone 2 (secondes)"),
    # Vent
    "WINDSPEED_LIMIT":              ("40.0",  "float",  "Vitesse vent limite → alerte (km/h)"),
    # Humidité air
    "HUMIDITY_LIMIT":               ("80.0",  "float",  "Humidité air max (%)"),
    # Intervalle automation
    "AUTOMATION_INTERVAL":          ("900",   "int",    "Intervalle entre cycles automation (secondes)"),
    # Mode nuit
    "NIGHT_MODE_ENABLED":           ("false", "bool",   "Mode nuit activé"),
    "NIGHT_START":                  ("22:00", "str",    "Début mode nuit (HH:MM)"),
    "NIGHT_END":                    ("07:00", "str",    "Fin mode nuit (HH:MM)"),
    "NIGHT_TEMP_MAX":               ("25.0",  "float",  "Température max nuit (°C)"),
    "NIGHT_TEMP_MIN":               ("18.0",  "float",  "Température min nuit (°C)"),
    "NIGHT_MOISTURE_ZONE_1":        ("55.0",  "float",  "Humidité sol zone 1 nuit (%)"),
    "NIGHT_MOISTURE_ZONE_2":        ("55.0",  "float",  "Humidité sol zone 2 nuit (%)"),
}


class ConfigEntry(Base):
    __tablename__ = "config"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(10), default="str")   # str, int, float, bool
    description: Mapped[str] = mapped_column(String(200), default="")

    def typed_value(self):
        """Retourne la valeur dans le bon type Python."""
        if self.type == "int":
            return int(self.value)
        if self.type == "float":
            return float(self.value)
        if self.type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        return self.value
