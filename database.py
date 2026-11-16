from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL  

#crea il collegamento tra l'applicazione e il database 
engine = create_engine(DATABASE_URL)

#crea sessioni
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)