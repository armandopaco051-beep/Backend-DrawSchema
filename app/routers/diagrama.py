from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.diagrama import (
    ClaseCreate,
    ClaseMove,
    ClaseUpdate,
    DiagramaCreate,
    DiagramaResponse,
    DiagramaUpdate,
    MensajeResponse,
    RelacionCreate,
    RelacionUpdate,
    RestaurarVersionRequest,
    VersionHistorialResponse,
)
from app.services.diagrama import (
    actualizar_diagrama,
    agregar_clase,
    agregar_relacion,
    crear_diagrama,
    editar_clase,
    editar_relacion,
    eliminar_clase,
    eliminar_diagrama,
    eliminar_relacion,
    listar_diagramas,
    listar_diagramas_por_proyecto,
    listar_versiones_diagrama,
    mover_clase,
    obtener_diagrama,
    restaurar_version_diagrama,
)
from app.security.auth_dependencies import get_current_user
from app.services.proyecto import usuario_tiene_permiso
from app.services.realtime_manager import realtime_manager


router = APIRouter(prefix="/diagramas", tags=["Diagramas"])


def obtener_nodo_por_id(diagrama, node_id: str | None):
    if not diagrama or not diagrama.contenido:
        return None
    nodes = diagrama.contenido.get("nodes", [])
    if node_id:
        for node in nodes:
            if node.get("id") == node_id:
                return node
    return nodes[-1] if nodes else None


def obtener_arista_por_id(diagrama, edge_id: str | None):
    if not diagrama or not diagrama.contenido:
        return None
    edges = diagrama.contenido.get("edges", [])
    if edge_id:
        for edge in edges:
            if edge.get("id") == edge_id:
                return edge
    return edges[-1] if edges else None



def verificar_permiso_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_codigo: str,
    permiso: str,
):
    if not usuario_tiene_permiso(db, proyecto_id, usuario_codigo, permiso):
        raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta accion")


def obtener_diagrama_con_permiso(
    db: Session,
    diagrama_id: int,
    usuario_codigo: str,
    permiso: str,
):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    verificar_permiso_proyecto(db, diagrama.id_proyecto, usuario_codigo, permiso)
    return diagrama


@router.post("/", response_model=DiagramaResponse)
def crear(
    datos: DiagramaCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_proyecto(db, datos.id_proyecto, usuario_actual.codigo, "crear_diagrama")
    diagrama, error = crear_diagrama(db, datos)

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return diagrama


@router.get("/", response_model=list[DiagramaResponse])
def listar(db: Session = Depends(get_db)):
    return listar_diagramas(db)


@router.get("/proyecto/{id_proyecto}", response_model=list[DiagramaResponse])
def listar_por_proyecto(
    id_proyecto: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_proyecto(db, id_proyecto, usuario_actual.codigo, "ver_diagrama")
    return listar_diagramas_por_proyecto(db, id_proyecto)


@router.get("/{diagrama_id}", response_model=DiagramaResponse)
def abrir(
    diagrama_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    return obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "ver_diagrama")


@router.get("/{diagrama_id}/versiones", response_model=list[VersionHistorialResponse])
def listar_versiones(
    diagrama_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "ver_diagrama")
    return listar_versiones_diagrama(db, diagrama_id)


@router.post("/{diagrama_id}/versiones/{version_id}/restaurar", response_model=DiagramaResponse)
def restaurar_version(
    diagrama_id: int,
    version_id: int,
    datos: RestaurarVersionRequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = restaurar_version_diagrama(
        db,
        diagrama_id,
        version_id,
        datos.autor_codigo or usuario_actual.codigo,
    )

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "VERSION_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Version no encontrada")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return diagrama


@router.put("/{diagrama_id}", response_model=DiagramaResponse)
async def guardar(
    diagrama_id: int,
    datos: DiagramaUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = actualizar_diagrama(db, diagrama_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error:
        raise HTTPException(status_code=400, detail=error)

    actor = datos.autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "DIAGRAM_SAVED",
                "diagrama_id": diagrama_id,
                "payload": {"contenido": diagrama.contenido, "version": diagrama.version},
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama



@router.delete("/{diagrama_id}", response_model=MensajeResponse)
def eliminar(
    diagrama_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "eliminar_diagrama")
    diagrama = eliminar_diagrama(db, diagrama_id)

    if diagrama is None:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    return {"mensaje": "Diagrama eliminado correctamente"}


@router.post("/{diagrama_id}/clases", response_model=DiagramaResponse)
async def crear_clase(
    diagrama_id: int,
    datos: ClaseCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = agregar_clase(db, diagrama_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_YA_EXISTE":
        raise HTTPException(status_code=400, detail="Ya existe una clase con ese id")

    if error:
        raise HTTPException(status_code=400, detail=error)

    nueva_clase = obtener_nodo_por_id(diagrama, datos.id)
    actor = datos.autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "CLASS_CREATED",
                "diagrama_id": diagrama_id,
                "payload": nueva_clase,
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama


@router.patch("/{diagrama_id}/clases/{clase_id}/mover", response_model=DiagramaResponse)
async def mover(
    diagrama_id: int,
    clase_id: str,
    datos: ClaseMove,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = mover_clase(db, diagrama_id, clase_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    if error:
        raise HTTPException(status_code=400, detail=error)

    actor = datos.autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "CLASS_MOVED",
                "diagrama_id": diagrama_id,
                "payload": {
                    "id": clase_id,
                    "class_id": clase_id,
                    "clase_id": clase_id,
                    "node_id": clase_id,
                    "position": {"x": datos.x, "y": datos.y},
                    "x": datos.x,
                    "y": datos.y,
                },
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama


@router.put("/{diagrama_id}/clases/{clase_id}", response_model=DiagramaResponse)
async def actualizar_clase(
    diagrama_id: int,
    clase_id: str,
    datos: ClaseUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = editar_clase(db, diagrama_id, clase_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    if error:
        raise HTTPException(status_code=400, detail=error)

    clase_actualizada = obtener_nodo_por_id(diagrama, clase_id)
    actor = datos.autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "CLASS_UPDATED",
                "diagrama_id": diagrama_id,
                "payload": clase_actualizada,
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama


@router.delete("/{diagrama_id}/clases/{clase_id}", response_model=DiagramaResponse)
async def borrar_clase(
    diagrama_id: int,
    clase_id: str,
    autor_codigo: str | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = eliminar_clase(db, diagrama_id, clase_id, autor_codigo)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "CLASE_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    if error:
        raise HTTPException(status_code=400, detail=error)

    actor = autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "CLASS_DELETED",
                "diagrama_id": diagrama_id,
                "payload": {"clase_id": clase_id},
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama


@router.post("/{diagrama_id}/relaciones", response_model=DiagramaResponse)
async def crear_relacion(
    diagrama_id: int,
    datos: RelacionCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = agregar_relacion(db, diagrama_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "RELACION_YA_EXISTE":
        raise HTTPException(status_code=400, detail="Ya existe una relacion con ese id")

    if error:
        raise HTTPException(status_code=400, detail=error)

    nueva_relacion = obtener_arista_por_id(diagrama, datos.id)
    actor = datos.autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "RELATION_CREATED",
                "diagrama_id": diagrama_id,
                "payload": nueva_relacion,
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama


@router.put("/{diagrama_id}/relaciones/{relacion_id}", response_model=DiagramaResponse)
async def actualizar_relacion(
    diagrama_id: int,
    relacion_id: str,
    datos: RelacionUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = editar_relacion(db, diagrama_id, relacion_id, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "RELACION_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Relacion no encontrada")

    if error:
        raise HTTPException(status_code=400, detail=error)

    relacion_actualizada = obtener_arista_por_id(diagrama, relacion_id)
    actor = datos.autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "RELATION_UPDATED",
                "diagrama_id": diagrama_id,
                "payload": relacion_actualizada,
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama


@router.delete("/{diagrama_id}/relaciones/{relacion_id}", response_model=DiagramaResponse)
async def borrar_relacion(
    diagrama_id: int,
    relacion_id: str,
    autor_codigo: str | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    obtener_diagrama_con_permiso(db, diagrama_id, usuario_actual.codigo, "editar_diagrama")
    diagrama, error = eliminar_relacion(db, diagrama_id, relacion_id, autor_codigo)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "RELACION_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Relacion no encontrada")

    if error:
        raise HTTPException(status_code=400, detail=error)

    actor = autor_codigo or usuario_actual.codigo or "Usuario"

    try:
        await realtime_manager.broadcast(
            diagrama_id,
            {
                "type": "RELATION_DELETED",
                "diagrama_id": diagrama_id,
                "payload": {"relacion_id": relacion_id},
                "actor": actor,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass

    return diagrama

