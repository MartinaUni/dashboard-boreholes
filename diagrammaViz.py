import os
os.environ["PATH"] += r";C:\Program Files\Graphviz\bin"

from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph
from models import Base

engine = create_engine(
   "postgresql+psycopg2://postgres:pgAdmin98@localhost:5432/geotermia_portamivia" 
)
graph = create_schema_graph(
    engine=engine,
    metadata=Base.metadata,
    show_datatypes=True,
    show_indexes=False,
    rankdir="LR",
    concentrate=False,

)

graph.write_png("diagramma_db.png")