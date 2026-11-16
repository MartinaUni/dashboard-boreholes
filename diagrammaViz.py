"""import os
import graphviz

COLORS = {
    "central":   "#5a3a32",
    "geo":       "#3a6045",
    "thermal":   "#7a3020",
    "strat":     "#4a5a7a",
    "technical": "#6a5a30",
    "reservoir": "#5a3a6a",
    "biblio":    "#3a5a5a",
    "vocab":     "#505050",
}

GROUPS = {
    "Geografico":      (["Regioni", "Province", "Comuni"], "geo"),
    "Vocabolari":      (["Tipi", "Scopi", "Stato", "FluidoT", "Metodi"], "vocab"),
    "Termico":         (["TempFin", "Grados", "Flusco", "Condt"], "thermal"),
    "Stratigrafico":   (["Litologia", "LitologiaStandard", "Litstr", "Cronostr"], "strat"),
    "Profilo tecnico": (["Rivest", "Finest", "Forlib", "Deviazione"], "technical"),
    "Reservoir / DST": (["Dst", "DatiPressione", "Mineralizzazioni"], "reservoir"),
    "Bibliografico":   (["BiblioRef"], "biblio"),
}

RELATIONS = [
    ("Pozzi", "Regioni",           "N:1"),
    ("Pozzi", "Province",          "N:1"),
    ("Pozzi", "Comuni",            "N:1"),
    ("Pozzi", "Tipi",              "N:1"),
    ("Pozzi", "Scopi",             "N:1"),
    ("Pozzi", "Stato",             "N:1"),
    ("Pozzi", "TempFin",           "1:N"),
    ("Pozzi", "Grados",            "1:N"),
    ("Pozzi", "Flusco",            "1:N"),
    ("Pozzi", "Condt",             "1:N"),
    ("TempFin", "Metodi",          "N:1"),
    ("Pozzi", "Litologia",         "1:N"),
    ("Pozzi", "LitologiaStandard", "1:N"),
    ("Pozzi", "Litstr",            "1:N"),
    ("Pozzi", "Cronostr",          "1:N"),
    ("Pozzi", "Rivest",            "1:N"),
    ("Pozzi", "Finest",            "1:N"),
    ("Pozzi", "Forlib",            "1:N"),
    ("Pozzi", "Deviazione",        "1:N"),
    ("Pozzi", "Dst",               "1:N"),
    ("Pozzi", "Mineralizzazioni",  "1:N"),
    ("Dst",   "DatiPressione",     "1:N"),
    ("Dst",   "FluidoT",           "N:1"),
    ("Mineralizzazioni", "FluidoT","N:1"),
    ("Pozzi", "BiblioRef",         "N:M"),
]

dot = graphviz.Digraph("ER_Semplice", format="png")
dot.attr(
    rankdir="TB",        # top→bottom più compatto con tanti cluster
    splines="polyline",
    nodesep="0.4",
    ranksep="0.9",
    fontname="Helvetica",
    bgcolor="white",
    pad="0.4",
    dpi="200",
)
dot.attr("node", fontname="Helvetica", fontsize="11",
         style="filled", penwidth="1.5")
dot.attr("edge", fontname="Helvetica", fontsize="9",
         color="#666666", arrowsize="0.65")

# Entità centrale
dot.node("Pozzi",
    shape="rectangle",
    fillcolor=COLORS["central"],
    fontcolor="white",
    fontsize="13",
    penwidth="2.5",
    color=COLORS["central"],
    width="1.6",
    height="0.55",
)

# Gruppi
for group_name, (members, color_key) in GROUPS.items():
    color = COLORS[color_key]
    with dot.subgraph(name=f"cluster_{group_name.replace(' ','_')}") as sg:
        sg.attr(
            label=group_name,
            style="rounded,filled",
            fillcolor=f"{color}15",
            color=color,
            penwidth="1.5",
            fontcolor=color,
            fontname="Helvetica Bold",
            fontsize="10",
        )
        for tbl in members:
            sg.node(tbl,
                shape="rectangle",
                fillcolor=color,
                fontcolor="white",
                color=color,
                width="1.5",
                height="0.45",
            )

# Relazioni
for src, dst, card in RELATIONS:
    is_nm = "N:M" in card
    dot.edge(src, dst,
        label=f" {card} ",
        style="dashed" if is_nm else "solid",
        fontcolor="#555555",
        fontsize="8",
        color="#444444" if not is_nm else "#888888",
    )

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "er_semplice")
dot.format = "png"
dot.render(out, cleanup=True)
print(f"PNG: {out}.png")
dot.format = "pdf"
dot.render(out, cleanup=True)
print(f"PDF: {out}.pdf")"""

import os
import graphviz

COLORS = {
    "central":   "#5a3a32",
    "geo":       "#3a6045",
    "thermal":   "#7a3020",
    "strat":     "#4a5a7a",
    "technical": "#6a5a30",
    "reservoir": "#5a3a6a",
    "vocab":     "#505050",
}

GROUPS = {
    "Geografico":      (["Regioni", "Province", "Comuni"], "geo"),
    "Vocabolari":      (["Tipi", "Scopi", "Stato", "FluidoT", "Metodi"], "vocab"),
    "Termico":         (["TempFin", "TempRaw", "TempConnex", "Grados", "Flusco", "Condt"], "thermal"),
    "Stratigrafico":   (["Litologia", "LitologiaStandard", "Litstr", "Cronostr"], "strat"),
    "Profilo tecnico": (["Rivest", "Finest", "Forlib", "Deviazione"], "technical"),
    "Reservoir / DST": (["Dst", "DatiPressione", "Mineralizzazioni"], "reservoir"),
}

RELATIONS = [
    # Geografico & Vocabolari base
    ("Pozzi", "Regioni",           "N:1"),
    ("Pozzi", "Province",          "N:1"),
    ("Pozzi", "Comuni",            "N:1"),
    ("Pozzi", "Tipi",              "N:1"),
    ("Pozzi", "Scopi",             "N:1"),
    ("Pozzi", "Stato",             "N:1"),
    
    # Termico
    ("Pozzi", "TempFin",           "1:N"),
    ("Pozzi", "Grados",            "1:N"),
    ("Pozzi", "Flusco",            "1:N"),
    ("Pozzi", "Condt",             "1:N"),
    ("TempFin", "Metodi",          "N:1"),
    
    # --- LA RELAZIONE N:M SULLE TEMPERATURE ---
    ("TempFin", "TempRaw",         "N:M"),   # Relazione logica diretta
    ("TempFin", "TempConnex",      "1:N"),   # Implementazione fisica
    ("TempRaw", "TempConnex",      "1:N"),   # Implementazione fisica
    
    # Stratigrafico
    ("Pozzi", "Litologia",         "1:N"),
    ("Pozzi", "LitologiaStandard", "1:N"),
    ("Pozzi", "Litstr",            "1:N"),
    ("Pozzi", "Cronostr",          "1:N"),
    
    # Profilo Tecnico
    ("Pozzi", "Rivest",            "1:N"),
    ("Pozzi", "Finest",            "1:N"),
    ("Pozzi", "Forlib",            "1:N"),
    ("Pozzi", "Deviazione",        "1:N"),
    
    # Reservoir / DST
    ("Pozzi", "Dst",               "1:N"),
    ("Pozzi", "Mineralizzazioni",  "1:N"),
    ("Dst",   "DatiPressione",     "1:N"),
    ("Dst",   "FluidoT",           "N:1"),
    ("Mineralizzazioni", "FluidoT","N:1"),
]

dot = graphviz.Digraph("ER_Complesso_Verticale", format="png")
dot.attr(
    rankdir="LR",        
    splines="ortho",     
    nodesep="0.3",
    ranksep="1.2",
    fontname="Helvetica",
    bgcolor="white",
    pad="0.5",
    dpi="300",           
)
dot.attr("node", fontname="Helvetica", fontsize="11",
         style="filled", penwidth="1.5")
dot.attr("edge", fontname="Helvetica", fontsize="9",
         color="#666666", arrowsize="0.65")

# Entità centrale
dot.node("Pozzi",
    shape="rectangle",
    fillcolor=COLORS["central"],
    fontcolor="white",
    fontsize="14",
    fontname="Helvetica Bold",
    penwidth="2.5",
    color=COLORS["central"],
    width="1.8",
    height="0.6",
)

# Creazione dei Gruppi/Cluster
for group_name, (members, color_key) in GROUPS.items():
    color = COLORS[color_key]
    with dot.subgraph(name=f"cluster_{group_name.replace(' ','_')}") as sg:
        sg.attr(
            label=group_name,
            style="rounded,filled",
            fillcolor=f"{color}15",
            color=color,
            penwidth="1.5",
            fontcolor=color,
            fontname="Helvetica Bold",
            fontsize="11",
            margin="15",
        )
        for tbl in members:
            # Rende la tabella di giunzione graficamente diversa (ellisse invece di rettangolo)
            is_junction = (tbl == "TempConnex")
            sg.node(tbl,
                shape="ellipse" if is_junction else "rectangle",
                fillcolor="white" if is_junction else color,
                fontcolor=color if is_junction else "white",
                color=color,
                penwidth="2.0" if is_junction else "1.5",
                width="1.5",
                height="0.45",
            )

# Generazione delle Relazioni
for src, dst, card in RELATIONS:
    is_nm = ("N:M" in card)
    dot.edge(src, dst,
        label=f" {card} ",
        style="dashed" if is_nm else "solid",
        fontcolor="#333333",
        fontsize="9",
        color="#888888" if is_nm else "#444444",
        penwidth="1.5" if is_nm else "1.0"
    )

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "er_aggiornato")
dot.format = "png"
dot.render(out, cleanup=True)
print(f"PNG salvato: {out}.png")
dot.format = "pdf"
dot.render(out, cleanup=True)
print(f"PDF salvato: {out}.pdf")