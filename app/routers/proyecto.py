from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.proyecto import (
    CodigoInvitacionResponse,
    InvitacionPreviewResponse,
    ProyectoCreate,
    ProyectoResponse,
    ProyectoUpdate,
    ProyectoUsuarioCreate,
    ProyectoUsuarioResponse,
    ProyectoUsuarioUpdate,
    UnirseProyectoRequest,
)
from app.security.auth_dependencies import get_current_user
from app.services.proyecto import (
    actualizar_proyecto,
    actualizar_rol_colaborador,
    agregar_colaborador_a_proyecto,
    crear_proyecto,
    eliminar_proyecto,
    listar_miembros_proyecto,
    listar_proyectos,
    listar_proyectos_por_usuario,
    obtener_info_codigo_invitacion,
    obtener_o_crear_codigo_invitacion,
    obtener_proyecto,
    quitar_colaborador_de_proyecto,
    unirse_a_proyecto_con_codigo,
    usuario_tiene_permiso,
)



router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


def verificar_permiso_proyecto(
    db: Session,
    proyecto_id: int,
    usuario_codigo: str,
    permiso: str,
):
    if not usuario_tiene_permiso(db, proyecto_id, usuario_codigo, permiso):
        raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta accion")


@router.post("/", response_model=ProyectoResponse)
def crear(datos: ProyectoCreate, db: Session = Depends(get_db)):
    proyecto, error = crear_proyecto(db, datos)

    if error == "USUARIO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Usuario no existe")

    if error == "ROL_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Rol no existe")

    if error == "ROL_PROYECTO_INVALIDO":
        raise HTTPException(
            status_code=400,
            detail="El rol del proyecto debe ser propietario, admin, editor o visualizador",
        )

    return proyecto


@router.get("/", response_model=list[ProyectoResponse])
def listar(db: Session = Depends(get_db)):
    return listar_proyectos(db)


@router.get("/usuario/{usuario_codigo}", response_model=list[ProyectoResponse])
def listar_por_usuario(usuario_codigo: str, db: Session = Depends(get_db)):
    return listar_proyectos_por_usuario(db, usuario_codigo)


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
def obtener(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    verificar_permiso_proyecto(db, proyecto_id, usuario_actual.codigo, "ver_proyecto")

    return proyecto


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
def actualizar(
    proyecto_id: int,
    datos: ProyectoUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_proyecto(db, proyecto_id, usuario_actual.codigo, "editar_proyecto")
    proyecto = actualizar_proyecto(db, proyecto_id, datos)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return proyecto


@router.delete("/{proyecto_id}")
def eliminar(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_proyecto(db, proyecto_id, usuario_actual.codigo, "eliminar_proyecto")
    proyecto = eliminar_proyecto(db, proyecto_id)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return {"mensaje": "Proyecto eliminado correctamente"}


@router.post("/{proyecto_id}/miembros", response_model=ProyectoUsuarioResponse)
def agregar_miembro(
    proyecto_id: int,
    datos: ProyectoUsuarioCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    miembro, error = agregar_colaborador_a_proyecto(
        db,
        proyecto_id,
        datos,
        usuario_actual.codigo,
    )

    if error == "USUARIO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Usuario no existe")

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    if error == "ROL_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Rol no existe")

    if error == "ROL_PROYECTO_INVALIDO":
        raise HTTPException(
            status_code=400,
            detail="El rol del proyecto debe ser propietario, admin, editor o visualizador",
        )

    if error == "SIN_PERMISO":
        raise HTTPException(status_code=403, detail="No tienes permiso para gestionar miembros")

    if error == "USUARIO_YA_ESTA_EN_PROYECTO":
        raise HTTPException(status_code=400, detail="El usuario ya pertenece al proyecto")

    return miembro


@router.get("/{proyecto_id}/miembros", response_model=list[ProyectoUsuarioResponse])
def listar_miembros(
    proyecto_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    verificar_permiso_proyecto(db, proyecto_id, usuario_actual.codigo, "ver_proyecto")
    return listar_miembros_proyecto(db, proyecto_id)


@router.put("/{proyecto_id}/miembros/{usuario_codigo}", response_model=ProyectoUsuarioResponse)
def cambiar_rol_miembro(
    proyecto_id: int,
    usuario_codigo: str,
    datos: ProyectoUsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    miembro, error = actualizar_rol_colaborador(
        db,
        proyecto_id,
        usuario_codigo,
        datos,
        usuario_actual.codigo,
    )

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    if error == "MIEMBRO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Miembro no encontrado en el proyecto")

    if error == "ROL_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Rol no existe")

    if error == "ROL_PROYECTO_INVALIDO":
        raise HTTPException(
            status_code=400,
            detail="El rol del proyecto debe ser propietario, admin, editor o visualizador",
        )

    if error == "SIN_PERMISO":
        raise HTTPException(status_code=403, detail="No tienes permiso para gestionar miembros")

    if error == "NO_PUEDE_QUEDAR_SIN_PROPIETARIO":
        raise HTTPException(status_code=400, detail="El proyecto debe tener al menos un propietario")

    return miembro


@router.delete("/{proyecto_id}/miembros/{usuario_codigo}")
def quitar_miembro(
    proyecto_id: int,
    usuario_codigo: str,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    miembro, error = quitar_colaborador_de_proyecto(
        db,
        proyecto_id,
        usuario_codigo,
        usuario_actual.codigo,
    )

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    if error == "MIEMBRO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Miembro no encontrado en el proyecto")

    if error == "SIN_PERMISO":
        raise HTTPException(status_code=403, detail="No tienes permiso para gestionar miembros")

    if error == "NO_PUEDE_QUEDAR_SIN_PROPIETARIO":
        raise HTTPException(status_code=400, detail="El proyecto debe tener al menos un propietario")

    return {"mensaje": "Usuario quitado del proyecto correctamente"}


@router.post("/{proyecto_id}/codigo-invitacion", response_model=CodigoInvitacionResponse)
def generar_o_obtener_codigo(
    proyecto_id: int,
    forzar: bool = False,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    resultado, error = obtener_o_crear_codigo_invitacion(
        db,
        proyecto_id,
        usuario_actual.codigo,
        forzar=forzar,
    )

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    if error == "SIN_PERMISO":
        raise HTTPException(status_code=403, detail="No tienes permiso para gestionar invitaciones de este proyecto")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return resultado


@router.get("/invitacion/{codigo}", response_model=InvitacionPreviewResponse)
def vista_previa_invitacion(
    codigo: str,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    resultado, error = obtener_info_codigo_invitacion(db, codigo)

    if error == "CODIGO_INVALIDO":
        raise HTTPException(status_code=404, detail="Código de invitación no encontrado")

    if error == "CODIGO_VACIO":
        raise HTTPException(status_code=400, detail="El código no puede estar vacío")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return resultado


@router.post("/unirse", response_model=ProyectoResponse)
def unirse_con_codigo(
    datos: UnirseProyectoRequest,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    proyecto, error = unirse_a_proyecto_con_codigo(
        db,
        datos.codigo,
        usuario_actual.codigo,
    )

    if error == "CODIGO_INVALIDO":
        raise HTTPException(status_code=404, detail="Código de invitación no encontrado")

    if error == "CODIGO_EXPIRADO":
        raise HTTPException(status_code=400, detail="El código de invitación ha expirado")

    if error == "USUARIO_YA_ESTA_EN_PROYECTO":
        raise HTTPException(status_code=400, detail="Ya perteneces a este proyecto")

    if error == "CODIGO_VACIO":
        raise HTTPException(status_code=400, detail="El código no puede estar vacío")

    if error:
        raise HTTPException(status_code=400, detail=error)

    return proyecto

