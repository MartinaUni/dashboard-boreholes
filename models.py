from sqlalchemy import Column, Integer, SmallInteger, String, Float, ForeignKey, Numeric, Boolean, Text, BigInteger
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ENTITÀ GEOGRAFICHE


class Regioni(Base):
    __tablename__ = "regioni"
    __table_args__ = {"schema": "info_cod"}

    reg = Column(Numeric, primary_key=True)
    nome = Column(String(255))

    x_min = Column(Numeric)
    y_min = Column(Numeric)
    x_max = Column(Numeric)
    y_max = Column(Numeric)

    pozzi = relationship("Pozzo", back_populates="regione")


class Province(Base):
    __tablename__ = "province"
    __table_args__ = {"schema": "info_cod"}

    prov = Column("PROV", Numeric, primary_key=True)
    reg  = Column("REG", Numeric)
    nome = Column("NOME", String(255))
    targa = Column("TARGA", String(4))

    x_min = Column(Numeric)
    y_min = Column(Numeric)
    x_max = Column(Numeric)
    y_max = Column(Numeric)

    pozzi = relationship("Pozzo", back_populates="provincia")


class Comuni(Base):
    __tablename__ = "comuni"
    __table_args__ = {"schema": "info_cod"}

    
    istat = Column(Numeric, primary_key=True)
    id = Column(Numeric)

    nome = Column(String(255))

    x = Column(Numeric)
    y = Column(Numeric)
    j1 = Column(Numeric)
    j2 = Column(Numeric)

    x_min = Column(Numeric)
    y_min = Column(Numeric)
    x_max = Column(Numeric)
    y_max = Column(Numeric)

    reg = Column(Numeric)
    prov = Column(Numeric)



# VOCABOLARI


class Tipi(Base):
    __tablename__ = "tipi"
    __table_args__ = {"schema": "info_cod"}

    tipo = Column(SmallInteger, primary_key=True)  # FIX: smallint
    descrizione = Column(String(30))


class Scopi(Base):
    __tablename__ = "scopi"
    __table_args__ = {"schema": "info_cod"}

    scopo = Column(SmallInteger, primary_key=True)  # FIX: smallint
    descrizione = Column(String(13))


class Usi(Base):
    __tablename__ = "usi"
    __table_args__ = {"schema": "info_cod"}

    uso = Column("Uso", Float, primary_key=True)
    descrizione = Column("DESCRIZIONE", String(21))


class Stato(Base):
    __tablename__ = "stati"
    __table_args__ = {"schema": "info_cod"}

    stato = Column("STATO", SmallInteger, primary_key=True)  
    descrizione = Column("DESCRIZIONE", String(22))


class Esiti(Base):
    __tablename__ = "esiti"
    __table_args__ = {"schema": "info_cod"}

    esitom = Column(SmallInteger, primary_key=True)  
    descrizione = Column("Descrizione", String(24))


class Inn(Base):
    __tablename__ = "inn"
    __table_args__ = {"schema": "info_cod"}

    inn = Column(SmallInteger, primary_key=True)  # FIX: smallint
    descrizione = Column(String(14))


class Litho(Base):
    __tablename__ = "litho"
    __table_args__ = {"schema": "info_cod"}

    litologia = Column(Integer, primary_key=True)
    descrizione = Column(String(120))


class Metodi(Base):
    """Vocabolario metodi di misura — FK reale di info_pozzi.temp.metodo"""
    __tablename__ = "metodi"
    __table_args__ = {"schema": "info_cod"}

    tipo_metodo = Column(SmallInteger, primary_key=True)
    descrizione = Column(String(30))


class Unita(Base):
    """Unità di misura — FK di Pozzo.umpt e info_pozzi.assorb.u_misura"""
    __tablename__ = "unita"
    __table_args__ = {"schema": "info_cod"}

    unita = Column(SmallInteger, primary_key=True)
    descrizione = Column(String(8))



# SCALA GEOLOGICA
# tutte le PK/FK sono String, non Integer


class Eone(Base):
    __tablename__ = "eone"
    __table_args__ = {"schema": "info_cod"}

    cod_eone = Column(String(10), primary_key=True)  # FIX: varchar(10)
    eone = Column(String(20))
    anni_inf = Column(Float)                          # FIX: double precision
    anni_sup = Column(Float)


class Era(Base):
    __tablename__ = "era"
    __table_args__ = {"schema": "info_cod"}

    cod_era  = Column(String(4), primary_key=True)    # FIX: varchar(4)
    era = Column(String(30))
    anni_inf = Column(Float)
    anni_sup = Column(Float)

    cod_eone = Column(String(10), ForeignKey("info_cod.eone.cod_eone"))  # FIX


class Periodo(Base):
    __tablename__ = "periodo"
    __table_args__ = {"schema": "info_cod"}

    cod_periodo = Column(String(4), primary_key=True)  # FIX: varchar(4)
    periodo = Column(String(30))
    anni_inf = Column(Float)
    anni_sup = Column(Float)

    cod_era = Column(String(4), ForeignKey("info_cod.era.cod_era"))  # FIX


class Epoca(Base):
    __tablename__ = "epoca"
    __table_args__ = {"schema": "info_cod"}

    cod_epoca = Column(String(6), primary_key=True)  # FIX: varchar(6)
    epoca = Column(String(30))
    anni_inf = Column(Float)
    anni_sup = Column(Float)

    cod_periodo = Column(String(4), ForeignKey("info_cod.periodo.cod_periodo"))  # FIX


class EtaPiano(Base):
    __tablename__ = "etapiano"
    __table_args__ = {"schema": "info_cod"}

    cod_eta = Column(String(7), primary_key=True)   
    eta_piano = Column(String(30))
    anni_inf = Column(Float)
    anni_sup = Column(Float)

    cod_epoca  = Column(String(7),  ForeignKey("info_cod.epoca.cod_epoca"))   #corretti tipi 
    cod_periodo = Column(String(4),  ForeignKey("info_cod.periodo.cod_periodo"))
    cod_era = Column(String(4),  ForeignKey("info_cod.era.cod_era"))        
    cod_eone = Column(String(4),  ForeignKey("info_cod.eone.cod_eone"))      



# POZZI


class Pozzo(Base):
    __tablename__ = "pozzi"
    __table_args__ = {"schema": "public"}

    key = Column(Integer, primary_key=True)

    # Anagrafica
    nome = Column(String(254))
    entitam = Column(String(254))  # entità amministrativa
    camploc = Column(String(254))  # campo / località
    locgeo = Column(String(254))  # località geografica
    proprietar = Column(String(254))
    datacomp = Column(String(254))  # data completamento
    util = Column(String(254))
    es = Column(String(254))
    tav = Column(String(254))

    # Coordinate
    lat = Column(Float)
    lon = Column(Float)
    lat_ = Column(Float)
    lon_ = Column(Float)

    # Misure
    prof  = Column(Float)
    quota = Column(Float)
    f100  = Column(Float)
    f200  = Column(Float)
    mua = Column(Float)
    tr = Column(Float)
    da = Column(String(254))
    a  = Column(String(254))

    # Deviazione
    pozdev_profdev = Column(String(254))
    pozdev_profver = Column(String(254))
    pozdev_lat = Column(String(254))
    pozdev_lon = Column(String(254))

    # Flags
    public = Column(Boolean)
    oid = Column(Integer)
    lon_mm = Column(Integer)
    anrd1 = Column(Float)

    # FK geografiche
    istat = Column(Numeric, ForeignKey("info_cod.comuni.istat"))
    reg = Column(Numeric, ForeignKey("info_cod.regioni.reg"))
    prov = Column(Numeric, ForeignKey("info_cod.province.PROV"))

    # FK vocabolari
    tipo = Column(SmallInteger, ForeignKey("info_cod.tipi.tipo"))
    scopo = Column(SmallInteger, ForeignKey("info_cod.scopi.scopo"))
    uso = Column(Float,        ForeignKey("info_cod.usi.Uso"))
    stato = Column(SmallInteger, ForeignKey("info_cod.stati.STATO"))   # FIX: SmallInteger
    esitom = Column(SmallInteger, ForeignKey("info_cod.esiti.esitom"))
    inn = Column(SmallInteger, ForeignKey("info_cod.inn.inn"))
    umpt = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))   # FIX: era assente

    # Relationships
    regione = relationship("Regioni",  back_populates="pozzi")
    provincia = relationship("Province", back_populates="pozzi")

    tipo_rel = relationship("Tipi")
    scopo_rel = relationship("Scopi")
    uso_rel = relationship("Usi")
    stato_rel = relationship("Stato")
    unita_rel = relationship("Unita")


# DATI POZZO

#QUESTA NON VA USATA
class Temp(Base):
    __tablename__ = "temp"
    __table_args__ = {"schema": "info_pozzi"}

    oid = Column(Integer, primary_key=True)
    key = Column(Integer, ForeignKey("public.pozzi.key"))

    data = Column(String(10))
    prof = Column(Float)
    temp = Column(Float)
    tcirc = Column(Float)
    tstop = Column(Float)

    metodo = Column(SmallInteger, ForeignKey("info_cod.metodi.tipo_metodo"))  

    tp = Column(String)
    id_temp = Column(Integer)
    id_ref_temp = Column(String(20))

    pozzo  = relationship("Pozzo",   backref="temperature")
    metodo_rel = relationship("Metodi")


class Litologia(Base):
    __tablename__ = "litologia"
    __table_args__ = {"schema": "info_pozzi"}

    oid = Column(Integer, primary_key=True)
    key = Column(Integer, ForeignKey("public.pozzi.key"))

    daprof = Column(Float)
    aprof  = Column(Float)

    litologia = Column(String(1000))
    eni = Column(Boolean)

    pozzo = relationship("Pozzo", backref="litologie")

#Cose che probabilmente non userò negli endpoint



# VOCABOLARI MANCANTI (info_cod)


class AssorbT(Base):
    __tablename__ = "assorb_t"
    __table_args__ = {"schema": "info_cod"}

    tipo = Column(String(1), primary_key=True)
    descrizione = Column(String(24))


class FluidoT(Base):
    __tablename__ = "fluido_t"
    __table_args__ = {"schema": "info_cod"}

    fluido_t = Column(SmallInteger, primary_key=True)
    descrizione = Column("DESCRIZIONE", String(24))


class GeomsVoc(Base):
    __tablename__ = "geoms_voc"
    __table_args__ = {"schema": "info_cod"}

    sede = Column("SEDE", Numeric, primary_key=True)
    descrizione = Column("DESCRIZIONE", String(21))


class FaseProva(Base):
    __tablename__ = "faseprova"
    __table_args__ = {"schema": "info_cod"}

    cod_faseprova = Column(SmallInteger, primary_key=True)
    fase_prova = Column(String(6))
    descr_faseprova = Column(String(40))


class ParamFisico(Base):
    __tablename__ = "param_fisico"
    __table_args__ = {"schema": "info_cod"}

    codparamF  = Column(SmallInteger, primary_key=True)
    parametroF = Column(String(30))


class PermT(Base):
    __tablename__ = "perm_t"
    __table_args__ = {"schema": "info_cod"}

    perm_t = Column(SmallInteger, primary_key=True)
    descrizione = Column("DESCRIZIONE", String(24))


class Quantit(Base):
    __tablename__ = "quantit"
    __table_args__ = {"schema": "info_cod"}

    # due colonne candidate a PK nel DB — usiamo cod_quant (NOT NULL, char(1))
    cod_quant = Column(String(1), primary_key=True)
    codquant = Column(SmallInteger)
    limite = Column(String(15))
    simbolo = Column(String(1))


class Ref(Base):
    __tablename__ = "ref"
    __table_args__ = {"schema": "info_cod"}

    ref = Column(SmallInteger, primary_key=True)
    descrizione = Column(String(56))


class Regime(Base):
    __tablename__ = "regime"
    __table_args__ = {"schema": "info_cod"}

    regime = Column(Integer, primary_key=True)
    descrizione = Column(String(15))


class TipoPerm(Base):
    __tablename__ = "tipoperm"
    __table_args__ = {"schema": "info_cod"}

    tipoperm = Column(SmallInteger, primary_key=True)
    descrizione = Column("DESCRIZIONE", String(24))


class TipoProva(Base):
    __tablename__ = "tipoprova"
    __table_args__ = {"schema": "info_cod"}

    cod_tipoprova = Column(SmallInteger, primary_key=True)
    descri_tipoprova = Column(String(40))


class UnitLitoT(Base):
    __tablename__ = "unitlitoT"
    __table_args__ = {"schema": "info_cod"}

    codlitoT = Column(SmallInteger, primary_key=True)
    sigla = Column(String(10))
    litolog_litot = Column(String(80))



# TABELLE DATI POZZO MANCANTI (info_pozzi)

class Assorb(Base):
    __tablename__ = "assorb"
    __table_args__ = {"schema": "info_pozzi"}

    oid  = Column(Integer, primary_key=True)
    key   = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof = Column(Float)
    aprof = Column(Float)
    tipo_assorbimento = Column(String(1), ForeignKey("info_cod.assorb_t.tipo"))
    valore = Column(Float)
    note = Column(String(254))
    u_misura = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    eni = Column(Boolean)

    pozzo  = relationship("Pozzo",   backref="assorbimenti")
    tipo_rel = relationship("AssorbT")
    unita_rel = relationship("Unita")


class BiblioRef(Base):
    __tablename__ = "biblio_ref"
    __table_args__ = {"schema": "info_pozzi"}

    oid = Column(Integer, primary_key=True)
    key = Column(Integer, ForeignKey("public.pozzi.key"))
    ref = Column(SmallInteger, ForeignKey("info_cod.ref.ref"))

    pozzo   = relationship("Pozzo", backref="biblio_refs")
    ref_rel = relationship("Ref")


class Finest(Base):
    __tablename__ = "finest"
    __table_args__ = {"schema": "info_pozzi"}

    oid    = Column(Integer, primary_key=True)
    key    = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof = Column(Float)
    aprof  = Column(Float)
    tp     = Column(String)   # tipo "char" nel DB

    pozzo = relationship("Pozzo", backref="finestrature")


class Forlib(Base):
    __tablename__ = "forlib"
    __table_args__ = {"schema": "info_pozzi"}

    oid    = Column(Integer, primary_key=True)
    key    = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof = Column(Float)
    aprof  = Column(Float)
    diametr = Column(Float)
    tp     = Column(String)

    pozzo = relationship("Pozzo", backref="fori_liberi")


class Litstr(Base):
    __tablename__ = "litstr"
    __table_args__ = {"schema": "info_pozzi"}

    oid        = Column(Integer, primary_key=True)
    key        = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof     = Column(Float)
    aprof      = Column(Float)
    nomeunita1 = Column(String(64))
    rango      = Column(String(64))
    nomeunita2 = Column(String(64))
    posizione  = Column(String(64))
    etarel     = Column(String(64))
    a          = Column(String(64))
    indice     = Column(Integer, ForeignKey("info_cod.litho.litologia"))  # FK reale su litho
    litologia  = Column(String(1000))
    tp         = Column(String)
    eni        = Column(Boolean)

    pozzo     = relationship("Pozzo",  backref="litostratigrafia")
    litho_rel = relationship("Litho")


class Rivest(Base):
    __tablename__ = "rivest"
    __table_args__ = {"schema": "info_pozzi"}

    oid     = Column(Integer, primary_key=True)
    key     = Column(Integer, ForeignKey("public.pozzi.key"))
    testa   = Column(Float)
    scarpa  = Column(Float)
    diamest = Column(Float)
    spestub = Column(Float)
    fin     = Column(String(2))
    tp      = Column(String)
    eni     = Column(Boolean)

    pozzo = relationship("Pozzo", backref="rivestimenti")

"""
class TempFin(Base):
    __tablename__ = "temp_fin"
    __table_args__ = {"schema": "info_pozzi"}

    id_temp       = Column(Integer, primary_key=True)
    key           = Column(Integer, ForeignKey("public.pozzi.key"))
    data          = Column(String(10))
    nr_misura     = Column(SmallInteger)
    discesa       = Column(SmallInteger)
    prof          = Column(Float)
    temp          = Column(Float)
    tcirc         = Column(Float)
    metodo_misura = Column(SmallInteger, ForeignKey("info_cod.metodi.tipo_metodo"))

    pozzo      = relationship("Pozzo",  backref="temperature_finali")
    metodo_rel = relationship("Metodi")


class TempRaw(Base):
    __tablename__ = "temp_raw"
    __table_args__ = {"schema": "info_pozzi"}

    id_bht    = Column(Integer, primary_key=True)
    data      = Column(String(10))
    nr_misura = Column(SmallInteger)
    discesa   = Column(SmallInteger)
    prof      = Column(Float)
    temp      = Column(Float)
    tcirc     = Column(Float)
    tstop     = Column(Float)


class TempConnex(Base):
    
    __tablename__ = "temp_connex"
    __table_args__ = {"schema": "info_pozzi"}

    oid    = Column(Integer, primary_key=True)
    id_bht = Column(Integer, ForeignKey("info_pozzi.temp_raw.id_bht"))
    id_temp = Column(Integer, ForeignKey("info_pozzi.temp_fin.id_temp"))

    temp_raw_rel = relationship("TempRaw")
    temp_fin_rel = relationship("TempFin")
"""


# NUOVO MODELLO TEMPERATURE CORRETTO
# Sostituisce l'uso della vecchia tabella Temp quando servono
# relazioni reali tra misure raw e misure finali.

class TempRaw(Base):
    """
    Misurazioni grezze
    Più record indipendenti
    """
    __tablename__ = "temp_raw"
    __table_args__ = {"schema": "info_pozzi"}

    id_bht = Column(Integer, primary_key=True)

    data = Column(String(10))
    nr_misura = Column(SmallInteger)
    discesa = Column(SmallInteger)

    prof = Column(Float)
    temp = Column(Float)
    tcirc = Column(Float)
    tstop = Column(Float)

    # relazione N:N verso TempFin tramite TempConnex
    temperature_finali = relationship(
        "TempFin",
        secondary="info_pozzi.temp_connex",
        back_populates="temperature_raw"
    )


class TempFin(Base):
    """
    Misure finali
    Queste sono le temperature da usare negli endpoint analytics.
    """
    __tablename__ = "temp_fin"
    __table_args__ = {"schema": "info_pozzi"}

    id_temp = Column(Integer, primary_key=True)

    key = Column(Integer, ForeignKey("public.pozzi.key"), nullable=False)

    data = Column(String(10))
    nr_misura = Column(SmallInteger)
    discesa = Column(SmallInteger)

    prof = Column(Float)
    temp = Column(Float)
    tcirc = Column(Float)

    metodo_misura = Column(
        SmallInteger,
        ForeignKey("info_cod.metodi.tipo_metodo")
    )

    # relazioni principali
    pozzo = relationship("Pozzo", backref="temperature_finali")
    metodo_rel = relationship("Metodi")

    # relazione N:N con raw
    temperature_raw = relationship(
        "TempRaw",
        secondary="info_pozzi.temp_connex",
        back_populates="temperature_finali"
    )


class TempConnex(Base):
    """
    Tabella ponte N:N tra:
    - TempRaw (id_bht)
    - TempFin (id_temp)

    Una misura finale può derivare da più raw.
    Una raw può contribuire a più finali.
    """
    __tablename__ = "temp_connex"
    __table_args__ = {"schema": "info_pozzi"}

    oid = Column(Integer, primary_key=True)

    id_bht = Column(
        Integer,
        ForeignKey("info_pozzi.temp_raw.id_bht"),
        nullable=False
    )

    id_temp = Column(
        Integer,
        ForeignKey("info_pozzi.temp_fin.id_temp"),
        nullable=False
    )

class Tempdst(Base):
    __tablename__ = "tempdst"
    __table_args__ = {"schema": "info_pozzi"}

    oid              = Column(Integer, primary_key=True)
    id_licence       = Column(Integer, ForeignKey("public.concessioni.id"))
    nome_licence     = Column(String)
    prof_top         = Column(Float)
    prof_bottom      = Column(Float)
    temp             = Column(Float)
    name_giacimento  = Column(String)

    concessione = relationship("Concessioni")


class WellCoord(Base):
    __tablename__ = "well_coord"
    __table_args__ = {"schema": "info_pozzi"}

    key         = Column(Integer, ForeignKey("public.pozzi.key"), primary_key=True)
    lat         = Column(Float)
    lon         = Column(Float)
    lon_mm      = Column(Integer)
    reg         = Column(Numeric)
    lat_gg      = Column(Integer)
    lat_pp      = Column(Integer)
    lat_ss      = Column(Integer)
    lon_gg      = Column(Integer)
    lon_pp      = Column(Integer)
    lon_ss      = Column(Integer)
    lat_cc      = Column(Numeric)
    lon_cc      = Column(Numeric)
    lat_gd      = Column(Numeric)
    lon_gd      = Column(Numeric)
    lon_gw      = Column(Numeric)
    lon_mm_new  = Column(Numeric)
    id_mm_new   = Column(Numeric)
    lon_gg_     = Column(Numeric)
    lon_pp_     = Column(Numeric)
    lon_ss_     = Column(Numeric)
    lon_cc_     = Column(Numeric)
    lon_gw_final = Column(Numeric)

    pozzo = relationship("Pozzo", backref="coordinate")


class WellSr(Base):
    __tablename__ = "well_sr"
    __table_args__ = {"schema": "info_pozzi"}

    oid                = Column(Integer, primary_key=True)
    key                = Column(Integer, ForeignKey("public.pozzi.key"))
    lat_wgs84          = Column(Float)
    lon_wgs84          = Column(Float)
    lat_roma40_1       = Column(Integer)
    lon_roma40_1       = Column(Integer)
    lat_roma40_2       = Column(Integer)
    lon_roma40_2       = Column(Integer)
    lat_rdn2008_italy  = Column(Integer)
    lon_rdn2008_italy  = Column(Integer)
    lat_rdn2008_tm32   = Column(Integer)
    lon_rdn2008_tm32   = Column(Integer)
    lat_rdn2008_tm33   = Column(Integer)
    lon_rdn2008_tm33   = Column(Numeric)
    lat_wgs84utm32     = Column(Integer)
    lon_wgs84utm32     = Column(Integer)
    lat_wgs84utm33     = Column(Integer)
    lon_wgs84utm33     = Column(Numeric)

    pozzo = relationship("Pozzo", backref="sistemi_riferimento")


# =========================
# PUBLIC
# =========================

class Concessioni(Base):
    __tablename__ = "concessioni"
    __table_args__ = {"schema": "public"}

    id          = Column(Integer, primary_key=True)
    name        = Column(String(254))
    descriptio  = Column(String(254))
    tipologia   = Column(String(200))
    nome        = Column(String(200))
    # geom: colonna PostGIS, non mappata





# SCHEMA info_pozzi_geothermal
# Dati termici specifici per pozzi geotermici:
# conduttività termica, flusso di calore, gradiente geotermico
# Tutte le tabelle hanno FK → public.pozzi.key


class Condt(Base):
    """Conduttività termica per intervallo di profondità"""
    __tablename__ = "condt"
    __table_args__ = {"schema": "info_pozzi_geothermal"}

    oid      = Column(Integer, primary_key=True)
    key      = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof   = Column(Float)
    aprof    = Column(Float)
    cond     = Column(Float)   # conduttività termica
    dvs      = Column(Float)   # deviazione standard
    litologia = Column(String(40))
    metodo   = Column(String(15))
    tp       = Column(String)

    pozzo = relationship("Pozzo", backref="conduttivita")


class Flusco(Base):
    """Flusso di calore geotermico"""
    __tablename__ = "flusco"
    __table_args__ = {"schema": "info_pozzi_geothermal"}

    oid       = Column(Integer, primary_key=True)
    key       = Column(Integer, ForeignKey("public.pozzi.key"))
    data      = Column(String(10))
    flusso    = Column(Float)   # flusso di calore grezzo
    dvsf      = Column(Float)   # deviazione standard flusso
    flusso_c  = Column(Float)   # flusso corretto
    grad_c    = Column(Float)   # gradiente corretto
    dvsfc     = Column(Float)
    dvsgc     = Column(Float)
    correzione = Column(SmallInteger)
    tp        = Column(String)

    pozzo = relationship("Pozzo", backref="flussi_calore")


class Grados(Base):
    """Gradiente geotermico per intervallo di profondità"""
    __tablename__ = "grados"
    __table_args__ = {"schema": "info_pozzi_geothermal"}

    oid   = Column(Integer, primary_key=True)
    key   = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof = Column(Float)
    aprof  = Column(Float)
    grad   = Column(Float)   # gradiente geotermico
    dvsg   = Column(Float)   # deviazione standard gradiente
    condm  = Column(Float)   # conduttività media
    dvs    = Column(Float)
    tp     = Column(String)

    pozzo = relationship("Pozzo", backref="gradienti")




# SCHEMA info_pozzi_hydrocarbon
# Dati tecnici specifici per pozzi a idrocarburi:
# DST (drill stem test), analisi chimiche e fisiche dei fluidi,
# dati di pressione, stratigrafici, litotermici, deviazione e mineralizzazioni.



class Dst(Base):
    """Drill Stem Test — prove di produzione del pozzo"""
    __tablename__ = "dst"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    id_dst     = Column(Integer, primary_key=True)
    key        = Column(Integer, ForeignKey("public.pozzi.key"))
    nom_prov   = Column(String(8))
    tipo_prova = Column(SmallInteger, ForeignKey("info_cod.tipoprova.cod_tipoprova"))
    top        = Column(Float)
    bottom     = Column(Float)
    prof_misura = Column(Float)
    tipo_fluid = Column(SmallInteger, ForeignKey("info_cod.fluido_t.fluido_t"))
    note       = Column(String(254))

    pozzo          = relationship("Pozzo", backref="dst")
    tipo_prova_rel = relationship("TipoProva")
    fluido_rel     = relationship("FluidoT")


class AnChimica(Base):
    """Analisi chimiche del fluido estratto durante DST"""
    __tablename__ = "an_chimica"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid          = Column(Integer, primary_key=True)
    id_dst       = Column(Integer, ForeignKey("info_pozzi_hydrocarbon.dst.id_dst"))
    n_analisi    = Column(SmallInteger)
    tipo_fluido  = Column(SmallInteger, ForeignKey("info_cod.fluido_t.fluido_t"))
    lim_conc     = Column(String(1), ForeignKey("info_cod.quantit.cod_quant"))
    specie_ch    = Column(String(11))
    valore_sp    = Column(Float)
    u_mis_sp_ch  = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    nota         = Column(String(254))

    dst_rel     = relationship("Dst")
    fluido_rel  = relationship("FluidoT")
    quantit_rel = relationship("Quantit")
    unita_rel   = relationship("Unita")


class AnFisica(Base):
    """Analisi fisiche del fluido estratto durante DST"""
    __tablename__ = "an_fisica"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid          = Column(Integer, primary_key=True)
    id_dst       = Column(Integer, ForeignKey("info_pozzi_hydrocarbon.dst.id_dst"))
    n_analisi    = Column(SmallInteger)
    tipo_fluido  = Column(SmallInteger, ForeignKey("info_cod.fluido_t.fluido_t"))
    parametro    = Column(SmallInteger, ForeignKey("info_cod.param_fisico.codparamF"))
    valore_par   = Column(Float)
    u_mis_par_fi = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    nota         = Column(String(254))

    dst_rel        = relationship("Dst")
    fluido_rel     = relationship("FluidoT")
    parametro_rel  = relationship("ParamFisico")
    unita_rel      = relationship("Unita")


class DatiPressione(Base):
    """Dati di pressione di fondo registrati durante le fasi del DST"""
    __tablename__ = "dati_pressione"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid_press       = Column(Integer, primary_key=True)
    id_dst          = Column(Integer, ForeignKey("info_pozzi_hydrocarbon.dst.id_dst"))
    fase_prova      = Column(SmallInteger, ForeignKey("info_cod.faseprova.cod_faseprova"))
    press_fondo     = Column(Float)
    u_mis_press_fon = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    ore             = Column(SmallInteger)
    minuti          = Column(SmallInteger)
    vol_fluido      = Column(Float)
    u_mis_vol_flu   = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    vol_gas         = Column(Float)
    u_mis_vol_gas   = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    portata_fluido  = Column(Float)
    u_mis_por_flu   = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    portata_gas     = Column(Float)
    u_mis_por_gas   = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    nota            = Column(String(254))

    dst_rel       = relationship("Dst")
    fase_rel      = relationship("FaseProva")


class DensFango(Base):
    """Densità del fango di perforazione per intervallo di profondità"""
    __tablename__ = "dens_fango"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid          = Column(Integer, primary_key=True)
    key          = Column(Integer, ForeignKey("public.pozzi.key"))
    top          = Column(Numeric)
    bottom       = Column(Numeric)
    densit       = Column(Numeric)
    unit_mis_dens = Column(SmallInteger, ForeignKey("info_cod.unita.unita"))
    nota         = Column(String(50))

    pozzo     = relationship("Pozzo", backref="densita_fango")
    unita_rel = relationship("Unita")


class Deviazione(Base):
    """Deviazione del pozzo — inclinazione e azimuth a profondità misurata"""
    __tablename__ = "deviazione"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid          = Column(Integer, primary_key=True)
    key          = Column(Integer, ForeignKey("public.pozzi.key"))
    md           = Column(Float)   # measured depth
    inclinazione = Column(Float)
    azimuth      = Column(Float)

    pozzo = relationship("Pozzo", backref="deviazioni")


class Cronostr(Base):
    """Cronострatigrafia — età geologica per intervallo di profondità"""
    __tablename__ = "cronostr"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid     = Column(Integer, primary_key=True)
    key     = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof  = Column(Float)
    aprof   = Column(Float)
    eta_sup = Column(String(64))
    eta_inf = Column(String(64))
    note    = Column(String(500))

    pozzo = relationship("Pozzo", backref="cronostratigrafia")


class Str(Base):
    """Stratigrafia — formazioni geologiche per intervallo di profondità"""
    __tablename__ = "str"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid       = Column(Integer, primary_key=True)
    key       = Column(Integer, ForeignKey("public.pozzi.key"))
    daprof    = Column(Float)
    aprof     = Column(Float)
    formazione = Column(String(64))
    nota      = Column(String(500))

    pozzo = relationship("Pozzo", backref="stratigrafia")


class Litoterm(Base):
    """Unità litotermiche — classificazione termica della litologia"""
    __tablename__ = "litoterm"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid          = Column(Integer, primary_key=True)
    key          = Column(Integer, ForeignKey("public.pozzi.key"))
    top          = Column(Float)
    bottom       = Column(Float)
    unit_litoterm = Column(SmallInteger, ForeignKey("info_cod.unitlitoT.codlitoT"))
    note         = Column(String(254))

    pozzo        = relationship("Pozzo", backref="unita_litotermiche")
    litoterm_rel = relationship("UnitLitoT")


class Mineralizzazioni(Base):
    """Mineralizzazioni dei fluidi per intervallo di profondità"""
    __tablename__ = "mineralizzazioni"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    oid        = Column(Integer, primary_key=True)
    key        = Column(Integer, ForeignKey("public.pozzi.key"))
    top        = Column(Float)
    bottom     = Column(Float)
    tipo_fluido = Column(SmallInteger, ForeignKey("info_cod.fluido_t.fluido_t"))
    nota       = Column(String(254))

    pozzo      = relationship("Pozzo", backref="mineralizzazioni")
    fluido_rel = relationship("FluidoT")

#questa qui è quella già pronta
class PozziLitologiaStrCronostr(Base):
    """Vista materializzata — unione di litologia, stratigrafia e croostratigrafia"""
    __tablename__ = "pozzi_litologia_str_cronostr"
    __table_args__ = {"schema": "info_pozzi_hydrocarbon"}

    # nota: gid è bigint, usato come PK surrogato
    gid          = Column(BigInteger, primary_key=True)
    #key con FK non so
    key          = Column(Integer, ForeignKey("public.pozzi.key"))
    posiz_interna = Column(BigInteger)
    daprof       = Column(Float)
    aprof        = Column(Float)
    litologia    = Column(String(1000))
    formazione   = Column(String(64))
    eta_sup      = Column(String(64))
    eta_inf      = Column(String(64))
    # nessuna FK esplicita nel DB — è una tabella denormalizzata/vista
