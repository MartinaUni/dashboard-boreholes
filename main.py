from fastapi import FastAPI
from models import Base
from database import engine

from routers import pozzi, geologia
from routers.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware

#crea applicazione
app = FastAPI()

# permessi
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#creazione automatica delle tabelle
Base.metadata.create_all(bind=engine)

#registrazione dei router
app.include_router(pozzi.router)
app.include_router(geologia.router)
app.include_router(auth_router)

