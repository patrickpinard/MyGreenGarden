#!/usr/bin/env python3
"""
Génère une paire de clés VAPID pour les notifications push.
Usage : python scripts/generate_vapid.py
Coller les résultats dans .env.
"""
try:
    from py_vapid import Vapid
except ImportError:
    print("Installer py_vapid : pip install py-vapid")
    exit(1)

v = Vapid()
v.generate_keys()
private_key = v.private_key.private_bytes(
    encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.PEM,
    format=__import__('cryptography').hazmat.primitives.serialization.PrivateFormat.PKCS8,
    encryption_algorithm=__import__('cryptography').hazmat.primitives.serialization.NoEncryption(),
).decode()

public_key = v.public_key.public_bytes(
    encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.X962,
    format=__import__('cryptography').hazmat.primitives.serialization.PublicFormat.UncompressedPoint,
)
import base64
public_b64 = base64.urlsafe_b64encode(public_key).decode().rstrip('=')

print("Ajoutez ces lignes dans .env :\n")
print(f'VAPID_PUBLIC_KEY="{public_b64}"')
print(f'VAPID_PRIVATE_KEY="{private_key.strip()}"')
