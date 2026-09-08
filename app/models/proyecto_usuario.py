from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ProyectoUsuario(Base):
    __tablename__ = "proyecto_usuario"
    __table_args__ = {"schema": "diagramas"}

    usuario_codigo = Column(
        String(150),
        ForeignKey("Usuario.usuarios.codigo", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    id_proyecto = Column(
        Integer,
        ForeignKey("diagramas.proyecto.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    id_rol = Column(
        Integer,
        ForeignKey("Usuario.rol.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    usuario = relationship("Usuario", back_populates="proyectos")
    proyecto = relationship("Proyecto", back_populates="miembros")
    rol = relationship("Rol", back_populates="proyectos_usuario")
