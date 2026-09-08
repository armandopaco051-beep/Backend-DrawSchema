from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioResponse
from app.security.auth_dependencies import get_current_user
from app.services.auth_service import login_usuario


router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    token = login_usuario(db, datos.email, datos.password)

    if token is None:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UsuarioResponse)
def obtener_perfil(usuario: Usuario = Depends(get_current_user)):
    return usuario
