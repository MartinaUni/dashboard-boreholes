# -*- coding: utf-8 -*-
"""import pandas as pd
from sqlalchemy import text
from database import SessionLocal
from models import LitologiaStandard


Quando un intervallo contiene sia una litologia principale sia una o più subordinate, 
generiamo una riga per ciascuna, tutte con lo stesso daprof/aprof — perché il testo libero non dice mai dove esattamente inizia/finisce il singolo "livello subordinato" dentro l'intervallo, sappiamo solo che è presente da qualche parte in quel range. Quindi la subordinata eredita per forza i confini del padre. 
Era la decisione di modello dati che avevamo preso insieme (te lo avevo anche disegnato con l'esempio ARGILLA+LIVELLO[ARENARIA]).


# Per ripulire e rilanciare la migrazione da capo (es. dopo aver corretto
# il vocabolario e rigenerato l'Excel), esegui prima:
#
from database import SessionLocal
from models import LitologiaStandard
s = SessionLocal()
s.query(LitologiaStandard).delete()
s.commit()

FILE_INPUT = "Descrizioni_strutturate4.xlsx"
COMMIT_OGNI = 500

df = pd.read_excel(FILE_INPUT)
sessione = SessionLocal()

righe_inserite = 0
righe_primaria_saltate = 0
righe_key_orfane = 0

# carica tutti i key validi una volta sola
key_validi = set(
    row[0] for row in sessione.execute(
        text("SELECT key FROM public.pozzi")
    )
)
print(f"Key validi nel DB: {len(key_validi)}")

for _, row in df.iterrows():
    key = row["key"]        # <-- definisci key PRIMA del controllo
    daprof = row["daprof"]
    aprof = row["aprof"]

    if key not in key_validi:   # <-- ora key esiste
        righe_key_orfane += 1
        continue

    # --- litologia primaria ---
    litologia_primaria = row.get("litologia_primaria")
    if pd.notna(litologia_primaria) and str(litologia_primaria).strip():
        sessione.add(LitologiaStandard(
            key=key, daprof=daprof, aprof=aprof,
            litologia_standard=str(litologia_primaria).strip(),
            ruolo="primaria", relazione=None,
        ))
        righe_inserite += 1
    else:
        righe_primaria_saltate += 1

    # --- litologie subordinate ---
    subordinate_dettaglio = row.get("subordinate_dettaglio")
    if pd.notna(subordinate_dettaglio) and str(subordinate_dettaglio).strip():
        for parte in str(subordinate_dettaglio).split(" | "):
            if ":" not in parte:
                continue
            relazione, litologia_sub = parte.split(":", 1)
            litologia_sub = litologia_sub.strip()
            if not litologia_sub or litologia_sub == "None":
                continue
            sessione.add(LitologiaStandard(
                key=key, daprof=daprof, aprof=aprof,
                litologia_standard=litologia_sub,
                ruolo="subordinata", relazione=relazione.strip(),
            ))
            righe_inserite += 1

    if righe_inserite % COMMIT_OGNI == 0:
        sessione.commit()

sessione.commit()
sessione.close()

print(f"Righe inserite: {righe_inserite}")
print(f"Intervalli senza litologia primaria valida: {righe_primaria_saltate}")
print(f"Righe saltate per key inesistente: {righe_key_orfane}")


"""



"""
# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy import text
from database import SessionLocal
from models import LitologiaStandard

import pandas as pd
from sqlalchemy import text
from database import SessionLocal, engine
from models import LitologiaStandard, Base

# crea la tabella se non esiste ancora (non fa nulla se esiste già)
Base.metadata.create_all(bind=engine, tables=[LitologiaStandard.__table__])

FILE_INPUT = "Descrizioni_strutturate4_RIPARSATO_bis.xlsx"
COMMIT_OGNI = 500

sessione = SessionLocal()

# Optional: Ripulitura tabella prima di rilanciare l'importazione
sessione.query(LitologiaStandard).delete()
sessione.commit()

df = pd.read_excel(FILE_INPUT)

righe_inserite = 0
righe_primaria_saltate = 0
righe_key_orfane = 0

# Carica tutti i key validi una volta sola
key_validi = set(
    row[0] for row in sessione.execute(
        text("SELECT key FROM public.pozzi")
    )
)
print(f"Key validi nel DB: {len(key_validi)}")

# --- DIAGNOSI: confrontiamo tipi e valori prima di continuare ---
print("Tipo colonna 'key' in df:", df["key"].dtype)
print("Esempi key nel df:", df["key"].dropna().unique()[:10])

esempio_validi = list(key_validi)[:10]
print("Esempi key_validi nel DB:", esempio_validi)
print("Tipo di un esempio in key_validi:", type(esempio_validi[0]) if esempio_validi else None)

# quante chiavi UNICHE ha il df in totale?
chiavi_df = set(df["key"].dropna().unique())
print(f"Chiavi uniche nel df: {len(chiavi_df)}")
print(f"Chiavi valide nel DB: {len(key_validi)}")

# intersezione DIRETTA (senza normalizzare) - probabilmente vicina a zero
intersezione_diretta = chiavi_df & key_validi
print(f"Intersezione diretta (senza normalizzare): {len(intersezione_diretta)}")

# intersezione dopo normalizzazione a stringa
chiavi_df_str = set(str(k).strip() for k in chiavi_df)
key_validi_str = set(str(k).strip() for k in key_validi)
intersezione_str = chiavi_df_str & key_validi_str
print(f"Intersezione dopo normalizzazione a stringa: {len(intersezione_str)}")

# intersezione dopo normalizzazione a stringa SENZA eventuale '.0' finale
def norm_key(k):
    s = str(k).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

chiavi_df_norm = set(norm_key(k) for k in chiavi_df)
key_validi_norm = set(norm_key(k) for k in key_validi)
intersezione_norm = chiavi_df_norm & key_validi_norm
print(f"Intersezione dopo normalizzazione (rimuovendo '.0'): {len(intersezione_norm)}")

for _, row in df.iterrows():
    key = row["key"]
    daprof = row["daprof"]
    aprof = row["aprof"]

    if key not in key_validi:
        righe_key_orfane += 1
        continue

    # --- Litologia primaria ---
    litologia_primaria = row.get("litologia_primaria")
    if pd.notna(litologia_primaria) and str(litologia_primaria).strip():
        sessione.add(LitologiaStandard(
            key=key,
            daprof=daprof,
            aprof=aprof,
            litologia_standard=str(litologia_primaria).strip(),
            ruolo="primaria",
            relazione=None,
        ))
        righe_inserite += 1
    else:
        righe_primaria_saltate += 1

    # --- Litologie subordinate ---
    subordinate_dettaglio = row.get("subordinate_dettaglio")
    if pd.notna(subordinate_dettaglio) and str(subordinate_dettaglio).strip():
        for parte in str(subordinate_dettaglio).split(" | "):
            if ":" not in parte:
                continue
            relazione, litologia_sub = parte.split(":", 1)
            litologia_sub = litologia_sub.strip()
            if not litologia_sub or litologia_sub == "None":
                continue
            sessione.add(LitologiaStandard(
                key=key,
                daprof=daprof,
                aprof=aprof,
                litologia_standard=litologia_sub,
                ruolo="subordinata",
                relazione=relazione.strip(),
            ))
            righe_inserite += 1

    if righe_inserite % COMMIT_OGNI == 0:
        sessione.commit()

sessione.commit()
sessione.close()

print(f"Righe inserite: {righe_inserite}")
print(f"Intervalli senza litologia primaria valida: {righe_primaria_saltate}")
print(f"Righe saltate per key inesistente: {righe_key_orfane}")

"""

# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy import text
from database import SessionLocal, engine
from models import LitologiaStandard, Base

# crea la tabella se non esiste ancora (non fa nulla se esiste già)
Base.metadata.create_all(bind=engine, tables=[LitologiaStandard.__table__])

FILE_INPUT = "Descrizioni_strutturate4_RIPARSATO_bis.xlsx"
COMMIT_OGNI = 500

sessione = SessionLocal()

# Optional: Ripulitura tabella prima di rilanciare l'importazione
sessione.query(LitologiaStandard).delete()
sessione.commit()

df = pd.read_excel(FILE_INPUT)

# --- DEDUPLICA: rimuove righe con stessa tripla (key, daprof, aprof), ---
# --- tenendo solo la prima occorrenza. Questo evita di inserire due    ---
# --- volte la stessa descrizione nel database (causa nota: unione di  ---
# --- checkpoint sovrapposti durante il riparsing).                    ---
n_prima_dedup = len(df)
df = df.drop_duplicates(subset=["key", "daprof", "aprof"], keep="first")
n_duplicati_rimossi = n_prima_dedup - len(df)
print(f"Righe nel file originale: {n_prima_dedup}")
print(f"Righe duplicate rimosse (stessa key/daprof/aprof): {n_duplicati_rimossi}")
print(f"Righe uniche da elaborare: {len(df)}")

righe_inserite = 0
righe_primaria_saltate = 0
righe_key_orfane = 0

# Carica tutti i key validi una volta sola
key_validi = set(
    row[0] for row in sessione.execute(
        text("SELECT key FROM public.pozzi")
    )
)
print(f"Key validi nel DB: {len(key_validi)}")

# --- DIAGNOSI: confrontiamo tipi e valori prima di continuare ---
print("Tipo colonna 'key' in df:", df["key"].dtype)
print("Esempi key nel df:", df["key"].dropna().unique()[:10])

esempio_validi = list(key_validi)[:10]
print("Esempi key_validi nel DB:", esempio_validi)
print("Tipo di un esempio in key_validi:", type(esempio_validi[0]) if esempio_validi else None)

# quante chiavi UNICHE ha il df in totale?
chiavi_df = set(df["key"].dropna().unique())
print(f"Chiavi uniche nel df: {len(chiavi_df)}")
print(f"Chiavi valide nel DB: {len(key_validi)}")

# intersezione DIRETTA (senza normalizzare) - probabilmente vicina a zero
intersezione_diretta = chiavi_df & key_validi
print(f"Intersezione diretta (senza normalizzare): {len(intersezione_diretta)}")

# intersezione dopo normalizzazione a stringa
chiavi_df_str = set(str(k).strip() for k in chiavi_df)
key_validi_str = set(str(k).strip() for k in key_validi)
intersezione_str = chiavi_df_str & key_validi_str
print(f"Intersezione dopo normalizzazione a stringa: {len(intersezione_str)}")

# intersezione dopo normalizzazione a stringa SENZA eventuale '.0' finale
def norm_key(k):
    s = str(k).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

chiavi_df_norm = set(norm_key(k) for k in chiavi_df)
key_validi_norm = set(norm_key(k) for k in key_validi)
intersezione_norm = chiavi_df_norm & key_validi_norm
print(f"Intersezione dopo normalizzazione (rimuovendo '.0'): {len(intersezione_norm)}")

for _, row in df.iterrows():
    key = row["key"]
    daprof = row["daprof"]
    aprof = row["aprof"]

    if key not in key_validi:
        righe_key_orfane += 1
        continue

    # --- Litologia primaria ---
    litologia_primaria = row.get("litologia_primaria")
    if pd.notna(litologia_primaria) and str(litologia_primaria).strip():
        sessione.add(LitologiaStandard(
            key=key,
            daprof=daprof,
            aprof=aprof,
            litologia_standard=str(litologia_primaria).strip(),
            ruolo="primaria",
            relazione=None,
        ))
        righe_inserite += 1
    else:
        righe_primaria_saltate += 1

    # --- Litologie subordinate ---
    subordinate_dettaglio = row.get("subordinate_dettaglio")
    if pd.notna(subordinate_dettaglio) and str(subordinate_dettaglio).strip():
        for parte in str(subordinate_dettaglio).split(" | "):
            if ":" not in parte:
                continue
            relazione, litologia_sub = parte.split(":", 1)
            litologia_sub = litologia_sub.strip()
            if not litologia_sub or litologia_sub == "None":
                continue
            sessione.add(LitologiaStandard(
                key=key,
                daprof=daprof,
                aprof=aprof,
                litologia_standard=litologia_sub,
                ruolo="subordinata",
                relazione=relazione.strip(),
            ))
            righe_inserite += 1

    if righe_inserite % COMMIT_OGNI == 0:
        sessione.commit()

sessione.commit()
sessione.close()

print(f"Righe inserite: {righe_inserite}")
print(f"Intervalli senza litologia primaria valida: {righe_primaria_saltate}")
print(f"Righe saltate per key inesistente: {righe_key_orfane}")