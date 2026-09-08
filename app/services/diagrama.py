from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import Session

from app.models.diagrama import Diagrama
from app.models.proyecto import Proyecto
from app.models.usuario import Usuario
from app.models.version_historial import VersionHistorial
from app.schemas.diagrama import ClaseCreate, ClaseMove, ClaseUpdate, DiagramaCreate, DiagramaUpdate


def contenido_inicial():
    return {
        "nodes": [],
        "edges": [],
    }


def guardar_version(db: Session, diagrama: Diagrama, autor_codigo: str | None):
    if autor_codigo is None:
        return

    autor = db.query(Usuario).filter(Usuario.codigo == autor_codigo).first()

    if autor is None:
        return

    version = VersionHistorial(
        diagrama_id=diagrama.id,
        autor_id=autor_codigo,
        contenido=deepcopy(diagrama.contenido),
        version=diagrama.version,
    )

    db.add(version)


def normalizar_contenido(contenido: dict | None):
    if not contenido:
        return contenido_inicial()

    nuevo_contenido = deepcopy(contenido)
    nuevo_contenido.setdefault("nodes", [])
    nuevo_contenido.setdefault("edges", [])
    return nuevo_contenido


def crear_diagrama(db: Session, datos: DiagramaCreate):
    proyecto = db.query(Proyecto).filter(Proyecto.id == datos.id_proyecto).first()

    if proyecto is None:
        return None, "PROYECTO_NO_EXISTE"

    diagrama = Diagrama(
        id_proyecto=datos.id_proyecto,
        nombre=datos.nombre,
        contenido=normalizar_contenido(datos.contenido),
        version=1,
    )

    db.add(diagrama)
    db.commit()
    db.refresh(diagrama)

    return diagrama, None


def listar_diagramas(db: Session):
    return db.query(Diagrama).order_by(Diagrama.id.desc()).all()


def listar_diagramas_por_proyecto(db: Session, id_proyecto: int):
    return (
        db.query(Diagrama)
        .filter(Diagrama.id_proyecto == id_proyecto)
        .order_by(Diagrama.id.desc())
        .all()
    )


def obtener_diagrama(db: Session, diagrama_id: int):
    return db.query(Diagrama).filter(Diagrama.id == diagrama_id).first()


def actualizar_diagrama(db: Session, diagrama_id: int, datos: DiagramaUpdate):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        return None

    guardar_version(db, diagrama, datos.autor_codigo)

    if datos.nombre is not None:
        diagrama.nombre = datos.nombre

    if datos.contenido is not None:
        diagrama.contenido = normalizar_contenido(datos.contenido)
        flag_modified(diagrama, "contenido")

    diagrama.version += 1
    diagrama.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(diagrama)

    return diagrama


def eliminar_diagrama(db: Session, diagrama_id: int):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        return None

    db.delete(diagrama)
    db.commit()

    return diagrama


def buscar_indice_clase(contenido: dict, clase_id: str):
    for index, node in enumerate(contenido.get("nodes", [])):
        if node.get("id") == clase_id:
            return index

    return None


def agregar_clase(db: Session, diagrama_id: int, datos: ClaseCreate):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        return None, "DIAGRAMA_NO_EXISTE"

    contenido = normalizar_contenido(diagrama.contenido)
    clase_id = datos.id or f"class-{uuid4().hex[:8]}"

    if buscar_indice_clase(contenido, clase_id) is not None:
        return None, "CLASE_YA_EXISTE"

    guardar_version(db, diagrama, datos.autor_codigo)

    nueva_clase = {
        "id": clase_id,
        "type": "classNode",
        "position": {
            "x": datos.x,
            "y": datos.y,
        },
        "data": {
            "name": datos.name,
            "attributes": datos.attributes,
            "methods": datos.methods,
        },
    }

    contenido["nodes"].append(nueva_clase)
    diagrama.contenido = contenido
    flag_modified(diagrama, "contenido")
    diagrama.version += 1
    diagrama.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(diagrama)

    return diagrama, None


def mover_clase(db: Session, diagrama_id: int, clase_id: str, datos: ClaseMove):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        return None, "DIAGRAMA_NO_EXISTE"

    contenido = normalizar_contenido(diagrama.contenido)
    index = buscar_indice_clase(contenido, clase_id)

    if index is None:
        return None, "CLASE_NO_EXISTE"

    guardar_version(db, diagrama, datos.autor_codigo)

    contenido["nodes"][index]["position"] = {
        "x": datos.x,
        "y": datos.y,
    }

    diagrama.contenido = contenido
    flag_modified(diagrama, "contenido")
    diagrama.version += 1
    diagrama.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(diagrama)

    return diagrama, None


def editar_clase(db: Session, diagrama_id: int, clase_id: str, datos: ClaseUpdate):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        return None, "DIAGRAMA_NO_EXISTE"

    contenido = normalizar_contenido(diagrama.contenido)
    index = buscar_indice_clase(contenido, clase_id)

    if index is None:
        return None, "CLASE_NO_EXISTE"

    guardar_version(db, diagrama, datos.autor_codigo)

    data = contenido["nodes"][index].setdefault("data", {})

    if datos.name is not None:
        data["name"] = datos.name

    if datos.attributes is not None:
        data["attributes"] = datos.attributes

    if datos.methods is not None:
        data["methods"] = datos.methods

    diagrama.contenido = contenido
    flag_modified(diagrama, "contenido")
    diagrama.version += 1
    diagrama.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(diagrama)

    return diagrama, None


def eliminar_clase(db: Session, diagrama_id: int, clase_id: str, autor_codigo: str | None = None):
    diagrama = obtener_diagrama(db, diagrama_id)

    if diagrama is None:
        return None, "DIAGRAMA_NO_EXISTE"

    contenido = normalizar_contenido(diagrama.contenido)
    index = buscar_indice_clase(contenido, clase_id)

    if index is None:
        return None, "CLASE_NO_EXISTE"

    guardar_version(db, diagrama, autor_codigo)

    contenido["nodes"].pop(index)
    contenido["edges"] = [
        edge
        for edge in contenido.get("edges", [])
        if edge.get("source") != clase_id and edge.get("target") != clase_id
    ]

    diagrama.contenido = contenido
    flag_modified(diagrama, "contenido")
    diagrama.version += 1
    diagrama.actualizado_en = datetime.utcnow()

    db.commit()
    db.refresh(diagrama)

    return diagrama, None
