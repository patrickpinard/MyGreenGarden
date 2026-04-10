"""
MyGreenGarden V7.0 — Driver ADC 12 bits Grove Hat (I2C).
Utilisé pour : humidité sol (ch0, ch1), anémomètre (ch4).
"""
import logging
import random
from hardware import SIMULATION

logger = logging.getLogger(__name__)

ADC_ADDRESS = 0x08
ADC_MAX     = 4095   # 12 bits
ADC_VCC_MV  = 3300   # tension de référence en mV


class ADC:
    """
    Driver pour le convertisseur analogique-numérique Grove 12 bits.
    Canaux 0-7 disponibles.
    """

    def __init__(self, address: int = ADC_ADDRESS):
        self.address = address
        self._bus = None
        if not SIMULATION:
            try:
                import smbus2
                self._bus = smbus2.SMBus(1)
                logger.info(f"ADC initialisé (I2C addr 0x{address:02X})")
            except Exception as e:
                logger.error(f"Erreur init ADC: {e}")

    def read_raw(self, channel: int) -> int:
        """Lecture brute 12 bits (0-4095)."""
        if not 0 <= channel <= 7:
            raise ValueError(f"Canal ADC invalide : {channel}")
        if SIMULATION:
            return random.randint(800, 3000)
        try:
            data = self._bus.read_i2c_block_data(self.address, channel, 2)
            return ((data[0] & 0x0F) << 8) | data[1]
        except Exception as e:
            logger.error(f"Erreur lecture ADC ch{channel}: {e}")
            return 0

    def read_voltage(self, channel: int) -> float:
        """Tension en mV (0-3300 mV)."""
        raw = self.read_raw(channel)
        return (raw / ADC_MAX) * ADC_VCC_MV

    def read_ratio(self, channel: int) -> float:
        """Ratio en % (0-100)."""
        raw = self.read_raw(channel)
        return (raw / ADC_MAX) * 100.0
