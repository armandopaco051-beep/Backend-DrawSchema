from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.security.password import hash_password

def crear_usuario(db : Session, datos : UsuarioCreate): 
    usuario = Usuario(
        codigo = datos.codigo, 
        nombres = datos.nombres, 
        apellidos = datos.apellidos, 
        email = datos.email,
        password = hash_password(datos.password),
        pais  = datos.pais,
        id_rol = datos.id_rol
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario

def listar_usuarios(db : Session):
    return db.query(Usuario).all()

def obtener_usuario(db: Session, codigo : str): 
    return db.query(Usuario).filter(Usuario.codigo == codigo).first()

def obtener_usuario_por_email(db : Session , email: str): 
    return db.query(Usuario).filter(Usuario.email == email).first()

def actualizar_usuario(db :Session, codigo :str, datos :UsuarioUpdate) :
    usuario = obtener_usuario(db, codigo)

    if usuario is None : return None 
    if datos.nombres is not None : usuario.nombres = datos.nombres
    if datos.apellidos is not None : usuario.apellidos = datos.apellidos
    if datos.email is not None : usuario.email = datos.email
    if datos.password is not None: usuario.password = hash_password(datos.password)
    if datos.pais is not None : usuario.pais  = datos.pais 
    if datos.id_rol is not None  : usuario.id_rol = datos.id_rol

    db.commit()
    db.refresh(usuario)
    
    return usuario

def eliminar_usuario(db: Session, codigo :str): 
    usuario = obtener_usuario(db, codigo)

    if usuario is None : 
        return None

    db.delete(usuario)
    db.commit()
    return usuario
