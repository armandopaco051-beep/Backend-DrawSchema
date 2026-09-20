from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Diagrama(Base):
    __tablename__ = "diagrama"
    __table_args__ = {"schema": "diagramas"}

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    contenido = Column(JSONB, nullable=False, default=dict)
    version = Column(Integer, nullable=False, default=1)
    creado_en = Column(DateTime, server_default=func.now())
    actualizado_en = Column(DateTime, server_default=func.now(), onupdate=func.now())
    id_proyecto = Column(
        Integer,
        ForeignKey("diagramas.proyecto.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )

    proyecto = relationship("Proyecto", back_populates="diagramas")
    versiones = relationship(
        "VersionHistorial",
        back_populates="diagrama",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    comentarios = relationship(
        "Comentario",
        back_populates="diagrama",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

