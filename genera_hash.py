"""
Script per generare l'hash bcrypt di una password.
Esegui con: python genera_hash.py
Poi copia l'hash nella query SQL per inserire l'utente nel database.
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================================================
# MODIFICA QUESTE PASSWORD
# ==================================================
utenti = [
    {"username": "admin",   "password": "geotermici1", "ruolo": "esperto"},
    {"username": "utente1", "password": "geotermici2",    "ruolo": "base"},
]

print("=" * 60)
print("Copia queste query su pgAdmin per inserire gli utenti:")
print("=" * 60)

for u in utenti:
    hashed = pwd_context.hash(u["password"])
    print(f"""
INSERT INTO public.utenti (username, password, ruolo) VALUES
('{u["username"]}', '{hashed}', '{u["ruolo"]}');
""")