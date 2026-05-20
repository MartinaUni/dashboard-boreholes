from fastapi import FastAPI
from models import Base
from database import engine

from routers import pozzi, geologia
from routers.auth import router as auth_router


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(pozzi.router)
app.include_router(geologia.router)
app.include_router(auth_router)

