"""
MyGreenGarden V7.0 — Classes actionneurs.
Lampe, ventilateurs, vannes d'eau, lucarne (prévu mais non installé).
"""
import logging
import time
from hardware import SIMULATION
from hardware.relay import RelayDriver

logger = logging.getLogger(__name__)

RELAY_STACK = 7   # jumpers tous à 1 → adresse 0x3F (0x38 ^ 7)

# Numéros de relais
RELAY_LIGHT  = 6
RELAY_FAN    = 7
RELAY_VALVE1 = 4
RELAY_VALVE2 = 5
RELAY_WIN_A  = 1  # Lucarne (non installée)
RELAY_WIN_B  = 2
RELAY_WIN_C  = 3

WINDOW_TRAVEL_TIME = 60  # secondes pour ouvrir/fermer complètement la lucarne


class Actuator:
    """Base pour tous les actionneurs à relais."""

    def __init__(self, relay_id: int, name: str, inverted: bool = False):
        self.relay_id = relay_id
        self.name = name
        self.inverted = inverted
        # État interne suivi en mémoire (évite les lectures I2C inutiles)
        self._state: bool = False
        if not SIMULATION:
            RelayDriver._init_module(RELAY_STACK)

    def _set(self, on: bool) -> None:
        raw = (not on) if self.inverted else on
        RelayDriver.set(RELAY_STACK, self.relay_id, int(raw))
        self._state = on
        logger.info(f"{self.name} → {'ON' if on else 'OFF'}")

    @property
    def state(self) -> bool:
        return self._state

    def on(self) -> None:
        self._set(True)

    def off(self) -> None:
        self._set(False)

    def toggle(self) -> bool:
        self._set(not self._state)
        return self._state


class Light(Actuator):
    """Lampe LED 24V — relais #6."""

    def __init__(self):
        super().__init__(RELAY_LIGHT, "Lampe LED")


class Fan(Actuator):
    """Ventilateurs 24V Sunon — relais #7."""

    def __init__(self):
        super().__init__(RELAY_FAN, "Ventilateurs")


class WaterValve(Actuator):
    """
    Vanne d'arrosage GARDENA 24V solénoïde.
    Logique inversée : relais fermé = vanne ouverte (normalement fermée).
    """

    def __init__(self, zone: int):
        relay_id = RELAY_VALVE1 if zone == 1 else RELAY_VALVE2
        super().__init__(relay_id, f"Vanne zone {zone}", inverted=True)
        self.zone = zone

    def open(self) -> None:
        self.on()
        logger.info(f"Vanne zone {self.zone} OUVERTE")

    def close(self) -> None:
        self.off()
        logger.info(f"Vanne zone {self.zone} FERMÉE")

    def water(self, duration_seconds: int) -> None:
        """Ouvre la vanne pendant duration_seconds puis ferme."""
        logger.info(f"Arrosage zone {self.zone} démarré ({duration_seconds}s)")
        self.open()
        time.sleep(duration_seconds)
        self.close()
        logger.info(f"Arrosage zone {self.zone} terminé")


class SkyLight:
    """
    Lucarne motorisée — vérin VEVOR 12V 500mm.
    Contrôle par inversion de polarité (3 relais).
    NOTE : non installée — code désactivé, prévu pour V7+.
    """
    INSTALLED = False  # passer à True quand le vérin est câblé

    def __init__(self):
        self._open = False
        if self.INSTALLED and not SIMULATION:
            RelayDriver._init_module(RELAY_STACK)
        logger.info("SkyLight : " + ("installée" if self.INSTALLED else "non installée (désactivée)"))

    @property
    def state(self) -> bool:
        return self._open

    def open(self) -> None:
        if not self.INSTALLED:
            logger.warning("SkyLight.open() ignoré — lucarne non installée")
            return
        logger.info("Lucarne → OUVERTURE")
        RelayDriver.set(RELAY_STACK, RELAY_WIN_C, 0)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_A, 1)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_B, 1)
        time.sleep(WINDOW_TRAVEL_TIME)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_A, 0)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_B, 0)
        self._open = True

    def close(self) -> None:
        if not self.INSTALLED:
            logger.warning("SkyLight.close() ignoré — lucarne non installée")
            return
        logger.info("Lucarne → FERMETURE")
        RelayDriver.set(RELAY_STACK, RELAY_WIN_A, 0)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_B, 0)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_C, 1)
        time.sleep(WINDOW_TRAVEL_TIME)
        RelayDriver.set(RELAY_STACK, RELAY_WIN_C, 0)
        self._open = False
