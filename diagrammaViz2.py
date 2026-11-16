import os
import graphviz

dot = graphviz.Digraph("Architettura_Sistema", format="png")
dot.attr(
    rankdir="TB",        # Top-Bottom per dare l'idea della "pila" di livelli
    splines="ortho",
    nodesep="0.6",
    ranksep="0.8",
    fontname="Helvetica",
    bgcolor="white",
    pad="0.5",
    dpi="300",
)
dot.attr("node", fontname="Helvetica", fontsize="12", style="filled", penwidth="1.5")
dot.attr("edge", fontname="Helvetica", fontsize="10", color="#555555", arrowsize="0.8")

# 1. Frontend
dot.node("Frontend", 
         label="Dashboard Interattiva\n(Livello di Presentazione)", 
         shape="rect", 
         fillcolor="#4A90E2", 
         fontcolor="white", 
         width="3", height="0.8")

# 2. Backend / API
dot.node("FastAPI", 
         label="FastAPI\n(Livello Applicativo / Endpoint REST)", 
         shape="rect", 
         fillcolor="#50E3C2", 
         fontcolor="black", 
         width="3", height="0.8")

# 3. ORM
dot.node("SQLAlchemy", 
         label="SQLAlchemy\n(Object-Relational Mapper)", 
         shape="rect", 
         fillcolor="#F5A623", 
         fontcolor="black", 
         width="3", height="0.8")

# 4. Database
dot.node("Database", 
         label="PostgreSQL + PostGIS", 
         shape="cylinder",  # Forma classica per i DB
         fillcolor="#9013FE", 
         fontcolor="white", 
         width="3", height="1")

# Connessioni (Flusso della richiesta e risposta)
dot.edge("Frontend", "FastAPI", label=" Richieste HTTP (GET/POST)", dir="forward")
dot.edge("FastAPI", "Frontend", label=" Risposte JSON", dir="forward", style="dashed")

dot.edge("FastAPI", "SQLAlchemy", label=" Chiamate Python", dir="forward")
dot.edge("SQLAlchemy", "FastAPI", label=" Oggetti Python", dir="forward", style="dashed")

dot.edge("SQLAlchemy", "Database", label=" Query SQL", dir="forward")
dot.edge("Database", "SQLAlchemy", label=" Record SQL", dir="forward", style="dashed")

# Salvataggio
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architettura_sistema")
dot.render(out, cleanup=True)
print(f"Diagramma salvato in: {out}.png")