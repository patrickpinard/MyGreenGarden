#!/usr/bin/env python3
"""
Génère le hash bcrypt d'un code PIN.
Usage : python scripts/generate_pin.py
Coller le résultat dans .env → PIN_HASH="..."
"""
from passlib.hash import bcrypt
import getpass

pin = getpass.getpass("Entrez votre code PIN (4-6 chiffres) : ").strip()
if not pin.isdigit() or not 4 <= len(pin) <= 6:
    print("❌ Le PIN doit contenir 4 à 6 chiffres.")
    exit(1)

hashed = bcrypt.hash(pin)
print(f'\nAjoutez cette ligne dans votre fichier .env :\n')
print(f'PIN_HASH="{hashed}"')
