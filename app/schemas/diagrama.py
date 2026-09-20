from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DiagramaCreate(BaseModel):
    id_proyecto: int
    nombre: str
    contenido: dict[str, Any] | None = None


class DiagramaUpdate(BaseModel):
    nombre: str | None = None
    contenido: dict[str, Any] | None = None
    autor_codigo: str | None = None


class DiagramaResponse(BaseModel):
    id: int
    id_proyecto: int
    nombre: str
    contenido: dict[str, Any]
    version: int
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None

    class Config:
        from_attributes = True


class VersionAutorResponse(BaseModel):
    codigo: str
    nombres: str
    apellidos: str
    email: str

    class Config:
        from_attributes = True


class VersionHistorialResponse(BaseModel):
    id: int
    diagrama_id: int
    autor_id: str
    contenido: dict[str, Any]
    version: int
    fecha: datetime
    titulo: str | None = None
    descripcion: str | None = None
    tipo: str
    autor: VersionAutorResponse | None = None

    class Config:
        from_attributes = True


class RestaurarVersionRequest(BaseModel):
    autor_codigo: str | None = None


class ClaseCreate(BaseModel):
    id: str | None = None
    name: str
    x: float = 100
    y: float = 100
    attributes: list[dict[str, Any]] = Field(default_factory=list)
    methods: list[dict[str, Any]] = Field(default_factory=list)
    autor_codigo: str | None = None


class ClaseUpdate(BaseModel):
    name: str | None = None
    attributes: list[dict[str, Any]] | None = None
    methods: list[dict[str, Any]] | None = None
    autor_codigo: str | None = None


class ClaseMove(BaseModel):
    x: float
    y: float
    autor_codigo: str | None = None


class RelacionCreate(BaseModel):
    id: str | None = None
    source: str
    target: str
    type: str | None = None
    data: dict[str, Any]
    autor_codigo: str | None = None


class RelacionUpdate(BaseModel):
    source: str | None = None
    target: str | None = None
    type: str | None = None
    data: dict[str, Any] | None = None
    autor_codigo: str | None = None


class MensajeResponse(BaseModel):
    mensaje: str
