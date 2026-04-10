"""
MyGreenGarden V7.0 — Driver module 8 relais Sequent (I2C).
Port direct depuis SequentLib8relay.py V6, refactorisé en classe.
"""
import logging
from hardware import SIMULATION

logger = logging.getLogger(__name__)

# Adresses I2C du module relais
RELAY_I2C_ADDRESS_PRIMARY = 0x38
RELAY_I2C_ADDRESS_ALT     = 0x20

# Remapping physique des relais (câblage du module Sequent)
RELAY_MASK_REMAP = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

# Registres I2C
REG_OUTPUT  = 0x02
REG_POLARITY = 0x04
REG_CONFIG  = 0x06


class RelayDriver:
    """
    Driver bas niveau pour le module 8 relais Sequent stackable.
    Supporte plusieurs modules empilés (stack 0-7).
    """
    _bus = None

    @classmethod
    def _get_bus(cls):
        if cls._bus is None and not SIMULATION:
            try:
                import smbus2
                cls._bus = smbus2.SMBus(1)
            except Exception as e:
                logger.error(f"Impossible d'ouvrir le bus I2C pour les relais : {e}")
                return None
        return cls._bus

    @classmethod
    def _get_address(cls, stack: int) -> int:
        return RELAY_I2C_ADDRESS_PRIMARY ^ (stack & 0x07)

    @classmethod
    def _init_module(cls, stack: int) -> None:
        if SIMULATION:
            return
        bus = cls._get_bus()
        addr = cls._get_address(stack)
        try:
            bus.write_byte_data(addr, REG_CONFIG, 0x00)   # tous en sortie
            bus.write_byte_data(addr, REG_POLARITY, 0x00)
        except Exception as e:
            logger.error(f"Erreur init module relais stack {stack}: {e}")

    @classmethod
    def set(cls, stack: int, relay: int, value: int) -> None:
        """
        Active ou désactive un relais.
        relay : 1-8
        value : 0 (OFF) ou 1 (ON)
        """
        if not 1 <= relay <= 8:
            raise ValueError(f"Numéro de relais invalide : {relay} (1-8)")
        if SIMULATION:
            logger.debug(f"[SIMUL] Relais {relay} stack {stack} → {'ON' if value else 'OFF'}")
            return
        bus = cls._get_bus()
        if bus is None:
            logger.error(f"Bus I2C indisponible — commande relais {relay} ignorée")
            return
        addr = cls._get_address(stack)
        try:
            current = bus.read_byte_data(addr, REG_OUTPUT)
            mask = RELAY_MASK_REMAP[relay - 1]
            new_val = (current | mask) if value else (current & ~mask)
            bus.write_byte_data(addr, REG_OUTPUT, new_val)
        except Exception as e:
            logger.error(f"Erreur set relais {relay}: {e}")

    @classmethod
    def get(cls, stack: int, relay: int) -> int:
        """Retourne l'état d'un relais (0 ou 1)."""
        if not 1 <= relay <= 8:
            raise ValueError(f"Numéro de relais invalide : {relay}")
        if SIMULATION:
            return 0
        bus = cls._get_bus()
        if bus is None:
            return 0
        addr = cls._get_address(stack)
        try:
            val = bus.read_byte_data(addr, REG_OUTPUT)
            return 1 if (val & RELAY_MASK_REMAP[relay - 1]) else 0
        except Exception as e:
            logger.error(f"Erreur get relais {relay}: {e}")
            return 0
