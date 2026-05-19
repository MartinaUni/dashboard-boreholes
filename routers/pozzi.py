from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from database import SessionLocal
from models import (
    Pozzo, Tipi, Stato, Usi, Scopi, Esiti, Inn,
    Regioni, Province, Comuni, Temp, Grados,
    Litologia, WellCoord, Metodi, TempConnex, TempFin, TempRaw, Dst, DatiPressione, Condt, Flusco, Rivest, Deviazione, Mineralizzazioni
)

router = APIRouter(prefix="/pozzi", tags=["Pozzi"])



# DATABASE SESSION

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# HELPER: decodifica vocabolari

def get_descrizione(db, modello, colonna, valore):
    if valore is None:
        return None
    row = db.query(modello).filter(colonna == valore).first()
    return row.descrizione if row else None



# HELPER: query base con join sicuri
class QueryBuilder:
    """Gestisce la query su Pozzo evitando join duplicati."""
    def __init__(self, db):
        self.q = db.query(Pozzo)
        self._join_fatti = set()

    def join(self, modello, cond, nome):
        if nome not in self._join_fatti:
            self.q = self.q.join(modello, cond)
            self._join_fatti.add(nome)

    def filter(self, *args, **kwargs):
        self.q = self.q.filter(*args, **kwargs)

    def get(self):
        return self.q


# CAMPI CATEGORICI (GROUP BY)

CAMPI = {
    "regione":   (Regioni,  Pozzo.reg   == Regioni.reg,   Regioni.reg,   "regioni"),
    "provincia": (Province, Pozzo.prov  == Province.prov,  Province.prov,  "province"),
    "comune":    (Comuni,   Pozzo.istat == Comuni.istat,   Comuni.istat,    "comuni"),
    "tipo":      (Tipi,     Pozzo.tipo  == Tipi.tipo,      Tipi.descrizione, "tipi"),
    "stato":     (Stato,    Pozzo.stato == Stato.stato,    Stato.descrizione, "stati"),
    "uso":       (Usi,      Pozzo.uso   == Usi.uso,        Usi.descrizione,  "usi"),
    "scopo":     (Scopi,    Pozzo.scopo == Scopi.scopo,    Scopi.descrizione, "scopi"),
    "esito":     (Esiti,    Pozzo.esitom == Esiti.esitom,  Esiti.descrizione, "esiti"),
    "inn":       (Inn,      Pozzo.inn   == Inn.inn,        Inn.descrizione,   "inn")
}



# METRICHE NUMERICHE

METRICHE = {
    "profondita_media": (func.avg(Pozzo.prof),  "pozzo"),
    "profondita_min":   (func.min(Pozzo.prof),  "pozzo"),
    "profondita_max":   (func.max(Pozzo.prof),  "pozzo"),
    "temperatura_media": (func.avg(TempFin.temp),  "temp"),
    "temperatura_min":   (func.min(TempFin.temp),  "temp"),
    "temperatura_max":   (func.max(TempFin.temp),  "temp"),
    "gradiente_medio":  (func.avg(Grados.grad), "grados"),
    "gradiente_min":    (func.min(Grados.grad), "grados"),
    "gradiente_max":    (func.max(Grados.grad), "grados"),
}



#  ENDPOINT MAPPA
# Restituisce i pozzi con coordinate per la visualizzazione
# sulla mappa, con filtri opzionali sugli slider della dashboard.
#
# Uso:
#   GET /pozzi/mappa
#   GET /pozzi/mappa?regione=Toscana
#   GET /pozzi/mappa?prof_min=1000&prof_max=3000
#   GET /pozzi/mappa?temp_min=50&tipo=Geotermico

@router.get("/mappa", summary="Pozzi per la mappa con filtri opzionali")
def mappa_pozzi(
    # filtri geografici
    regione: int | None = Query(default=None, description="Codice regione"),
    provincia: int | None = Query(default=None, description="Codice provincia"),

    # filtri classificazione (ID)
    tipo: int | None = Query(default=None, description="Codice tipo pozzo"),
    scopo: int | None = Query(default=None, description="Codice scopo"),
    stato: int | None = Query(default=None, description="Codice stato"),


    # filtri numerici — slider dashboard
    prof_min:  float | None = Query(default=None, description="Profondità minima (m)"),
    prof_max:  float | None = Query(default=None, description="Profondità massima (m)"),
    temp_min:  float | None = Query(default=None, description="Temperatura minima (°C)"),
    temp_max:  float | None = Query(default=None, description="Temperatura massima (°C)"),

    limit: int = Query(default=1000, le=5000, description="Max risultati"),
    db: Session = Depends(get_db)
    #oggetto user
):
    qb = QueryBuilder(db)

    if regione is not None:
        qb.filter(Pozzo.reg == regione)

    if provincia is not None:
        qb.filter(Pozzo.prov == provincia)

    if tipo is not None:
        qb.filter(Pozzo.tipo == tipo)

    if scopo is not None:
        qb.filter(Pozzo.scopo == scopo)

    if stato is not None:
        qb.filter(Pozzo.stato == stato)

    if prof_min is not None:
        qb.filter(Pozzo.prof >= prof_min)
    if prof_max is not None:
        qb.filter(Pozzo.prof <= prof_max)

    if temp_min is not None or temp_max is not None:
        qb.join(TempFin, Pozzo.key == TempFin.key, "temp")
        if temp_min is not None:
            qb.filter(TempFin.temp >= temp_min)
        if temp_max is not None:
            qb.filter(TempFin.temp <= temp_max)

    risultati = (
        qb.get()
        .filter(Pozzo.lat_.isnot(None), Pozzo.lon_.isnot(None))
        .limit(limit)
        .all()
    )

    # temperatura massima per pozzo — dizionario key -> temp_max
    # estrae i key dei pozzi già trovati dalla query principale
    keys = [p.key for p in risultati] 
    temp_map = {
        row[0]: row[1]
        for row in db.query(TempFin.key, func.max(TempFin.temp)) #estrae la massima
        .filter(TempFin.key.in_(keys))
        .group_by(TempFin.key)# raggruppa per pozzo
        .all()
    }

    return [
        {
            "key":        p.key,
            "nome":       p.nome,
            "lat":        p.lat_,
            "lon":        p.lon_,
            "profondita": p.prof,
            "quota":      p.quota,
            "temp_max":   round(temp_map[p.key], 2) if p.key in temp_map else None,
        }
        for p in risultati
    ]



# ENDPOINT DISTRIBUZIONE
# Statistiche aggregate sui pozzi per categoria o metrica.
#
# Uso:
#   GET /pozzi/distribuzione?campo=tipo
#   GET /pozzi/distribuzione?campo=regione
#   GET /pozzi/distribuzione?campo=profondita_media&modalita=metrica
#   GET /pozzi/distribuzione?campo=tipo&regione=Toscana

@router.get("/distribuzione", summary="Distribuzione pozzi per categoria o metrica")
def distribuzione(
    campo: str = Query(..., description=(
        "Categoria: regione, provincia, comune, tipo, stato, uso, scopo, esito, inn | "
        "Metrica: profondita_media/min/max, temperatura_media/min/max, gradiente_medio/min/max"
    )),
    modalita: str = Query(default="categoria", description="categoria | metrica | boxplot"),
    regione:   int | None = Query(default=None),
    provincia: int | None = Query(default=None),
    comune:    int | None = Query(default=None),
    key:       int | None = Query(default=None, description="Key pozzo per localizzarlo nel box plot"),
    db: Session = Depends(get_db)
):
    qb = QueryBuilder(db)

    if regione is not None:
        qb.filter(Pozzo.reg == regione)

    if provincia is not None:
        qb.filter(Pozzo.prov == provincia)

    if comune:
        qb.filter(Pozzo.istat == comune)

    # --- modalità metrica ---
    if modalita == "metrica":
        if campo not in METRICHE:
            raise HTTPException(
                status_code=400,
                detail=f"Metrica non valida. Scegli tra: {', '.join(METRICHE.keys())}"
            )

        metrica, tabella = METRICHE[campo]

        if tabella == "temp":
            qb.join(TempFin, Pozzo.key == TempFin.key, "temp")
        elif tabella == "grados":
            qb.join(Grados, Pozzo.key == Grados.key, "grados")

        valore = qb.get().with_entities(metrica).scalar()
        return {
            "modalita": "metrica",
            "campo": campo,
            "valore": round(valore, 2) if valore is not None else None
        }

    # --- modalità boxplot ---
    if modalita == "boxplot":

        BOXPLOT_CAMPI = {
            "temperatura": (TempFin,   TempFin.temp,   TempFin.key,   Pozzo.key),
            "profondita":  (None,   Pozzo.prof,  None,       None),
            "gradiente":   (Grados, Grados.grad, Grados.key, Pozzo.key),
        }

        if campo not in BOXPLOT_CAMPI:
            raise HTTPException(
                status_code=400,
                detail=f"Campo non valido per boxplot. Scegli tra: {', '.join(BOXPLOT_CAMPI.keys())}"
            )

        tabella, colonna, fk_col, pozzo_col = BOXPLOT_CAMPI[campo]

        if tabella is not None:
            qb.join(tabella, fk_col == pozzo_col, str(tabella.__tablename__))
            q = qb.get().with_entities(colonna)
        else:
            q = qb.get().with_entities(colonna)

        valori = [v[0] for v in q.all() if v[0] is not None]

        if not valori:
            raise HTTPException(status_code=404, detail="Nessun dato disponibile")

        valori_sorted = sorted(valori)
        n = len(valori_sorted)

        def percentile(data, p):
            idx = (len(data) - 1) * p / 100
            lower = int(idx)
            upper = lower + 1
            if upper >= len(data):
                return data[-1]
            return data[lower] + (data[upper] - data[lower]) * (idx - lower)

        q1      = percentile(valori_sorted, 25)
        mediana = percentile(valori_sorted, 50)
        q3      = percentile(valori_sorted, 75)

        risultato = {
            "modalita": "boxplot",
            "campo":    campo,
            "min":      round(valori_sorted[0], 2),
            "q1":       round(q1, 2),
            "mediana":  round(mediana, 2),
            "q3":       round(q3, 2),
            "max":      round(valori_sorted[-1], 2),
            "media":    round(sum(valori) / n, 2),
            "n":        n,
        }

        if key is not None:
            if tabella is not None:
                valore_pozzo = (
                    db.query(colonna)
                    .filter(fk_col == key)
                    .order_by(colonna.desc())
                    .first()
                )
                valore_pozzo = valore_pozzo[0] if valore_pozzo else None
            else:
                p = db.query(Pozzo).filter(Pozzo.key == key).first()
                valore_pozzo = getattr(p, campo, None) if p else None

            if valore_pozzo is not None:
                posizione = sum(1 for v in valori_sorted if v <= valore_pozzo)
                percentile_pozzo = round((posizione / n) * 100, 1)
                risultato["pozzo"] = {
                    "key":         key,
                    "valore":      round(valore_pozzo, 2),
                    "percentile":  percentile_pozzo,
                    "sopra_media": valore_pozzo > (sum(valori) / n),
                }

        return risultato

    # --- modalità categoria ---
    if campo not in CAMPI:
        raise HTTPException(
            status_code=400,
            detail=f"Campo non valido. Scegli tra: {', '.join(CAMPI.keys())}"
        )

    modello, join_cond, colonna, join_nome = CAMPI[campo]
    qb.join(modello, join_cond, join_nome)

    totale = qb.get().count()

    results = (
        qb.get()
        .with_entities(colonna.label("gruppo"), func.count(Pozzo.key).label("conteggio"))
        .group_by(colonna)
        .order_by(func.count(Pozzo.key).desc())
        .all()
    )

    return [
        {
            "gruppo": nome,
            "conteggio": count,
            "percentuale": round((count / totale) * 100, 2) if totale else 0
        }
        for nome, count in results
    ]



# ENDPOINT CONFRONTO
# Dettaglio di uno o più pozzi affiancati.


@router.get("/confronto", summary="Dettaglio e confronto di uno o più pozzi")
def confronto_pozzi(
    key: List[int] = Query(..., description="Uno o più key di pozzi da confrontare"),
    db: Session = Depends(get_db)
):
    if len(key) > 10:
        raise HTTPException(status_code=400, detail="Massimo 10 pozzi per confronto")

    risultati = []

    for k in key:
        pozzo = db.query(Pozzo).filter(Pozzo.key == k).first()
        if not pozzo:
            raise HTTPException(status_code=404, detail=f"Pozzo {k} non trovato")

        # posizione geografica
        regione  = db.query(Regioni).filter(Regioni.reg == pozzo.reg).first()
        provincia = db.query(Province).filter(Province.prov == pozzo.prov).first()
        comune   = db.query(Comuni).filter(Comuni.istat == pozzo.istat).first()

        # trova id_dst
        dst_records = (db.query(Dst).filter(Dst.key == k).all())

        # temperature ordinate per profondità
        temperature = (
            db.query(TempFin)
            .filter(TempFin.key == k)
            .order_by(TempFin.prof)
            .all()
        )


        # litologia
        litologie = (
            db.query(Litologia)
            .filter(Litologia.key == k)
            .order_by(Litologia.daprof)
            .all()
        )

        # gradiente geotermico
        gradienti = (
            db.query(Grados)
            .filter(Grados.key == k)
            .order_by(Grados.daprof)
            .all()
        )

        # temperatura massima (per scatter plot e KPI)
        temp_max = (
            db.query(func.max(TempFin.temp))
            .filter(TempFin.key == k)
            .scalar()
        )

        # gradiente medio (per KPI)
        grad_medio = (
            db.query(func.avg(Grados.grad))
            .filter(Grados.key == k)
            .scalar()
        )

        

        risultati.append({
            "anagrafica": {
                "key":        pozzo.key,
                "nome":       pozzo.nome,
                "proprietar": pozzo.proprietar,
                "datacomp":   pozzo.datacomp,
                "prof":       pozzo.prof,
                "quota":      pozzo.quota,
                "entitam":    pozzo.entitam,
                "camploc":    pozzo.camploc,
                "locgeo":     pozzo.locgeo,
            },
            "posizione": {
                "lat":       pozzo.lat_,
                "lon":       pozzo.lon_,
                "regione":   regione.nome   if regione   else None,
                "provincia": provincia.nome if provincia else None,
                "comune":    comune.nome    if comune    else None,
            },
            "classificazione": {
                "tipo":  get_descrizione(db, Tipi,  Tipi.tipo,    pozzo.tipo),
                "scopo": get_descrizione(db, Scopi, Scopi.scopo,  pozzo.scopo),
                "uso":   get_descrizione(db, Usi,   Usi.uso,      pozzo.uso),
                "stato": get_descrizione(db, Stato, Stato.stato,  pozzo.stato),
                "esito": get_descrizione(db, Esiti, Esiti.esitom, pozzo.esitom),
            },
            "kpi": {
                "temp_max":    round(temp_max, 2)   if temp_max   else None,
                "grad_medio":  round(grad_medio, 2) if grad_medio else None,
                "prof_max":    pozzo.prof,
            },
            "temperatura_vs_profondita": [
                {"prof": t.prof, "temp": t.temp}
                for t in temperature
            ],
            "litologia": [
                {"da": l.daprof, "a": l.aprof, "litologia": l.litologia}
                for l in litologie
            ],
            "dst": [
                {
                    "id_dst": d.id_dst,
                    "top": d.top,
                    "bottom": d.bottom,
                    "prof_misura": d.prof_misura,
                    "note": d.note,
                    "pressioni": [
                        {
                            "fase": p.fase_prova,
                            "press_fondo": p.press_fondo,
                            "ore": p.ore,
                            "minuti": p.minuti
                        }
                        for p in db.query(DatiPressione)
                            .filter(DatiPressione.id_dst == d.id_dst)
                            .order_by(DatiPressione.ore, DatiPressione.minuti)
                            .all()
                    ]
                }
                for d in dst_records
            ],
            "gradiente_geotermico": [
                {"da": g.daprof, "a": g.aprof, "grad": g.grad, "condm": g.condm}
                for g in gradienti
            ]
        })

    return risultati

### ENDPOINT DISPONIBILITA

@router.get("/{key}/disponibilita")
def disponibilita(key: int, db: Session = Depends(get_db)):

    pozzo = db.query(Pozzo).filter(Pozzo.key == key).first()
    if not pozzo:
        raise HTTPException(status_code=404, detail="Pozzo non trovato")

    return {
        "temperatura": (
            db.query(TempFin).filter(TempFin.key == key).first() is not None or
            db.query(Temp).filter(Temp.key == key).first() is not None
        ),
        # "temperatura":      db.query(TempFin).filter(TempFin.key == key).first() is not None,
        "litologia":        db.query(Litologia).filter(Litologia.key == key).first() is not None,
        "gradiente":        db.query(Grados).filter(Grados.key == key).first() is not None,
        "conduttivita":     db.query(Condt).filter(Condt.key == key).first() is not None,
        "flusso_calore":    db.query(Flusco).filter(Flusco.key == key).first() is not None,
        "rivestimento":     db.query(Rivest).filter(Rivest.key == key).first() is not None,
        "mineralizzazioni": db.query(Mineralizzazioni).filter(Mineralizzazioni.key == key).first() is not None,
        "dst":              db.query(Dst).filter(Dst.key == key).first() is not None,
        "deviazione":       db.query(Deviazione).filter(Deviazione.key == key).first() is not None,
    }


# ENDPOINT DETTAGLIO SINGOLO POZZO
"""
@router.get("/{key}", summary="Dettaglio completo di un singolo pozzo")
def dettaglio_pozzo(key: int, db: Session = Depends(get_db)):

    pozzo = db.query(Pozzo).filter(Pozzo.key == key).first()
    if not pozzo:
        raise HTTPException(status_code=404, detail=f"Pozzo {key} non trovato")

    regione   = db.query(Regioni).filter(Regioni.reg == pozzo.reg).first()
    provincia = db.query(Province).filter(Province.prov == pozzo.prov).first()
    comune    = db.query(Comuni).filter(Comuni.istat == pozzo.istat).first()
    coord     = db.query(WellCoord).filter(WellCoord.key == key).first()

    temperature = (
        db.query(TempFin).filter(TempFin.key == key).order_by(TempFin.prof).all()
    )
    litologie = (
        db.query(Litologia).filter(Litologia.key == key).order_by(Litologia.daprof).all()
    )
    gradienti = (
        db.query(Grados).filter(Grados.key == key).order_by(Grados.daprof).all()
    )

    dati_pressione = (
         db.query(Dst).filter(Dst.key == key)
    )

    return {
        "anagrafica": {
            "key":        pozzo.key,
            "nome":       pozzo.nome,
            "proprietar": pozzo.proprietar,
            "datacomp":   pozzo.datacomp,
            "prof":       pozzo.prof,
            "quota":      pozzo.quota,
            "entitam":    pozzo.entitam,
            "camploc":    pozzo.camploc,
            "locgeo":     pozzo.locgeo,
        },
        "posizione": {
            "lat":       pozzo.lat_,
            "lon":       pozzo.lon_,
            "regione":   regione.nome   if regione   else None,
            "provincia": provincia.nome if provincia else None,
            "comune":    comune.nome    if comune    else None,
        },
        "classificazione": {
            "tipo":  get_descrizione(db, Tipi,  Tipi.tipo,    pozzo.tipo),
            "scopo": get_descrizione(db, Scopi, Scopi.scopo,  pozzo.scopo),
            "uso":   get_descrizione(db, Usi,   Usi.uso,      pozzo.uso),
            "stato": get_descrizione(db, Stato, Stato.stato,  pozzo.stato),
            "esito": get_descrizione(db, Esiti, Esiti.esitom, pozzo.esitom),
        },
        "temperature": [
            {
                "data":   t.data,
                "prof":   t.prof,
                "temp":   t.temp,
                "tcirc":  t.tcirc,
                #"tstop":  t.tstop,
                #"metodo": get_descrizione(db, Metodi, Metodi.tipo_metodo, t.metodo),
                "metodo": get_descrizione(db, Metodi, Metodi.tipo_metodo),
            }
            for t in temperature
        ],
        "litologia": [
            {"da": l.daprof, "a": l.aprof, "litologia": l.litologia}
            for l in litologie
        ],
        "gradiente_geotermico": [
            {"da": g.daprof, "a": g.aprof, "grad": g.grad, "condm": g.condm}
            for g in gradienti
        ],
        "dati_pressione": [
            {"da": dp.bottom, "a": dp.top}
            for dp in dati_pressione
        ],
        "coordinate_sistemi_riferimento": {
            "lat_wgs84": coord.lat    if coord else None,
            "lon_wgs84": coord.lon    if coord else None,
            "lat_gd":    coord.lat_gd if coord else None,
            "lon_gd":    coord.lon_gd if coord else None,
        } if coord else None,
    }
"""