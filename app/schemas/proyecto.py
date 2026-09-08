from datetime import datetime

from pydantic import BaseModel


class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    usuario_codigo: str
    id_rol: int


class ProyectoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None


class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    creado_en: datetime | None = None

    class Config:
        from_attributes = True


class ProyectoUsuarioCreate(BaseModel):
    usuario_codigo: str
    id_proyecto: int | None = None
    id_rol: int


class ProyectoUsuarioResponse(BaseModel):
    usuario_codigo: str
    id_proyecto: int
    id_rol: int

    class Config:
        from_attributes = True
