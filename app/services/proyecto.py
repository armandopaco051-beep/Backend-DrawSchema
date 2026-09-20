from datetime import datetime, timedelta
import secrets
import string

from sqlalchemy.orm import Session

from app.models.proyecto import Proyecto
from app.models.proyecto_usuario import ProyectoUsuario
from app.models.usuario import Usuario, Rol
from app.schemas.proyecto import ProyectoCreate, ProyectoUpdate, ProyectoUsuarioCreate, ProyectoUsuarioUpdate


PROJECT_ROLE_PERMISSIONS = {
    "propietario": {
        "ver_proyecto",
        "editar_proyecto",
        "eliminar_proyecto",
        "gestionar_miembros",
        "crear_diagrama",
        "editar_diagrama",
        "eliminar_diagrama",
        "ver_diagrama",
    },
    "admin": {
        "ver_proyecto",
        "editar_proyecto",
        "gestionar_miembros",
        "crear_diagrama",
        "editar_diagrama",
        "eliminar_diagrama",
        "ver_diagrama",
    },
    "editor": {
        "ver_proyecto",
        "crear_diagrama",
        "editar_diagrama",
        "ver_diagrama",
    },
    "visualizador": {
        "ver_proyecto",
        "ver_diagrama",
    },
}

PROJECT_ROLE_ALIASES = {
    "colaborador": "editor",
    "views": "visualizador",
}


def normalizar_rol(nombre: str | None):
    rol = (nombre or "").strip().lower()
    return PROJECT_ROLE_ALIASES.get(rol, rol)


def obtener_miembro_proyecto(db: Session, proyecto_id: int, usuario_codigo: str):
    return (
        db.query(ProyectoUsuario)
        .filter(
            ProyectoUsuario.id_proyecto == proyecto_id,
            ProyectoUsuario.usuario_codigo == usuario_codigo,
        )
        .first()
    )


def rol_es_valido_para_proyecto(rol: Rol | None):
    if rol is None:
        return False

    return normalizar_rol(rol.nombre) in PROJECT_ROLE_PERMISSIONS


def usuario_tiene_permiso(db: Session, proyecto_id: int, usuario_codigo: str, permiso: str):
    miembro = obtener_miembro_proyecto(db, proyecto_id, usuario_codigo)

    if miembro is None or miembro.rol is None:
        return False

    permisos = PROJECT_ROLE_PERMISSIONS.get(normalizar_rol(miembro.rol.nombre), set())
    return permiso in permisos


def contar_propietarios(db: Session, proyecto_id: int):
    return (
        db.query(ProyectoUsuario)
        .join(Rol, ProyectoUsuario.id_rol == Rol.id)
        .filter(
            ProyectoUsuario.id_proyecto == proyecto_id,
            Rol.nombre.ilike("propietario"),
        )
        .count()
    )


def crear_proyecto(db: Session, datos: ProyectoCreate):
    usuario = db.query(Usuario).filter(Usuario.codigo == datos.usuario_codigo).first()

    if usuario is None:
        return None, "USUARIO_NO_EXISTE"

    rol = db.query(Rol).filter(Rol.id == datos.id_rol).first()

    if rol is None:
        return None, "ROL_NO_EXISTE"

    if not rol_es_valido_para_proyecto(rol):
        return None, "ROL_PROYECTO_INVALIDO"

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
        return None, "USUARIO_NO_EXISTE"

    proyecto = obtener_proyecto(db, datos.id_proyecto)

    if proyecto is None:
        return None, "PROYECTO_NO_EXISTE"

    rol = db.query(Rol).filter(Rol.id == datos.id_rol).first()

    if rol is None:
        return None, "ROL_NO_EXISTE"

    if not rol_es_valido_para_proyecto(rol):
        return None, "ROL_PROYECTO_INVALIDO"

    existe = obtener_miembro_proyecto(db, datos.id_proyecto, datos.usuario_codigo)

    if existe:
        return None, "USUARIO_YA_ESTA_EN_PROYECTO"

    proyecto_usuario = ProyectoUsuario(
        usuario_codigo=datos.usuario_codigo,
        id_proyecto=datos.id_proyecto,
        id_rol=datos.id_rol,
    )

    db.add(proyecto_usuario)
    db.commit()
    db.refresh(proyecto_usuario)

    return proyecto_usuario, None


def agregar_colaborador_a_proyecto(
    db: Session,
    proyecto_id: int,
    datos: ProyectoUsuarioCreate,
    actor_codigo: str,
):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        return None, "PROYECTO_NO_EXISTE"

    if not usuario_tiene_permiso(db, proyecto_id, actor_codigo, "gestionar_miembros"):
        return None, "SIN_PERMISO"

    datos.id_proyecto = proyecto_id
    return agregar_usuario_a_proyecto(db, datos)


def actualizar_rol_colaborador(
    db: Session,
    proyecto_id: int,
    usuario_codigo: str,
    datos: ProyectoUsuarioUpdate,
    actor_codigo: str,
):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        return None, "PROYECTO_NO_EXISTE"

    if not usuario_tiene_permiso(db, proyecto_id, actor_codigo, "gestionar_miembros"):
        return None, "SIN_PERMISO"

    miembro = obtener_miembro_proyecto(db, proyecto_id, usuario_codigo)

    if miembro is None:
        return None, "MIEMBRO_NO_EXISTE"

    nuevo_rol = db.query(Rol).filter(Rol.id == datos.id_rol).first()

    if nuevo_rol is None:
        return None, "ROL_NO_EXISTE"

    if not rol_es_valido_para_proyecto(nuevo_rol):
        return None, "ROL_PROYECTO_INVALIDO"

    rol_actual = normalizar_rol(miembro.rol.nombre if miembro.rol else None)
    nuevo_rol_nombre = normalizar_rol(nuevo_rol.nombre)

    if rol_actual == "propietario" and nuevo_rol_nombre != "propietario":
        if contar_propietarios(db, proyecto_id) <= 1:
            return None, "NO_PUEDE_QUEDAR_SIN_PROPIETARIO"

    miembro.id_rol = datos.id_rol
    db.commit()
    db.refresh(miembro)

    return miembro, None


def listar_miembros_proyecto(db: Session, proyecto_id: int):
    return (
        db.query(ProyectoUsuario)
        .filter(ProyectoUsuario.id_proyecto == proyecto_id)
        .all()
    )


def quitar_usuario_de_proyecto(db: Session, proyecto_id: int, usuario_codigo: str):
    miembro = obtener_miembro_proyecto(db, proyecto_id, usuario_codigo)

    if miembro is None:
        return None

    db.delete(miembro)
    db.commit()

    return miembro


def quitar_colaborador_de_proyecto(db: Session, proyecto_id: int, usuario_codigo: str, actor_codigo: str):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        return None, "PROYECTO_NO_EXISTE"

    if not usuario_tiene_permiso(db, proyecto_id, actor_codigo, "gestionar_miembros"):
        return None, "SIN_PERMISO"

    miembro = obtener_miembro_proyecto(db, proyecto_id, usuario_codigo)

    if miembro is None:
        return None, "MIEMBRO_NO_EXISTE"

    rol_actual = normalizar_rol(miembro.rol.nombre if miembro.rol else None)

    if rol_actual == "propietario" and contar_propietarios(db, proyecto_id) <= 1:
        return None, "NO_PUEDE_QUEDAR_SIN_PROPIETARIO"

    db.delete(miembro)
    db.commit()

    return miembro, None


def generar_token_invitacion(longitud: int = 6) -> str:
    caracteres = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    random_part = "".join(secrets.choice(caracteres) for _ in range(longitud))
    return f"PRJ-{random_part}"


def obtener_o_crear_codigo_invitacion(
    db: Session,
    proyecto_id: int,
    actor_codigo: str,
    forzar: bool = False,
    dias_validez: int = 7,
):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        return None, "PROYECTO_NO_EXISTE"

    if not usuario_tiene_permiso(db, proyecto_id, actor_codigo, "gestionar_miembros"):
        return None, "SIN_PERMISO"

    ahora = datetime.utcnow()

    # Si ya existe código, no ha expirado y no se fuerza regeneración, reutilizamos el código
    if (
        not forzar
        and proyecto.codigo_invitacion
        and proyecto.codigo_expira_en
        and proyecto.codigo_expira_en > ahora
    ):
        dias_restantes = max(0, (proyecto.codigo_expira_en - ahora).days)
        return {
            "codigo": proyecto.codigo_invitacion,
            "expira_en": proyecto.codigo_expira_en,
            "dias_restantes": dias_restantes,
            "es_nuevo": False,
        }, None

    # Generar nuevo código garantizando que no colisione
    nuevo_codigo = generar_token_invitacion()
    while db.query(Proyecto).filter(Proyecto.codigo_invitacion == nuevo_codigo).first() is not None:
        nuevo_codigo = generar_token_invitacion()

    nueva_expiracion = ahora + timedelta(days=dias_validez)
    proyecto.codigo_invitacion = nuevo_codigo
    proyecto.codigo_expira_en = nueva_expiracion

    db.commit()
    db.refresh(proyecto)

    return {
        "codigo": proyecto.codigo_invitacion,
        "expira_en": proyecto.codigo_expira_en,
        "dias_restantes": dias_validez,
        "es_nuevo": True,
    }, None


def obtener_info_codigo_invitacion(db: Session, codigo: str):
    codigo_limpio = (codigo or "").strip().upper()

    if not codigo_limpio:
        return None, "CODIGO_VACIO"

    proyecto = db.query(Proyecto).filter(Proyecto.codigo_invitacion == codigo_limpio).first()

    if proyecto is None:
        return None, "CODIGO_INVALIDO"

    ahora = datetime.utcnow()
    valido = bool(proyecto.codigo_expira_en and proyecto.codigo_expira_en > ahora)

    return {
        "proyecto_id": proyecto.id,
        "nombre": proyecto.nombre,
        "descripcion": proyecto.descripcion,
        "valido": valido,
        "expira_en": proyecto.codigo_expira_en,
    }, None


def unirse_a_proyecto_con_codigo(db: Session, codigo: str, usuario_codigo: str):
    codigo_limpio = (codigo or "").strip().upper()

    if not codigo_limpio:
        return None, "CODIGO_VACIO"

    proyecto = db.query(Proyecto).filter(Proyecto.codigo_invitacion == codigo_limpio).first()

    if proyecto is None:
        return None, "CODIGO_INVALIDO"

    ahora = datetime.utcnow()

    if not proyecto.codigo_expira_en or proyecto.codigo_expira_en <= ahora:
        return None, "CODIGO_EXPIRADO"

    miembro = obtener_miembro_proyecto(db, proyecto.id, usuario_codigo)

    if miembro:
        return None, "USUARIO_YA_ESTA_EN_PROYECTO"

    # Buscar rol editor por defecto, o colaborador
    rol_editor = db.query(Rol).filter(Rol.nombre.ilike("editor")).first()

    if not rol_editor:
        rol_editor = db.query(Rol).filter(Rol.nombre.ilike("colaborador")).first()

    if not rol_editor:
        rol_editor = db.query(Rol).first()

    if not rol_editor:
        return None, "ROL_NO_EXISTE"

    nuevo_miembro = ProyectoUsuario(
        usuario_codigo=usuario_codigo,
        id_proyecto=proyecto.id,
        id_rol=rol_editor.id,
    )

    db.add(nuevo_miembro)
    db.commit()

    return proyecto, None

