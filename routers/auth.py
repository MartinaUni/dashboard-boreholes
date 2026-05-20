from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Utente

# ==================================================
# CONFIGURAZIONE
# ==================================================

# Chiave segreta per firmare i token JWT
# In produzione va messa in una variabile d'ambiente
SECRET_KEY = "chiave_segreta_da_cambiare_in_produzione"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # il token scade dopo 1 ora

router = APIRouter(prefix="/auth", tags=["Autenticazione"])

# contesto per hashare e verificare le password con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# schema OAuth2 — indica a FastAPI dove trovare il token (header Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ==================================================
# MODELLI PYDANTIC
# ==================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    ruolo: str


class TokenData(BaseModel):
    username: Optional[str] = None
    ruolo: Optional[str] = None


# ==================================================
# DATABASE SESSION
# ==================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================================================
# FUNZIONI HELPER
# ==================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica che la password in chiaro corrisponda all'hash salvato."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Genera l'hash bcrypt di una password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT con i dati passati e una scadenza."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_utente(db: Session, username: str) -> Optional[Utente]:
    """Recupera un utente dal database tramite username."""
    return db.query(Utente).filter(Utente.username == username).first()


# ==================================================
# DEPENDENCY: utente corrente
# Usata come Depends() negli endpoint per ottenere
# l'utente autenticato dalla richiesta corrente.
# ==================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Utente:
    """
    Legge il token JWT dall'header Authorization,
    lo decodifica e restituisce l'utente corrispondente.
    Solleva 401 se il token non è valido o scaduto.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token non valido o scaduto",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        ruolo: str = payload.get("ruolo")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, ruolo=ruolo)
    except JWTError:
        raise credentials_exception

    utente = get_utente(db, token_data.username)
    if utente is None:
        raise credentials_exception
    return utente


# ==================================================
# DEPENDENCY: solo utenti esperti
# Aggiungere Depends(require_esperto) agli endpoint
# riservati agli utenti esperti.
# ==================================================

def require_esperto(current_user: Utente = Depends(get_current_user)) -> Utente:
    """
    Blocca l'accesso se l'utente non è esperto.
    Solleva 403 Forbidden.
    """
    if current_user.ruolo != "esperto":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato agli utenti esperti"
        )
    return current_user


# ==================================================
# DEPENDENCY: qualsiasi utente autenticato
# Aggiungere Depends(require_base) agli endpoint
# accessibili a tutti gli utenti loggati.
# ==================================================

def require_base(current_user: Utente = Depends(get_current_user)) -> Utente:
    """
    Verifica che l'utente sia autenticato (base o esperto).
    """
    return current_user


# ==================================================
# ENDPOINT LOGIN
# POST /auth/login
# Riceve username e password, verifica le credenziali
# e restituisce un token JWT.
# ==================================================

@router.post("/login", response_model=Token, summary="Login e ottenimento token JWT")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint di login. Accetta username e password nel body
    come form data (standard OAuth2).

    Restituisce un token JWT da usare nelle richieste successive
    nell'header: Authorization: Bearer <token>
    """
    utente = get_utente(db, form_data.username)

    if not utente or not verify_password(form_data.password, utente.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username o password errati",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": utente.username, "ruolo": utente.ruolo},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "ruolo": utente.ruolo
    }


# ==================================================
# ENDPOINT REGISTRAZIONE
# POST /auth/registra
# Crea un nuovo utente base nel database.
# Gli utenti esperti vanno creati manualmente su pgAdmin.
# ==================================================

@router.post("/registra", summary="Registrazione nuovo utente base")
def registra(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    Registra un nuovo utente con ruolo 'base'.
    Per creare utenti esperti modificare direttamente il database.
    """
    if get_utente(db, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username già esistente"
        )

    nuovo_utente = Utente(
        username=username,
        password=hash_password(password),
        ruolo="base"
    )
    db.add(nuovo_utente)
    db.commit()

    return {"messaggio": f"Utente '{username}' creato con ruolo 'base'"}


# ==================================================
# ENDPOINT INFO UTENTE CORRENTE
# GET /auth/me
# Restituisce le info dell'utente loggato.
# ==================================================

@router.get("/me", summary="Info utente corrente")
def me(current_user: Utente = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "ruolo":    current_user.ruolo
    }