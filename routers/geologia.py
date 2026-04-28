from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Eone, Era, Periodo, Epoca, EtaPiano

router = APIRouter(prefix="/geologia", tags=["Geologia"])



# DATABASE SESSION

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



#  SCALA GEOLOGICA COMPLETA
# Uso:
#   GET /geologia/scala

@router.get("/scala", summary="Gerarchia geologica completa ordinata cronologicamente")
def scala_geologica(db: Session = Depends(get_db)):
    """
    Restituisce la scala dei tempi geologici come lista
    di oggetti annidati: eone > era > periodo > epoca.
    Utile per costruire la legenda del profilo verticale.
    """
    results = (
        db.query(Eone, Era, Periodo, Epoca)
        .join(Era,     Era.cod_eone     == Eone.cod_eone)
        .join(Periodo, Periodo.cod_era  == Era.cod_era)
        .join(Epoca,   Epoca.cod_periodo == Periodo.cod_periodo)
        .order_by(Eone.anni_inf, Era.anni_inf, Periodo.anni_inf, Epoca.anni_inf)
        .all()
    )

    return [
        {
            "eone":       eone.eone,
            "cod_eone":   eone.cod_eone,
            "era":        era.era,
            "cod_era":    era.cod_era,
            "periodo":    periodo.periodo,
            "cod_periodo": periodo.cod_periodo,
            "epoca":      epoca.epoca,
            "cod_epoca":  epoca.cod_epoca,
            "anni_inf":   epoca.anni_inf,
            "anni_sup":   epoca.anni_sup,
        }
        for eone, era, periodo, epoca in results
    ]



# LOOKUP ETÀ GEOLOGICA

@router.get("/eta", summary="Contesto geologico per un'età in milioni di anni")
def eta_geologica(
    anni: float = Query(..., description="Età in milioni di anni (es. 65 per il Cretacico superiore)"),
    db: Session = Depends(get_db)
):
    """
    Dato un valore in milioni di anni, restituisce il periodo
    e l'epoca geologica corrispondente.
    Utile per inquadrare un intervallo stratigrafico nella
    scala dei tempi geologici.
    """

    # cerco prima nell'epoca (livello più fine)
    epoca = (
        db.query(Epoca)
        .filter(Epoca.anni_inf <= anni, Epoca.anni_sup >= anni)
        .first()
    )

    # poi nel periodo
    periodo = (
        db.query(Periodo)
        .filter(Periodo.anni_inf <= anni, Periodo.anni_sup >= anni)
        .first()
    )

    # poi nell'era
    era = (
        db.query(Era)
        .filter(Era.anni_inf <= anni, Era.anni_sup >= anni)
        .first()
    )

    # poi nell'eone
    eone = (
        db.query(Eone)
        .filter(Eone.anni_inf <= anni, Eone.anni_sup >= anni)
        .first()
    )

    if not eone:
        raise HTTPException(
            status_code=404,
            detail=f"Nessun contesto geologico trovato per {anni} milioni di anni"
        )

    return {
        "anni":    anni,
        "eone":    eone.eone    if eone    else None,
        "era":     era.era      if era     else None,
        "periodo": periodo.periodo if periodo else None,
        "epoca":   epoca.epoca  if epoca   else None,
    }