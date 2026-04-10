"""
MyGreenGarden V7.0 — Diagnostic hardware.
Teste chaque composant et retourne un rapport de statut.
"""
import glob
import logging

logger = logging.getLogger(__name__)

# Adresses I2C attendues
I2C_RELAY_ADDR = 0x3F   # Module 8 relais Sequent (jumpers tous à 1, stack 7)
I2C_ADC_ADDR   = 0x08   # ADC Grove Hat 12 bits


def _status(ok: bool, detail: str = "") -> dict:
    return {"ok": ok, "detail": detail}


def probe_i2c_bus() -> dict:
    """Vérifie que le bus I2C est ouvert et lisible."""
    try:
        import smbus2
        bus = smbus2.SMBus(1)
        bus.close()
        return _status(True, "Bus I2C /dev/i2c-1 accessible")
    except ImportError:
        return _status(False, "smbus2 non installé (pip install smbus2)")
    except FileNotFoundError:
        return _status(False, "/dev/i2c-1 introuvable — I2C désactivé ? (raspi-config)")
    except PermissionError:
        return _status(False, "Permission refusée sur /dev/i2c-1 — ajoutez pi au groupe i2c")
    except Exception as e:
        return _status(False, str(e))


def probe_i2c_device(address: int, label: str) -> dict:
    """Tente une lecture sur un périphérique I2C à l'adresse donnée."""
    try:
        import smbus2
        bus = smbus2.SMBus(1)
        bus.read_byte(address)
        bus.close()
        return _status(True, f"{label} détecté à 0x{address:02X}")
    except ImportError:
        return _status(False, "smbus2 non installé")
    except Exception as e:
        return _status(False, f"{label} non détecté à 0x{address:02X} ({e})")


def probe_ds18b20() -> dict:
    """Vérifie la présence de sondes DS18B20 sur le bus 1-wire."""
    paths = glob.glob("/sys/bus/w1/devices/28*/w1_slave")
    if not paths:
        return _status(False, "Aucune sonde DS18B20 détectée sur le bus 1-wire")
    # Lecture rapide de la première sonde
    try:
        with open(paths[0]) as f:
            data = f.read()
        if "YES" in data:
            temp_str = data.split("t=")[-1].strip()
            temp = round(int(temp_str) / 1000.0, 1)
            return _status(True, f"{len(paths)} sonde(s) détectée(s) — lecture : {temp}°C")
        else:
            return _status(False, f"Sonde trouvée mais lecture invalide (CRC échoué)")
    except Exception as e:
        return _status(False, f"Erreur lecture DS18B20 : {e}")


def probe_w1_bus() -> dict:
    """Vérifie que le bus 1-wire est chargé."""
    import os
    if os.path.isdir("/sys/bus/w1/devices"):
        devices = glob.glob("/sys/bus/w1/devices/28*")
        if devices:
            return _status(True, f"Bus 1-wire actif — {len(devices)} device(s)")
        return _status(False, "Bus 1-wire actif mais aucun device DS18B20 connecté")
    return _status(False, "Bus 1-wire inactif — ajoutez 'dtoverlay=w1-gpio' dans /boot/config.txt")


def run_full_probe(simulation: bool = False) -> dict:
    """
    Lance tous les tests hardware.
    Retourne un dict avec le statut de chaque composant.
    """
    if simulation:
        return {
            "simulation": True,
            "i2c_bus":    _status(None, "Mode simulation — test ignoré"),
            "relay":      _status(None, "Mode simulation — test ignoré"),
            "adc":        _status(None, "Mode simulation — test ignoré"),
            "w1_bus":     _status(None, "Mode simulation — test ignoré"),
            "ds18b20":    _status(None, "Mode simulation — test ignoré"),
        }

    results = {"simulation": False}
    results["i2c_bus"] = probe_i2c_bus()

    if results["i2c_bus"]["ok"]:
        results["relay"]  = probe_i2c_device(I2C_RELAY_ADDR, "Module relais Sequent")
        results["adc"]    = probe_i2c_device(I2C_ADC_ADDR,   "ADC Grove Hat")
    else:
        results["relay"] = _status(False, "Bus I2C indisponible")
        results["adc"]   = _status(False, "Bus I2C indisponible")

    results["w1_bus"]  = probe_w1_bus()
    results["ds18b20"] = probe_ds18b20()

    all_ok = all(v["ok"] for v in results.values() if isinstance(v, dict) and v.get("ok") is not None)
    results["overall_ok"] = all_ok

    logger.info(f"Diagnostic hardware : {'OK' if all_ok else 'ERREURS DÉTECTÉES'}")
    for key, val in results.items():
        if isinstance(val, dict):
            status = "✓" if val.get("ok") else ("?" if val.get("ok") is None else "✗")
            logger.info(f"  [{status}] {key}: {val.get('detail', '')}")

    return results
