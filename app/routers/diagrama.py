from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.diagrama import (
    ClaseCreate,
    ClaseMove,
    ClaseUpdate,
    DiagramaCreate,
    DiagramaResponse,
    DiagramaUpdate,
    MensajeResponse,
)
from app.services.diagrama import (
    actualizar_diagrama,
    agregar_clase,
    crear_diagrama,
    editar_clase,
    eliminar_clase,
    eliminar_diagrama,
    listar_diagramas,
    listar_diagramas_por_proyecto,
    mover_clase,
    obtener_diagrama,
)


router = APIRouter(prefix="/diagramas", tags=["Diagramas"])


@router.post("/", response_model=DiagramaResponse)
def crear(datos: DiagramaCreate, db: Session = Depends(get_db)):
    diagrama, error = crear_diagrama(db, datos)

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    return diagrama


@router.get("/", response_model=list[DiagramaResponse])
def listar(db: Session = Depends(get_db)):
    return listar_diagramas(db)


@router.get("/proyecto/{id_proyecto}", response_model=list[DiagramaResponse])
def listar_por_proyecto(id_proyecto: int, db: Session = Depends(get_db)):
    return listar_diagramas_por_proyecto(db, id_proyecto)


@router.get("/{diagrama_id}", response_model=DiagramaResponse)
def abrir(diagrama_id: int, db: Session = Depends(get_db)):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    return diagrama


@router.put("/{diagrama_id}", response_model=DiagramaResponse)
def guardar(diagrama_id: int, datos: DiagramaUpdate, db: Session = Depends(get_db)):
    diagrama = actualizar_diagrama(db, diagrama_id, datos)

    if diagrama is None:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    return diagrama


@router.delete("/{diagrama_id}", response_model=MensajeResponse)
def eliminar(diagrama_id: int, db: Session = Depends(get_db)):
    diagrama = eliminar_diagrama(db, diagrama_id)

    if diagrama is None:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    return {"mensaje": "Diagrama eliminado correctamente"}


@router.post("/{diagrama_id}/clases", response_model=DiagramaResponse)
def crear_clase(diagrama_id: int, datos: ClaseCreate, db: Session = Depends(get_db)):
    diagrama, error = agregar_clase(db, diagrama_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_YA_EXISTE":
        raise HTTPException(status_code=400, detail="Ya existe una clase con ese id")

    return diagrama


@router.patch("/{diagrama_id}/clases/{clase_id}/mover", response_model=DiagramaResponse)
def mover(
    diagrama_id: int,
    clase_id: str,
    datos: ClaseMove,
    db: Session = Depends(get_db),
):
    diagrama, error = mover_clase(db, diagrama_id, clase_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    return diagrama


@router.put("/{diagrama_id}/clases/{clase_id}", response_model=DiagramaResponse)
def actualizar_clase(
    diagrama_id: int,
    clase_id: str,
    datos: ClaseUpdate,
    db: Session = Depends(get_db),
):
    diagrama, error = editar_clase(db, diagrama_id, clase_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    return diagrama


@router.delete("/{diagrama_id}/clases/{clase_id}", response_model=DiagramaResponse)
def borrar_clase(
    diagrama_id: int,
    clase_id: str,
    autor_codigo: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    diagrama, error = eliminar_clase(db, diagrama_id, clase_id, autor_codigo)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    return diagrama
