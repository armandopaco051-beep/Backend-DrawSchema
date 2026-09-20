from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.comentario import (
    ComentarioCreate,
    ComentarioResolver,
    ComentarioResponse,
    ComentarioUpdate,
)
from app.security.auth_dependencies import get_current_user
from app.services.comentario import (
    actualizar_comentario,
    crear_comentario,
    eliminar_comentario,
    listar_comentarios,
    obtener_comentario,
    resolver_comentario,
)
from app.services.diagrama import obtener_diagrama
from app.services.proyecto import usuario_tiene_permiso

router = APIRouter(tags=["Comentarios"])


def verificar_permiso_diagrama(
    db: Session,
    diagrama_id: int,
    usuario_codigo: str,
    permiso: str = "ver_diagrama",
):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if not usuario_tiene_permiso(db, diagrama.id_proyecto, usuario_codigo, permiso):
        raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta accion")

    return diagrama


@router.post("/diagramas/{diagrama_id}/comentarios", response_model=ComentarioResponse)
def crear(
    diagrama_id: int,
    datos: ComentarioCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_diagrama(db, diagrama_id, usuario_actual.codigo, "ver_diagrama")
    res, error = crear_comentario(db, diagrama_id, usuario_actual.codigo, datos)

    if error == "DIAGRAMA_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Diagrama no encontrado")

    if error == "TEXTO_VACIO":
        raise HTTPException(status_code=400, detail="El texto del comentario no puede estar vacio")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return res


@router.get("/diagramas/{diagrama_id}/comentarios", response_model=list[ComentarioResponse])
def listar(
    diagrama_id: int,
    solo_pendientes: bool = Query(default=False),
    nodo_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_diagrama(db, diagrama_id, usuario_actual.codigo, "ver_diagrama")
    return listar_comentarios(db, diagrama_id, solo_pendientes=solo_pendientes, nodo_id=nodo_id)


@router.patch("/comentarios/{comentario_id}/resolver", response_model=ComentarioResponse)
def resolver(
    comentario_id: int,
    datos: ComentarioResolver,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    comentario = obtener_comentario(db, comentario_id)

    if comentario is None:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")

    verificar_permiso_diagrama(db, comentario.diagrama_id, usuario_actual.codigo, "ver_diagrama")
    res, error = resolver_comentario(db, comentario_id, resuelto=datos.resuelto)

    if error:
        raise HTTPException(status_code=400, detail=error)

    return res


@router.put("/comentarios/{comentario_id}", response_model=ComentarioResponse)
def actualizar(
    comentario_id: int,
    datos: ComentarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    comentario = obtener_comentario(db, comentario_id)

    if comentario is None:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")

    verificar_permiso_diagrama(db, comentario.diagrama_id, usuario_actual.codigo, "ver_diagrama")
    res, error = actualizar_comentario(db, comentario_id, datos, usuario_actual.codigo)

    if error == "SIN_PERMISO_AUTOR":
        raise HTTPException(status_code=403, detail="Solo el autor puede editar este comentario")

    if error == "TEXTO_VACIO":
        raise HTTPException(status_code=400, detail="El texto del comentario no puede estar vacio")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return res


@router.delete("/comentarios/{comentario_id}", response_model=ComentarioResponse)
def borrar(
    comentario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    comentario = obtener_comentario(db, comentario_id)

    if comentario is None:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")

    diagrama = verificar_permiso_diagrama(db, comentario.diagrama_id, usuario_actual.codigo, "ver_diagrama")

    puede_administrar = usuario_tiene_permiso(
        db, diagrama.id_proyecto, usuario_actual.codigo, "gestionar_miembros"
    )

    res, error = eliminar_comentario(
        db, comentario_id, usuario_actual.codigo, puede_administrar=puede_administrar
    )

    if error == "SIN_PERMISO_ELIMINAR":
        raise HTTPException(
            status_code=403,
            detail="Solo el autor o administradores pueden eliminar este comentario",
        )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return res
