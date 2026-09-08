from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class VersionHistorial(Base):
    __tablename__ = "version_historial"
    __table_args__ = {"schema": "diagramas"}

    id = Column(Integer, primary_key=True, index=True)

    diagrama_id = Column(
        Integer,
        ForeignKey("diagramas.diagrama.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )

    autor_id = Column(
        String(150),
        ForeignKey("Usuario.usuarios.codigo", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )

    contenido = Column(JSONB, nullable=False)
    version = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())

    diagrama = relationship("Diagrama", back_populates="versiones")
    autor = relationship("Usuario", back_populates="versiones")
