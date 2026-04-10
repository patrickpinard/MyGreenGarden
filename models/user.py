"""
MyGreenGarden V7.0 — Modèle utilisateur.
Gestion multi-utilisateurs avec rôles admin/user et PIN haché.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(50), unique=True, nullable=False)
    pin_hash   = Column(String(255), nullable=False)
    role       = Column(String(10), default="user")   # "admin" ou "user"
    enabled    = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "username":   self.username,
            "role":       self.role,
            "enabled":    self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
