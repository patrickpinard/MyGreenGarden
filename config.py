"""
MyGreenGarden V7.0 — Configuration
Tous les paramètres sensibles chargés depuis .env via pydantic-settings.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Application
    app_name: str = "MyGreenGarden"
    secret_key: str = "dev-secret-key-changez-en-production"
    debug: bool = False

    # Authentification PIN
    pin_hash: str = ""  # hash bcrypt du PIN — généré avec scripts/generate_pin.py

    # Base de données
    database_url: str = "sqlite:///./data/mygreengarden.db"

    # Email
    smtp_server: str = "smtpauths.bluewin.ch"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    email_sender: str = ""
    email_receiver: str = ""

    # Notifications push (VAPID)
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@example.com"

    # Hardware
    simulation_mode: bool = False  # True = mode simulation sans Pi

    # Session
    session_timeout_hours: int = 24

    # Affichage
    owner_name: str = "Patrick"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
