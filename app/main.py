from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine 
from app import models
from app.routers.auth import router as auth
from app.routers.usuario import router as usuario
from app.routers.proyecto import router as proyecto
from app.routers.diagrama import router as diagrama

Base.metadata.create_all(bind=engine) # Crear las tablas en la base de datos

app = FastAPI(
    title = "Backen Diagramador Colaborativo",
    version = "1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.router.include_router(auth)
app.router.include_router(usuario)
app.router.include_router(proyecto)
app.router.include_router(diagrama)


@app.get("/")
def inicio(): 
    return {
        "mensaje": "Backend corriendo y funcionando correctamente"
    }

@app.get("/health")
def health_check(): 
    return {
        "estado" : "ok",
        "Base de datos": "conectada"
    }
