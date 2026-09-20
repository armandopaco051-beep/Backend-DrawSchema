from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Proyecto(Base):
    __tablename__ = "proyecto"
    __table_args__ = {"schema": "diagramas"}

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True)
    creado_en = Column(DateTime, server_default=func.now())
    codigo_invitacion = Column(String(64), unique=True, nullable=True, index=True)
    codigo_expira_en = Column(DateTime, nullable=True)


    miembros = relationship(
        "ProyectoUsuario",
        back_populates="proyecto",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    diagramas = relationship(
        "Diagrama",
        back_populates="proyecto",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
