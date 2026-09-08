from sqlalchemy.orm import Session

from app.models.proyecto import Proyecto
from app.models.proyecto_usuario import ProyectoUsuario
from app.models.usuario import Usuario, Rol
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate, ProyectoUsuarioCreate


def crear_proyecto(db: Session, datos: ProyectoCreate):
    usuario = db.query(Usuario).filter(Usuario.codigo == datos.usuario_codigo).first()

    if usuario is None:
        return None, "Usuario no Existe"

    rol = db.query(Rol).filter(Rol.id == datos.id_rol).first()

    if rol is None:
        return None, "Rol no existente"

    proyecto = Proyecto(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
    )

    db.add(proyecto)
    db.commit()
    db.refresh(proyecto)

    proyecto_usuario = ProyectoUsuario(
        usuario_codigo=datos.usuario_codigo,
        id_proyecto=proyecto.id,
        id_rol=datos.id_rol,
    )

    db.add(proyecto_usuario)
    db.commit()

    return proyecto, None


def listar_proyectos(db: Session):
    return db.query(Proyecto).all()


def obtener_proyecto(db: Session, proyecto_id: int):
    return db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()


def listar_proyectos_por_usuario(db: Session, usuario_codigo: str):
    return (
        db.query(Proyecto)
        .join(ProyectoUsuario, Proyecto.id == ProyectoUsuario.id_proyecto)
        .filter(ProyectoUsuario.usuario_codigo == usuario_codigo)
        .all()
    )


def actualizar_proyecto(db: Session, proyecto_id: int, datos: ProyectoUpdate):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        return None

    if datos.nombre is not None:
        proyecto.nombre = datos.nombre

    if datos.descripcion is not None:
        proyecto.descripcion = datos.descripcion

    db.commit()
    db.refresh(proyecto)

    return proyecto


def eliminar_proyecto(db: Session, proyecto_id: int):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        return None

    db.delete(proyecto)
    db.commit()

    return proyecto


def agregar_usuario_a_proyecto(db: Session, datos: ProyectoUsuarioCreate):
    usuario = db.query(Usuario).filter(Usuario.codigo == datos.usuario_codigo).first()

    if usuario is None:
        return None, "Usuario no existente"

    proyecto = obtener_proyecto(db, datos.id_proyecto)

    if proyecto is None:
        return None, "Proyecto no existe"

    rol = db.query(Rol).filter(Rol.id == datos.id_rol).first()

    if rol is None:
        return None, "Rol no existente"

    existe = (
        db.query(ProyectoUsuario)
        .filter(
            ProyectoUsuario.usuario_codigo == datos.usuario_codigo,
            ProyectoUsuario.id_proyecto == datos.id_proyecto,
        )
        .first()
    )

    if existe:
        return None, "El usuario ya se encuentra en el proyecto"

    proyecto_usuario = ProyectoUsuario(
        usuario_codigo=datos.usuario_codigo,
        id_proyecto=datos.id_proyecto,
        id_rol=datos.id_rol,
    )

    db.add(proyecto_usuario)
    db.commit()
    db.refresh(proyecto_usuario)

    return proyecto_usuario, None


def listar_miembros_proyecto(db: Session, proyecto_id: int):
    return (
        db.query(ProyectoUsuario)
        .filter(ProyectoUsuario.id_proyecto == proyecto_id)
        .all()
    )


def quitar_usuario_de_proyecto(db: Session, proyecto_id: int, usuario_codigo: str):
    miembro = (
        db.query(ProyectoUsuario)
        .filter(
            ProyectoUsuario.id_proyecto == proyecto_id,
            ProyectoUsuario.usuario_codigo == usuario_codigo,
        )
        .first()
    )

    if miembro is None:
        return None

    db.delete(miembro)
    db.commit()

    return miembro