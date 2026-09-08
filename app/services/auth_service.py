from sqlalchemy.orm import Session 

from app.services.usuario_service import obtener_usuario_por_email
from app.security.password import verify_password
from app.security.jwt import crear_token

def login_usuario(db : Session, email : str , password :str ): 
    usuario = obtener_usuario_por_email(db, email)
    if usuario is None :  return None
    if not verify_password(password, usuario.password): 
        return None 
    
    token= crear_token({
        "sub" : usuario.codigo,
        "email": usuario.email, 
        "id_rol" : usuario.id_rol
    })
    return token
    
