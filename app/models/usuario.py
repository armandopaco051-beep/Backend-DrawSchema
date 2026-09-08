from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Rol(Base):
    __tablename__ = "rol"
    __table_args__ = {"schema": "Usuario"}

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)

    usuarios = relationship("Usuario", back_populates="rol")
    proyectos_usuario = relationship("ProyectoUsuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "Usuario"}

    codigo = Column(String(150), primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(Text, nullable=False)
    pais = Column(String(100), nullable=False)
    id_rol = Column(
        Integer,
        ForeignKey("Usuario.rol.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )

    rol = relationship("Rol", back_populates="usuarios")
    proyectos = relationship(
        "ProyectoUsuario",
        back_populates="usuario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    versiones = relationship(
        "VersionHistorial",
        back_populates="autor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
