from pydantic import BaseModel, EmailStr
# crear usuario
class UsuarioCreate(BaseModel): 
    codigo : str 
    nombres : str
    apellidos: str 
    email: EmailStr
    password: str 
    pais: str 
    id_rol: int 
#actualizar usuario
class UsuarioUpdate(BaseModel): 
    nombres : str | None = None
    apellidos: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    pais: str | None = None
    id_rol: int | None = None   

# obtener usuarios
class UsuarioResponse(BaseModel): 
    codigo : str 
    nombres :str 
    apellidos  : str 
    email: EmailStr 
    pais : str
    id_rol: int 

    class Config: 
        from_attributes = True
