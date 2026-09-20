from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ComentarioCreate(BaseModel):
    nodo_id: str | None = None
    texto: str


class ComentarioUpdate(BaseModel):
    texto: str | None = None
    resuelto: bool | None = None


class ComentarioResolver(BaseModel):
    resuelto: bool = True


class ComentarioResponse(BaseModel):
    id: int
    diagrama_id: int
    autor_codigo: str
    autor_nombre: str | None = None
    nodo_id: str | None = None
    texto: str
    resuelto: bool
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)
