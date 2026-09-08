from sqlalchemy import create_engine
from  sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL) #se crea una conxion con postgreSQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # se crea sseiones para consultar con la base de datos
Base = declarative_base() #base para crear modelos/tablas 

#se entrega la conexion a los endpoints
def get_db(): 
    db = SessionLocal()
    try: 
        yield db 
    finally: 
        db.close()

