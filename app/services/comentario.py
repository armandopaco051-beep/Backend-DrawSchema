from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.comentario import Comentario
from app.models.diagrama import Diagrama
from app.models.usuario import Usuario
from app.schemas.comentario import ComentarioCreate, ComentarioResponse, ComentarioUpdate


def formatear_comentario_response(comentario: Comentario) -> dict:
    autor_nombre = None
    if comentario.autor:
        nombres = comentario.autor.nombres or ""
        apellidos = comentario.autor.apellidos or ""
        autor_nombre = " ".join([nombres, apellidos]).strip() or comentario.autor.email

    return {
        "id": comentario.id,
        "diagrama_id": comentario.diagrama_id,
        "autor_codigo": comentario.autor_codigo,
        "autor_nombre": autor_nombre,
        "nodo_id": comentario.nodo_id,
        "texto": comentario.texto,
        "resuelto": comentario.resuelto,
        "creado_en": comentario.creado_en,
        "actualizado_en": comentario.actualizado_en,
    }


def crear_comentario(
    db: Session,
    diagrama_id: int,
    autor_codigo: str,
    datos: ComentarioCreate,
):
    diagrama = db.query(Diagrama).filter(Diagrama.id == diagrama_id).first()

    if diagrama is None:
        return None, "DIAGRAMA_NO_EXISTE"

    if not datos.texto or not datos.texto.strip():
        return None, "TEXTO_VACIO"

    comentario = Comentario(
        diagrama_id=diagrama_id,
        autor_codigo=autor_codigo,
        nodo_id=datos.nodo_id.strip() if datos.nodo_id else None,
        texto=datos.texto.strip(),
        resuelto=False,
    )

    db.add(comentario)
    db.commit()
    db.refresh(comentario)

    # Cargar autor para obtener autor_nombre
    comentario = (
        db.query(Comentario)
        .options(joinedload(Comentario.autor))
        .filter(Comentario.id == comentario.id)
        .first()
    )

    return formatear_comentario_response(comentario), None


def listar_comentarios(
    db: Session,
    diagrama_id: int,
    solo_pendientes: bool = False,
    nodo_id: str | None = None,
):
    query = (
        db.query(Comentario)
        .options(joinedload(Comentario.autor))
        .filter(Comentario.diagrama_id == diagrama_id)
    )

    if solo_pendientes:
        query = query.filter(Comentario.resuelto == False)

    if nodo_id:
        query = query.filter(Comentario.nodo_id == nodo_id)

    comentarios = query.order_by(Comentario.creado_en.asc()).all()
    return [formatear_comentario_response(c) for c in comentarios]


def obtener_comentario(db: Session, comentario_id: int):
    return (
        db.query(Comentario)
        .options(joinedload(Comentario.autor))
        .filter(Comentario.id == comentario_id)
        .first()
    )


def actualizar_comentario(
    db: Session,
    comentario_id: int,
    datos: ComentarioUpdate,
    usuario_codigo: str,
):
    comentario = obtener_comentario(db, comentario_id)

    if comentario is None:
        return None, "COMENTARIO_NO_EXISTE"

    if comentario.autor_codigo != usuario_codigo:
        return None, "SIN_PERMISO_AUTOR"

    if datos.texto is not None:
        if not datos.texto.strip():
            return None, "TEXTO_VACIO"
        comentario.texto = datos.texto.strip()

    if datos.resuelto is not None:
        comentario.resuelto = datos.resuelto

    comentario.actualizado_en = datetime.utcnow()
    db.commit()
    db.refresh(comentario)

    return formatear_comentario_response(comentario), None


def resolver_comentario(
    db: Session,
    comentario_id: int,
    resuelto: bool,
):
    comentario = obtener_comentario(db, comentario_id)

    if comentario is None:
        return None, "COMENTARIO_NO_EXISTE"

    comentario.resuelto = resuelto
    comentario.actualizado_en = datetime.utcnow()
    db.commit()
    db.refresh(comentario)

    return formatear_comentario_response(comentario), None


def eliminar_comentario(
    db: Session,
    comentario_id: int,
    usuario_codigo: str,
    puede_administrar: bool = False,
):
    comentario = obtener_comentario(db, comentario_id)

    if comentario is None:
        return None, "COMENTARIO_NO_EXISTE"

    # Permiso: El autor o administradores/propietarios del proyecto pueden eliminar el comentario
    if comentario.autor_codigo != usuario_codigo and not puede_administrar:
        return None, "SIN_PERMISO_ELIMINAR"

    response_data = formatear_comentario_response(comentario)
    db.delete(comentario)
    db.commit()

    return response_data, None
