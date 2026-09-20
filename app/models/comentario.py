from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Comentario(Base):
    __tablename__ = "comentarios"
    __table_args__ = {"schema": "diagramas"}

    id = Column(Integer, primary_key=True, index=True)

    diagrama_id = Column(
        Integer,
        ForeignKey("diagramas.diagrama.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    autor_codigo = Column(
        String(150),
        ForeignKey("Usuario.usuarios.codigo", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nodo_id = Column(String(150), nullable=True, index=True)
    texto = Column(Text, nullable=False)
    resuelto = Column(Boolean, nullable=False, default=False)

    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    actualizado_en = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )

    diagrama = relationship("Diagrama", back_populates="comentarios")
    autor = relationship("Usuario", back_populates="comentarios")
