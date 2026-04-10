"""
MyGreenGarden V7.0 — Classes capteurs.
DS18B20 (température 1-wire), SoilWatch 10 (humidité sol ADC), QS-FS01 (anémomètre ADC).
"""
import glob
import logging
import random
from dataclasses import dataclass
from hardware import SIMULATION
from hardware.adc import ADC

logger = logging.getLogger(__name__)

# ADC partagé (singleton)
_adc: ADC | None = None

def get_adc() -> ADC:
    global _adc
    if _adc is None:
        _adc = ADC()
    return _adc


def _map_range(value: float, in_min: float, in_max: float,
               out_min: float, out_max: float) -> float:
    """Interpolation linéaire."""
    if in_max == in_min:
        return out_min
    return (value - in_min) / (in_max - in_min) * (out_max - out_min) + out_min


# ─── Textes d'état humidité sol ───────────────────────────────────────────────
MOISTURE_LABELS = [
    (0,   5,   "Sonde dans l'air"),
    (5,   30,  "Sol sec"),
    (30,  45,  "Sol humide"),
    (45,  70,  "Sol mouillé"),
    (70,  95,  "Sol trempé"),
    (95,  101, "Sonde dans l'eau"),
]

def moisture_label(pct: float) -> str:
    for lo, hi, label in MOISTURE_LABELS:
        if lo <= pct < hi:
            return label
    return "Inconnu"


# ─── DS18B20 Température ──────────────────────────────────────────────────────
@dataclass
class TemperatureReading:
    inside: float
    outside: float


class Temperatures:
    """
    Lecture des sondes DS18B20 via le bus 1-wire.
    Retourne intérieur [0] et extérieur [1].
    """

    def __init__(self):
        if not SIMULATION:
            self._sensors = self._discover()
            logger.info(f"DS18B20 : {len(self._sensors)} sonde(s) détectée(s)")
        else:
            self._sensors = []

    def _discover(self) -> list[str]:
        paths = glob.glob("/sys/bus/w1/devices/28*/w1_slave")
        return sorted(paths)

    def _read_sensor(self, path: str) -> float | None:
        try:
            with open(path) as f:
                lines = f.readlines()
            if "YES" not in lines[0]:
                return None
            temp_str = lines[1].split("t=")[-1].strip()
            return round(int(temp_str) / 1000.0, 2)
        except Exception as e:
            logger.error(f"Erreur lecture DS18B20 {path}: {e}")
            return None

    def read(self) -> TemperatureReading:
        if SIMULATION:
            return TemperatureReading(
                inside=round(random.uniform(22.0, 38.0), 1),
                outside=round(random.uniform(10.0, 28.0), 1),
            )
        temps = []
        for path in self._sensors[:2]:
            t = self._read_sensor(path)
            if t is not None:
                temps.append(t)
        inside  = temps[0] if len(temps) > 0 else 0.0
        outside = temps[1] if len(temps) > 1 else 0.0
        return TemperatureReading(inside=inside, outside=outside)


# ─── SoilWatch 10 — Humidité sol ─────────────────────────────────────────────
class MoistureSensor:
    """
    Sonde humidité sol SoilWatch 10 connectée via ADC.
    Conversion tension (mV) → pourcentage.
    """
    VOLTAGE_MIN = 0.0
    VOLTAGE_MAX = 3000.0

    def __init__(self, zone: int, adc_channel: int):
        self.zone = zone
        self.adc_channel = adc_channel

    def read(self) -> tuple[float, str]:
        """Retourne (pourcentage, label texte)."""
        if SIMULATION:
            pct = round(random.uniform(30.0, 90.0), 1)
            return pct, moisture_label(pct)
        voltage = get_adc().read_voltage(self.adc_channel)
        pct = round(_map_range(voltage, self.VOLTAGE_MIN, self.VOLTAGE_MAX, 0, 100), 1)
        pct = max(0.0, min(100.0, pct))
        return pct, moisture_label(pct)


# ─── QS-FS01 — Anémomètre ─────────────────────────────────────────────────────
class Anemometer:
    """
    Capteur vitesse du vent QS-FS01 via ADC.
    Plage : 0-32.4 m/s → 0-116.6 km/h.
    """

    def __init__(self, adc_channel: int):
        self.adc_channel = adc_channel

    def read(self) -> float:
        """Retourne la vitesse du vent en km/h."""
        if SIMULATION:
            return round(random.uniform(0.0, 25.0), 1)
        voltage_mv = get_adc().read_voltage(self.adc_channel)
        voltage_v  = voltage_mv / 1000.0
        # Formule constructeur : 0.4V = 0 m/s, 2.4V = 32.4 m/s
        speed_ms   = max(0.0, (voltage_v - 0.4) / 2.0 * 32.4)
        speed_kmh  = round(speed_ms * 3.6, 1)
        return speed_kmh
