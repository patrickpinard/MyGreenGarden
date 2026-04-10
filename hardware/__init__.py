"""
Couche hardware MyGreenGarden V7.0.
Fallback automatique en mode simulation si les modules Pi ne sont pas disponibles.
"""
import logging

from config import settings

logger = logging.getLogger(__name__)

SIMULATION = settings.simulation_mode

if not SIMULATION:
    # 1. Vérifier que smbus2 est installé
    try:
        import smbus2  # noqa
    except ImportError:
        SIMULATION = True
        logger.warning("smbus2 non installé — mode simulation activé automatiquement.")

if not SIMULATION:
    # 2. Vérifier que le bus I2C est réellement accessible
    try:
        import smbus2
        _bus = smbus2.SMBus(1)
        _bus.close()
        del _bus
        logger.info("Bus I2C disponible — mode hardware activé.")
    except Exception as e:
        SIMULATION = True
        logger.warning(
            f"Bus I2C inaccessible ({e}) — mode simulation activé automatiquement. "
            "Vérifiez que I2C est activé (raspi-config) et que le câblage est correct."
        )
