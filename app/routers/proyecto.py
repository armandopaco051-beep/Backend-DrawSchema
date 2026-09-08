from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.proyecto import (
    ProyectoCreate,
    ProyectoResponse,
    ProyectoUpdate,
    ProyectoUsuarioCreate,
    ProyectoUsuarioResponse,
)
from app.services.proyecto import (
    actualizar_proyecto,
    agregar_usuario_a_proyecto,
    crear_proyecto,
    eliminar_proyecto,
    listar_miembros_proyecto,
    listar_proyectos,
    listar_proyectos_por_usuario,
    obtener_proyecto,
    quitar_usuario_de_proyecto,
)


router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


@router.post("/", response_model=ProyectoResponse)
def crear(datos: ProyectoCreate, db: Session = Depends(get_db)):
    proyecto, error = crear_proyecto(db, datos)

    if error == "USUARIO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Usuario no existe")

    if error == "ROL_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Rol no existe")

    return proyecto


@router.get("/", response_model=list[ProyectoResponse])
def listar(db: Session = Depends(get_db)):
    return listar_proyectos(db)


@router.get("/usuario/{usuario_codigo}", response_model=list[ProyectoResponse])
def listar_por_usuario(usuario_codigo: str, db: Session = Depends(get_db)):
    return listar_proyectos_por_usuario(db, usuario_codigo)


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
def obtener(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = obtener_proyecto(db, proyecto_id)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return proyecto


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
def actualizar(proyecto_id: int, datos: ProyectoUpdate, db: Session = Depends(get_db)):
    proyecto = actualizar_proyecto(db, proyecto_id, datos)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return proyecto


@router.delete("/{proyecto_id}")
def eliminar(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = eliminar_proyecto(db, proyecto_id)

    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return {"mensaje": "Proyecto eliminado correctamente"}


@router.post("/{proyecto_id}/miembros", response_model=ProyectoUsuarioResponse)
def agregar_miembro(
    proyecto_id: int,
    datos: ProyectoUsuarioCreate,
    db: Session = Depends(get_db),
):
    datos.id_proyecto = proyecto_id
    miembro, error = agregar_usuario_a_proyecto(db, datos)

    if error == "USUARIO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Usuario no existe")

    if error == "PROYECTO_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Proyecto no existe")

    if error == "ROL_NO_EXISTE":
        raise HTTPException(status_code=404, detail="Rol no existe")

    if error == "USUARIO_YA_ESTA_EN_PROYECTO":
        raise HTTPException(status_code=400, detail="El usuario ya pertenece al proyecto")

    return miembro


@router.get("/{proyecto_id}/miembros", response_model=list[ProyectoUsuarioResponse])
def listar_miembros(proyecto_id: int, db: Session = Depends(get_db)):
    return listar_miembros_proyecto(db, proyecto_id)


@router.delete("/{proyecto_id}/miembros/{usuario_codigo}")
def quitar_miembro(
    proyecto_id: int,
    usuario_codigo: str,
    db: Session = Depends(get_db),
):
    miembro = quitar_usuario_de_proyecto(db, proyecto_id, usuario_codigo)

    if miembro is None:
        raise HTTPException(status_code=404, detail="Miembro no encontrado en el proyecto")

    return {"mensaje": "Usuario quitado del proyecto correctamente"}
