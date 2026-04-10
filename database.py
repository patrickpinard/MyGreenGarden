"""
MyGreenGarden V7.0 — Base de données SQLite via SQLAlchemy.
Remplace pickle (mesures.dta) et SQLite users séparés par une DB unifiée.
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from config import settings

# S'assurer que le dossier data/ existe
Path("data").mkdir(exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dépendance FastAPI — fournit une session DB par requête."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crée toutes les tables si elles n'existent pas encore."""
    # Import ici pour forcer la déclaration des modèles avant create_all
    from models import measurement, event, schedule, push_subscription, config_entry, user  # noqa
    Base.metadata.create_all(bind=engine)
