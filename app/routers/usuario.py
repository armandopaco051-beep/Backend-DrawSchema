from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.usuario_service import (
    crear_usuario, 
    listar_usuarios, 
    obtener_usuario, 
    actualizar_usuario, 
    eliminar_usuario,
    obtener_usuario_por_email
)
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse


router  = APIRouter(prefix = "/usuarios", tags = ["Usuarios"])

@router.post("/", response_model = UsuarioResponse )
def crear(datos : UsuarioCreate , db : Session  = Depends(get_db)): 
    usuario_existente  = obtener_usuario_por_email(db, datos.email)
    
    if usuario_existente: 
        raise HTTPException(status_code = 400, detail ="El email ya existe")
    return crear_usuario(db,datos)


@router.get("/", response_model = list[UsuarioResponse])
def listar(db : Session = Depends(get_db)):
    return listar_usuarios(db)


@router.get("/{codigo}", response_model = UsuarioResponse) 
def obtener ( codigo :str , db : Session = Depends(get_db)): 
    usuario = obtener_usuario(db, codigo)
    
    if usuario is None : raise HTTPException(status_code = 404 , detail = "usuario no encontrado")

    return usuario

@router.put("/{codigo}", response_model = UsuarioResponse)
def actualizar(codigo :str,datos :UsuarioUpdate,db : Session = Depends(get_db)): 
    usuario = actualizar_usuario(db, codigo, datos)
    if usuario is None : raise HTTPException(status_code = 404, detail = "Usuario no encontrado")

    return usuario


@router.delete("/{codigo}")
def eliminar (codigo: str , db : Session = Depends(get_db)) : 
    usuario = eliminar_usuario(db,codigo)
    if usuario is None : raise HTTPException(status_code = 404 , detail = "Usuario no encotrado")
    return {
    "mensaje": "Usuario eliminado correctamente"
    }

