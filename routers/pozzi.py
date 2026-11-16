from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from fastapi import status

from database import SessionLocal
from models import (
    Pozzo, Tipi, Stato, Usi, Scopi, Esiti, Inn,
    Regioni, Province, Comuni, Temp, Grados,
    Litologia, WellCoord, Metodi, TempConnex, TempFin, TempRaw, Dst, DatiPressione, Condt, Flusco, Rivest, Deviazione, Mineralizzazioni, FluidoT, LitologiaStandard
)
from routers.auth import require_esperto, require_base

router = APIRouter(prefix="/pozzi", tags=["Pozzi"])
# ============================================================
# ANALISI GEOLOGICA INTEGRATA (LitologiaStandard × Grados)
# ============================================================

CARBONATICI  = ['CALCARE', 'DOLOMIA', 'MARNA', 'MUDSTONE', 'WACKESTONE', 'PACKSTONE']
CLASTICI     = ['ARGILLA', 'SABBIA', 'ARENARIA', 'ALLUVIONE']
EVAPORITICI  = ['ANIDRITE', 'GESSO', 'SALGEMMA']
PERMEABILI   = ['CALCARE', 'DOLOMIA', 'ARENARIA', 'WACKESTONE', 'PACKSTONE']



# DATABASE SESSION

"""
def calcola_gradiente_da_profilo(temperatures):
    
    if not temperatures or len(temperatures) < 2:
        return None
    
    t_inizio = temperatures[0]  # (prof, temp)
    t_fine = temperatures[-1]
    
    delta_prof = t_fine['prof'] - t_inizio['prof']
    delta_temp = t_fine['temp'] - t_inizio['temp']
    
    if delta_prof == 0:
        return None
    
    # Gradiente in °C/km
    return (delta_temp / delta_prof) * 1000
"""

TEMPERATURA_SUPERFICIE_ITALIA = 15.0  # °C — media annua dell'aria in Italia (letteratura geotermica)

def calcola_gradiente_da_profilo(temperatures, temp_superficie=TEMPERATURA_SUPERFICIE_ITALIA):
    """
    Calcola il gradiente geotermico usando come riferimento a profondità
    zero la temperatura media annua dell'aria esterna (in assenza di una
    misura reale vicino alla superficie), e la misura più profonda
    disponibile per il pozzo.

    Questo permette di calcolare un gradiente anche con una SOLA misura
    di temperatura in pozzo (caso frequente nel dataset), a differenza
    del metodo precedente che richiedeva almeno due punti misurati.
    """
    if not temperatures:
        return None

    # punto più profondo disponibile
    t_fondo = max(temperatures, key=lambda t: t['prof'])

    if t_fondo['prof'] <= 0:
        return None  # non ha senso calcolare un gradiente a profondità 0

    delta_temp = t_fondo['temp'] - temp_superficie
    return (delta_temp / t_fondo['prof']) * 1000

def _calcola_gradiente_sicuro(key, grad_map, profili_termici):
    """Ritorna il gradiente arrotondato, o None se non calcolabile in alcun modo."""
    if key in grad_map:
        return round(grad_map[key], 2)

    profilo = profili_termici.get(key)
    if not profilo:
        return None

    gradiente = calcola_gradiente_da_profilo(profilo)
    if gradiente is None:
        return None

    return round(gradiente, 2)

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

#diagnostica

# Aggiungi questo endpoint per diagnostica:
@router.get("/diagnostica/gradiente")
def diagnostica_gradiente(db: Session = Depends(get_db)):
    total_pozzi = db.query(Pozzo).count()
    pozzi_con_grados = db.query(func.count(func.distinct(Grados.key))).scalar()
    pozzi_con_tempfin = db.query(func.count(func.distinct(TempFin.key))).scalar()
    
    return {
        "total_pozzi": total_pozzi,
        "con_gradiente": pozzi_con_grados,
        "con_temperatura": pozzi_con_tempfin,
        "percentuale_grados": round((pozzi_con_grados / total_pozzi * 100), 1) if total_pozzi else 0,
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
    db: Session = Depends(get_db),
    #current_user = Depends(require_base)
    #oggetto user
):
    #costruisco query
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

    # Join con WellCoord per le coordinate corrette
    from sqlalchemy.orm import joinedload

    risultati = (
        qb.get()
        .filter(Pozzo.lat_.isnot(None), Pozzo.lon_.isnot(None))
        .limit(limit)
        .all()
    )

    # Prendi le temperature
    keys = [p.key for p in risultati]
    temp_map = {
        row[0]: row[1]
        for row in db.query(TempFin.key, func.max(TempFin.temp))
        .filter(TempFin.key.in_(keys))
        .group_by(TempFin.key)
        .all()
    }

    from sqlalchemy import text

    # Dopo aver ottenuto risultati e keys...

    geom_map = {
        row[0]: (row[1], row[2])
        for row in db.execute(
            text("""
                SELECT key, ST_Y(the_geom) as lat, ST_X(the_geom) as lon
                FROM public.pozzi
                WHERE key = ANY(:keys) AND the_geom IS NOT NULL
            """),
            {"keys": keys}
        ).all()
    }

    # Prendi il gradiente medio per pozzo
    grad_map = {
        row[0]: row[1]
        for row in db.query(Grados.key, func.avg(Grados.grad))
        .filter(Grados.key.in_(keys))
        .group_by(Grados.key)
        .all()
    }
    #aggiunta questa parte:
    # Prendi il profilo termico completo per ogni pozzo
    profili_termici = {}
    for k in keys:
        profilo = (
            db.query(TempFin.prof, TempFin.temp)
            .filter(TempFin.key == k)
            .order_by(TempFin.prof)
            .all()
        )
        if profilo:
            profili_termici[k] = [
                {"prof": p[0], "temp": p[1]} for p in profilo
            ]
    
    # Prendi i gradienti già calcolati (fallback)
    grad_map = {
        row[0]: row[1]
        for row in db.query(Grados.key, func.avg(Grados.grad))
        .filter(Grados.key.in_(keys))
        .group_by(Grados.key)
        .all()
    }
    
    # Ritorna con gradiente calcolato se manca
    return [
        {
            "key": p.key,
            "nome": p.nome,
            "lat": geom_map[p.key][0] if p.key in geom_map else p.lat_,
            "lon": geom_map[p.key][1] if p.key in geom_map else p.lon_,
            "profondita": p.prof,
            "quota": p.quota,
            "temp_max": round(temp_map[p.key], 2) if p.key in temp_map else None,
            "gradiente": _calcola_gradiente_sicuro(p.key, grad_map, profili_termici),
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

@router.get("/mappa/avanzata", summary="Mappa con filtri avanzati (litologia + mineralizzazione)")
def mappa_avanzata(
    tipo_fluido: List[int] = Query(default=[]),
    prof_min: float | None = Query(default=None, description="Profondità minima evento (m)"),
    prof_max: float | None = Query(default=None, description="Profondità massima evento (m)"),
    termine_lito: List[str] = Query(default=[], description="Termini litologici standardizzati"),
    ruolo: str = Query(default='tutte'),
    limit: int = Query(default=1000, le=5000, description="Max risultati"),
    db: Session = Depends(get_db),
):
    """
    Ritorna pozzi filtrati per mineralizzazioni e litologie.
    
    Logica:
    - Se mineralizzazione + ruolo: conta pozzi dove l'evento mineralizzazione
      si verifica DENTRO uno strato di litologia con quel ruolo (overlap spaziale)
    - Se solo ruolo (senza mineralizzazione): conta pozzi con litologie di quel ruolo
    - Se mineralizzazione + litologie: conta pozzi dove evento è dentro quella litologia
    """
    
    # Se nessun filtro, ritorna vuoto
    if len(tipo_fluido) == 0 and len(termine_lito) == 0 and ruolo == 'tutte':
        return []
    
    subquery = db.query(func.distinct(Pozzo.key)).filter(
        Pozzo.lat_.isnot(None),
        Pozzo.lon_.isnot(None)
    )
    
    # ========== CASO 1: MINERALIZZAZIONE + RUOLO (overlap spaziale) ==========
    if len(tipo_fluido) > 0 and ruolo != 'tutte' and len(termine_lito) == 0:
        """
        Cerca pozzi dove l'evento di mineralizzazione cade dentro
        uno strato di litologia con quel ruolo.
        """
        subquery = subquery.join(Mineralizzazioni, Pozzo.key == Mineralizzazioni.key)
        subquery = subquery.join(
            LitologiaStandard,
            (LitologiaStandard.key == Mineralizzazioni.key) &
            (LitologiaStandard.daprof < Mineralizzazioni.bottom) &  # overlap
            (LitologiaStandard.aprof > Mineralizzazioni.top)         # overlap
        )
        
        subquery = subquery.filter(Mineralizzazioni.tipo_fluido.in_(tipo_fluido))
        subquery = subquery.filter(LitologiaStandard.ruolo == ruolo)
        
        if prof_min is not None:
            subquery = subquery.filter(Mineralizzazioni.top >= prof_min)
        if prof_max is not None:
            subquery = subquery.filter(Mineralizzazioni.bottom <= prof_max)
    
    # ========== CASO 2: MINERALIZZAZIONE + LITOLOGIE ==========
    elif len(tipo_fluido) > 0 and len(termine_lito) > 0:
        """
        Cerca pozzi dove l'evento di mineralizzazione cade dentro
        uno strato delle litologie selezionate.
        """
        subquery = subquery.join(Mineralizzazioni, Pozzo.key == Mineralizzazioni.key)
        subquery = subquery.join(
            LitologiaStandard,
            (LitologiaStandard.key == Mineralizzazioni.key) &
            (LitologiaStandard.daprof < Mineralizzazioni.bottom) &
            (LitologiaStandard.aprof > Mineralizzazioni.top)
        )
        
        subquery = subquery.filter(Mineralizzazioni.tipo_fluido.in_(tipo_fluido))
        subquery = subquery.filter(LitologiaStandard.litologia_standard.in_(termine_lito))
        
        if ruolo != 'tutte':
            subquery = subquery.filter(LitologiaStandard.ruolo == ruolo)
        
        if prof_min is not None:
            subquery = subquery.filter(Mineralizzazioni.top >= prof_min)
        if prof_max is not None:
            subquery = subquery.filter(Mineralizzazioni.bottom <= prof_max)
    
    # ========== CASO 3: MINERALIZZAZIONE SOLO (senza litologia) ==========
    elif len(tipo_fluido) > 0:
        """
        Cerca pozzi con la mineralizzazione selezionata.
        """
        subquery = subquery.join(Mineralizzazioni, Pozzo.key == Mineralizzazioni.key)
        subquery = subquery.filter(Mineralizzazioni.tipo_fluido.in_(tipo_fluido))
        
        if prof_min is not None:
            subquery = subquery.filter(Mineralizzazioni.top >= prof_min)
        if prof_max is not None:
            subquery = subquery.filter(Mineralizzazioni.bottom <= prof_max)
    
    # ========== CASO 4: LITOLOGIE + RUOLO (senza mineralizzazione) ==========
    elif len(termine_lito) > 0 or ruolo != 'tutte':
        """
        Cerca pozzi con le litologie selezionate.
        """
        subquery = subquery.join(LitologiaStandard, Pozzo.key == LitologiaStandard.key)
        
        if len(termine_lito) > 0:
            subquery = subquery.filter(LitologiaStandard.litologia_standard.in_(termine_lito))
        
        if ruolo != 'tutte':
            subquery = subquery.filter(LitologiaStandard.ruolo == ruolo)
        if prof_min is not None:
            subquery = subquery.filter(LitologiaStandard.daprof >= prof_min)
        if prof_max is not None:
            subquery = subquery.filter(LitologiaStandard.aprof <= prof_max)
    # ========== ESTRAI I KEY ==========
    keys = [row[0] for row in subquery.all()]
    print(f' Mappa avanzata: {len(keys)} pozzi trovati')
    
    if not keys:
        return []
    
    # ========== QUERY PULITA SU POZZO ==========
    risultati = db.query(Pozzo).filter(Pozzo.key.in_(keys)).limit(limit).all()
    
    # ========== ESTRAI COORDINATE DA the_geom (PostGIS) ==========
    from sqlalchemy import text
    
    geom_map = {
        row[0]: (row[1], row[2])
        for row in db.execute(
            text("""
                SELECT key, 
                       ST_Y(the_geom) as lat, 
                       ST_X(the_geom) as lon
                FROM public.pozzi
                WHERE key = ANY(:keys) 
                  AND the_geom IS NOT NULL
            """),
            {"keys": keys}
        ).all()
    }
    
    # ========== ESTRAI TEMPERATURE ==========
    temp_map = {
        row[0]: row[1]
        for row in db.query(TempFin.key, func.max(TempFin.temp))
        .filter(TempFin.key.in_(keys))
        .group_by(TempFin.key)
        .all()
    }
    
    # ========== ESTRAI GRADIENTI ==========
    grad_map = {
        row[0]: row[1]
        for row in db.query(Grados.key, func.avg(Grados.grad))
        .filter(Grados.key.in_(keys))
        .group_by(Grados.key)
        .all()
    }
    
    
    # Se un pozzo non ha gradiente in Grados, calcola da TempFin
    if len(grad_map) < len(keys):
        for k in keys:
            if k not in grad_map:
                profile = (
                    db.query(TempFin.prof, TempFin.temp)
                    .filter(TempFin.key == k)
                    .order_by(TempFin.prof)
                    .all()
                )
                
                if profile and len(profile) >= 2:
                    p1_prof, p1_temp = profile[0]
                    p2_prof, p2_temp = profile[-1]
                    delta_prof = p2_prof - p1_prof
                    delta_temp = p2_temp - p1_temp
                    
                    if delta_prof > 0:
                        grad = (delta_temp / delta_prof) * 1000  # °C/km
                        grad_map[k] = grad
    
    # ========== RITORNA RISULTATI ==========
    return [
        {
            "key":        p.key,
            "nome":       p.nome,
            "lat":        geom_map[p.key][0] if p.key in geom_map else p.lat_,
            "lon":        geom_map[p.key][1] if p.key in geom_map else p.lon_,
            "profondita": p.prof,
            "quota":      p.quota,
            "temp_max":   round(temp_map[p.key], 2) if p.key in temp_map else None,
            "gradiente":  round(grad_map[p.key], 2) if p.key in grad_map else None,
        }
        for p in risultati
    ]


from routers.auth import get_current_user_optional

@router.get("/confronto", summary="Dettaglio e confronto di uno o più pozzi")
def confronto_pozzi(
    key: List[int] = Query(..., description="Uno o più key di pozzi da confrontare"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional),
):
    if len(key) > 10:
        raise HTTPException(status_code=400, detail="Massimo 10 pozzi per confronto")

    # Il confronto tra PIÙ pozzi è riservato agli utenti esperti autenticati.
    # Il dettaglio di un SINGOLO pozzo resta accessibile a tutti.
    if len(key) > 1:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login richiesto per confrontare più pozzi"
            )
        if current_user.ruolo != "esperto":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Il confronto tra pozzi è riservato agli utenti esperti"
            )

    risultati = []

    for k in key:
        pozzo = db.query(Pozzo).filter(Pozzo.key == k).first()
        if not pozzo:
            raise HTTPException(status_code=404, detail=f"Pozzo {k} non trovato")

        # posizione geografica
        regione  = db.query(Regioni).filter(Regioni.reg == pozzo.reg).first()
        provincia = db.query(Province).filter(Province.prov == pozzo.prov).first()
        comune   = db.query(Comuni).filter(Comuni.istat == pozzo.istat).first()

        dst_records = (db.query(Dst).filter(Dst.key == k).all())

        temperature = (
            db.query(TempFin)
            .filter(TempFin.key == k)
            .order_by(TempFin.prof)
            .all()
        )

        litologie = (
            db.query(Litologia)
            .filter(Litologia.key == k)
            .order_by(Litologia.daprof)
            .all()
        )

        gradienti = (
            db.query(Grados)
            .filter(Grados.key == k)
            .order_by(Grados.daprof)
            .all()
        )

        temp_max = (
            db.query(func.max(TempFin.temp))
            .filter(TempFin.key == k)
            .scalar()
        )

        """grad_medio = (
            db.query(func.avg(Grados.grad))
            .filter(Grados.key == k)
            .scalar()
        )"""
        # gradiente medio — prima prova Grados, poi calcola dal profilo termico
        grad_medio = (
            db.query(func.avg(Grados.grad))
            .filter(Grados.key == k)
            .scalar()
        )

        if grad_medio is None:
            profilo_per_gradiente = [
                {"prof": t.prof, "temp": t.temp} for t in temperature
            ]
            grad_medio = calcola_gradiente_da_profilo(profilo_per_gradiente)

        litologie_std = (
            db.query(LitologiaStandard)
            .filter(LitologiaStandard.key == k)
            .order_by(LitologiaStandard.daprof)
            .all()
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
                "temp_max":    round(temp_max, 2)   if temp_max is not None   else None,
                "grad_medio":  round(grad_medio, 2) if grad_medio is not None else None,
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
            ],
            "litologia_standard": [
                {
                    "da": l.daprof,
                    "a":  l.aprof,
                    "litologia": l.litologia_standard,
                    "ruolo": l.ruolo,
                    "relazione": l.relazione
                }
                for l in litologie_std
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


### NUOVI ENDPOINT PER LA MINERALIZZAZIONE

# ==================================================
# ENDPOINT MINERALIZZAZIONI
# Filtro avanzato per tipo di fluido e profondità.
# Accessibile solo agli utenti esperti.
#
# Uso:
#   GET /pozzi/mineralizzazioni
#   GET /pozzi/mineralizzazioni?tipo_fluido=3
#   GET /pozzi/mineralizzazioni?tipo_fluido=5&prof_min=500&prof_max=2000
#   GET /pozzi/mineralizzazioni?tipo_fluido=3&regione=12
# ==================================================
@router.get("/mineralizzazioni", summary="Filtro avanzato mineralizzazioni (solo esperti)")
def mineralizzazioni(
    tipo_fluido: int | None = Query(default=None, description="Codice tipo fluido (es. 3=acqua salata, 5=gas)"),
    prof_min:    float | None = Query(default=None, description="Profondità minima evento (m)"),
    prof_max:    float | None = Query(default=None, description="Profondità massima evento (m)"),
    regione:     int | None = Query(default=None, description="Codice regione"),
    limit:       int = Query(default=200, le=1000),
    db: Session = Depends(get_db),
    #current_user = Depends(require_esperto)
):
    """
    Restituisce i pozzi che hanno mineralizzazioni corrispondenti
    ai filtri selezionati. Ogni pozzo può avere più eventi di
    mineralizzazione a profondità diverse.
    """
    query = (
        db.query(
            Pozzo.key,
            Pozzo.nome,
            Pozzo.lat_,
            Pozzo.lon_,
            Pozzo.prof,
            Mineralizzazioni.top,
            Mineralizzazioni.bottom,
            Mineralizzazioni.tipo_fluido,
            FluidoT.descrizione.label("fluido_descrizione")
        )
        .join(Mineralizzazioni, Pozzo.key == Mineralizzazioni.key)
        .join(FluidoT, Mineralizzazioni.tipo_fluido == FluidoT.fluido_t)
        .filter(Pozzo.lat_.isnot(None), Pozzo.lon_.isnot(None))
    )
 
    if tipo_fluido is not None:
        query = query.filter(Mineralizzazioni.tipo_fluido == tipo_fluido)
 
    if prof_min is not None:
        query = query.filter(Mineralizzazioni.top >= prof_min)
 
    if prof_max is not None:
        query = query.filter(Mineralizzazioni.bottom <= prof_max)
 
    if regione is not None:
        query = query.filter(Pozzo.reg == regione)
 
    risultati = query.limit(limit).all()
 
    return [
        {
            "key":              r.key,
            "nome":             r.nome,
            "lat":              r.lat_,
            "lon":              r.lon_,
            "profondita_pozzo": r.prof,
            "top":              r.top,
            "bottom":           r.bottom,
            "tipo_fluido":      r.tipo_fluido,
            "fluido":           r.fluido_descrizione,
        }
        for r in risultati
    ]
 
 
# ==================================================
# ENDPOINT TIPI FLUIDO
# Restituisce la lista dei tipi di fluido disponibili
# con il conteggio degli eventi.
# Utile al frontend per popolare il selettore del filtro.
#
# Uso:
#   GET /pozzi/mineralizzazioni/tipi
# ==================================================
from typing import Optional
@router.get("/mineralizzazioni/tipi")
def tipi_fluido(
    ruolo: str = Query(default='tutte'),  # ← DEFAULT 'tutte'
    db: Session = Depends(get_db),
):
    print(f" tipi_fluido chiamato con ruolo={ruolo}")
    
    query = (
        db.query(
            FluidoT.fluido_t,
            FluidoT.descrizione,
            func.count(func.distinct(Mineralizzazioni.key)).label("n_eventi")
        )
        .join(Mineralizzazioni, FluidoT.fluido_t == Mineralizzazioni.tipo_fluido)
        .join(Pozzo, Pozzo.key == Mineralizzazioni.key)
    )
    
    if ruolo != 'tutte':  # ← Se NON è 'tutte', applica il filtro
        query = query.join(
            LitologiaStandard,
            (LitologiaStandard.key == Mineralizzazioni.key) &
            (LitologiaStandard.daprof < Mineralizzazioni.bottom) &
            (LitologiaStandard.aprof > Mineralizzazioni.top)
        )
        query = query.filter(LitologiaStandard.ruolo == ruolo)
    
    results = (
        query
        .group_by(FluidoT.fluido_t, FluidoT.descrizione)
        .order_by(func.count(Mineralizzazioni.oid).desc())
        .all()
    )

    return [
        {
            "codice": r.fluido_t,
            "fluido": r.descrizione,
            "n_eventi": r.n_eventi
        }
        for r in results
    ]


#gestione utente

"""bug primaria/secondaria
@router.get("/mineralizzazioni/cooccorrenza", summary="Matrice co-occorrenza fluido ↔ litologia standardizzata (solo esperti)")
def cooccorrenza(
    prof_min: float | None = Query(default=None, description="Profondità minima (m)"),
    prof_max: float | None = Query(default=None, description="Profondità massima (m)"),
    solo_primaria: bool = Query(default=False, description="..."),
    db: Session = Depends(get_db),
    current_user = Depends(require_esperto),   # <-- unico endpoint protetto
):
    query = (
        db.query(
            FluidoT.descrizione.label("fluido"),
            LitologiaStandard.litologia_standard.label("litologia"),
            func.count(func.distinct(Mineralizzazioni.key)).label("n_pozzi")
        )
        .join(Mineralizzazioni, FluidoT.fluido_t == Mineralizzazioni.tipo_fluido)
        .join(
            LitologiaStandard,
            (LitologiaStandard.key == Mineralizzazioni.key) &
            (LitologiaStandard.daprof < Mineralizzazioni.bottom) &
            (LitologiaStandard.aprof  > Mineralizzazioni.top)
        )
    )

    if solo_primaria:
        query = query.filter(LitologiaStandard.ruolo == "primaria")
    if prof_min is not None:
        query = query.filter(Mineralizzazioni.top >= prof_min)
    if prof_max is not None:
        query = query.filter(Mineralizzazioni.bottom <= prof_max)

    results = (
        query
        .group_by(FluidoT.descrizione, LitologiaStandard.litologia_standard)
        .order_by(func.count(func.distinct(Mineralizzazioni.key)).desc())
        .limit(100)
        .all()
    )

    return [{"fluido": r.fluido, "litologia": r.litologia, "n_pozzi": r.n_pozzi} for r in results]
"""
"""
@router.get("/mineralizzazioni/cooccorrenza", summary="Matrice co-occorrenza fluido ↔ litologia standardizzata (solo esperti)")
def cooccorrenza(
    prof_min: float | None = Query(default=None, description="Profondità minima (m)"),
    prof_max: float | None = Query(default=None, description="Profondità massima (m)"),
    ruolo: str = Query(default='tutte', description="tutte | primaria | subordinata"),
    db: Session = Depends(get_db),
    current_user = Depends(require_esperto),   # <-- unico endpoint protetto
):
    query = (
        db.query(
            FluidoT.descrizione.label("fluido"),
            LitologiaStandard.litologia_standard.label("litologia"),
            func.count(func.distinct(Mineralizzazioni.key)).label("n_pozzi")
        )
        .join(Mineralizzazioni, FluidoT.fluido_t == Mineralizzazioni.tipo_fluido)
        .join(
            LitologiaStandard,
            (LitologiaStandard.key == Mineralizzazioni.key) &
            (LitologiaStandard.daprof < Mineralizzazioni.bottom) &
            (LitologiaStandard.aprof  > Mineralizzazioni.top)
        )
    )

    if ruolo != 'tutte':
        query = query.filter(LitologiaStandard.ruolo == ruolo)
    if prof_min is not None:
        query = query.filter(Mineralizzazioni.top >= prof_min)
    if prof_max is not None:
        query = query.filter(Mineralizzazioni.bottom <= prof_max)
    results = (
        query
        .group_by(FluidoT.descrizione, LitologiaStandard.litologia_standard)
        .order_by(func.count(func.distinct(Mineralizzazioni.key)).desc())
        .limit(100)
        .all()
    )

    return [{"fluido": r.fluido, "litologia": r.litologia, "n_pozzi": r.n_pozzi} for r in results]
"""
@router.get("/mineralizzazioni/cooccorrenza", summary="Matrice co-occorrenza fluido ↔ litologia standardizzata (solo esperti)")
def cooccorrenza(
    prof_min: float | None = Query(default=None, description="Profondità minima (m)"),
    prof_max: float | None = Query(default=None, description="Profondità massima (m)"),
    ruolo: str = Query(default='tutte', description="tutte | primaria | subordinata"),
    db: Session = Depends(get_db),
    current_user = Depends(require_esperto),   # <-- unico endpoint protetto
):
    query = (
        db.query(
            FluidoT.descrizione.label("fluido"),
            LitologiaStandard.litologia_standard.label("litologia"),
            func.count(func.distinct(Mineralizzazioni.oid)).label("n_eventi")  # ← era .key / n_pozzi
        )
        .join(Mineralizzazioni, FluidoT.fluido_t == Mineralizzazioni.tipo_fluido)
        #.join(Pozzo, Pozzo.key == Mineralizzazioni.key)
        .join(
            LitologiaStandard,
            (LitologiaStandard.key == Mineralizzazioni.key) &
            (LitologiaStandard.daprof < Mineralizzazioni.bottom) &
            (LitologiaStandard.aprof  > Mineralizzazioni.top)
        )
    )

    if ruolo != 'tutte':
        query = query.filter(LitologiaStandard.ruolo == ruolo)
    if prof_min is not None:
        query = query.filter(Mineralizzazioni.top >= prof_min)
    if prof_max is not None:
        query = query.filter(Mineralizzazioni.bottom <= prof_max)

    results = (
        query
        .group_by(FluidoT.descrizione, LitologiaStandard.litologia_standard)
        .order_by(func.count(func.distinct(Mineralizzazioni.oid)).desc())  # ← era .key
        .limit(100)
        .all()
    )

    return [{"fluido": r.fluido, "litologia": r.litologia, "n_eventi": r.n_eventi} for r in results]  # ← era n_pozzi

@router.get("/litologie/termini", summary="Lista termini litologici standardizzati con conteggio")
def termini_litologici(
    prof_min: float | None = Query(default=None),
    prof_max: float | None = Query(default=None),
    ruolo: str | None = Query(default=None, description="primaria | subordinata | None = entrambi"),
    db: Session = Depends(get_db),
):
    # 1. Aggiungiamo il JOIN con InfoPozzi alla query base
    base_query = db.query(LitologiaStandard).join(
        Pozzo, 
        Pozzo.key == LitologiaStandard.key
    )
    # 1. Query base (senza group by) per i filtri
    #base_query = db.query(LitologiaStandard)
    if prof_min is not None:
        base_query = base_query.filter(LitologiaStandard.daprof >= prof_min)
    if prof_max is not None:
        base_query = base_query.filter(LitologiaStandard.aprof <= prof_max)
    if ruolo is not None:
        base_query = base_query.filter(LitologiaStandard.ruolo == ruolo)

    # 2. Calcola il totale REALE dei pozzi univoci che matchano i filtri
    totale_pozzi_univoci = base_query.with_entities(func.count(func.distinct(LitologiaStandard.key))).scalar()

    # 3. Calcola i raggruppamenti per termine come facevi prima
    """q_group = base_query.with_entities(
        LitologiaStandard.litologia_standard,
        func.count(func.distinct(LitologiaStandard.key)).label("n_pozzi"),
        func.count(LitologiaStandard.oid).label("n_strati")
    ).group_by(
        LitologiaStandard.litologia_standard
    ).order_by(
        func.count(func.distinct(LitologiaStandard.key)).desc()
    ).all()

    # 4. Restituisci tutto insieme
    return {
        "totale_pozzi_univoci": totale_pozzi_univoci,
        "dati": [
            {
                "termine": r.litologia_standard,
                "n_pozzi": r.n_pozzi,
                "n_strati": r.n_strati,
            }
            for r in q_group
        ]
    }"""
    # 3. Calcola i raggruppamenti per termine come facevi prima
    q_group = base_query.with_entities(
        LitologiaStandard.litologia_standard,
        func.count(func.distinct(LitologiaStandard.key)).label("n_pozzi"),
        func.count(LitologiaStandard.key).label("n_strati")
    ).group_by(
        LitologiaStandard.litologia_standard
    ).order_by(
        func.count(LitologiaStandard.oid).desc()  # ordina per n_strati, coerente col nuovo criterio
    ).all()

    totale_strati = sum(r.n_strati for r in q_group)

    return {
        "totale_pozzi_univoci": totale_pozzi_univoci,
        "totale_strati": totale_strati,
        "dati": [
            {
                "termine": r.litologia_standard,
                "n_pozzi": r.n_pozzi,     # utile per tooltip, ma NON per la percentuale
                "n_strati": r.n_strati,   # base corretta per la percentuale
            }
            for r in q_group
        ]
    }

@router.get("/litologie/filtro", summary="Pozzi che attraversano i termini litologici selezionati")
def filtro_litologia(
    termine: list[str] = Query(..., description="Uno o più termini standardizzati es. CALCARE, ARGILLA"),
    prof_min: float | None = Query(default=None),
    prof_max: float | None = Query(default=None),
    ruolo: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(func.distinct(LitologiaStandard.key)).filter(
        LitologiaStandard.litologia_standard.in_(termine)
    )

    if prof_min is not None:
        q = q.filter(LitologiaStandard.daprof >= prof_min)
    if prof_max is not None:
        q = q.filter(LitologiaStandard.aprof <= prof_max)
    if ruolo is not None:
        q = q.filter(LitologiaStandard.ruolo == ruolo)

    keys = [row[0] for row in q.all()]

    return {
        "termini": termine,
        "n_pozzi": len(keys),
        "keys": keys,
    }

@router.get("/debug/check-orfani")
def check_orfani(db: Session = Depends(get_db)):
    orfani_mineral = db.query(func.count(func.distinct(Mineralizzazioni.key))).filter(
        ~Mineralizzazioni.key.in_(db.query(Pozzo.key))
    ).scalar()

    orfani_lito = db.query(func.count(func.distinct(LitologiaStandard.key))).filter(
        ~LitologiaStandard.key.in_(db.query(Pozzo.key))
    ).scalar()

    return {
        "orfani_mineralizzazioni": orfani_mineral,
        "orfani_litologia_standard": orfani_lito
    }