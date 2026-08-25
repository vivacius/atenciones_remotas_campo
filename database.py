import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Boolean, Float,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from passlib.hash import bcrypt
from dotenv import load_dotenv

load_dotenv()

# Soporta obtener la URL desde st.secrets si está en Streamlit Cloud, o de os.getenv localmente
DB_URL = None
try:
    import streamlit as st
    if hasattr(st, "secrets") and "DB_URL" in st.secrets:
        DB_URL = st.secrets["DB_URL"]
except Exception:
    pass

if not DB_URL:
    DB_URL = os.getenv("DB_URL", "sqlite:///data/soporte.db")

engine_kwargs = {}
if DB_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Para PostgreSQL / Supabase en producción
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DB_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios_atenciones"

    id = Column(Integer, primary_key=True)
    usuario = Column(String(80), unique=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(30), nullable=False, default="analista")
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.now)


class Maquina(Base):
    __tablename__ = "maquinas_atenciones"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(80), unique=True, nullable=False)
    descripcion = Column(String(255))
    modelo = Column(String(150))
    tipo = Column(String(100))
    grupo = Column(String(100))
    estado = Column(String(100))
    activa = Column(Boolean, default=True)
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Operario(Base):
    __tablename__ = "operarios_atenciones"

    id = Column(Integer, primary_key=True)
    codigo = Column(String(80), unique=True, nullable=False)
    nombre = Column(String(180), nullable=False)
    credencial = Column(String(100))
    cargo = Column(String(120))
    idioma = Column(String(80))
    unidad = Column(String(100))
    estado = Column(String(80))
    activo = Column(Boolean, default=True)
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Caso(Base):
    """
    Caso de soporte. La criticidad se asigna automáticamente según la categoría.
    Un caso empieza en estado 'Abierto' y se gestiona mediante registros en Gestion.
    """
    __tablename__ = "casos_atenciones"

    id = Column(Integer, primary_key=True)
    consecutivo = Column(String(40), unique=True, nullable=False)
    fecha_apertura = Column(DateTime, default=datetime.now, nullable=False)

    maquina_id = Column(Integer, ForeignKey("maquinas_atenciones.id"), nullable=False)
    operario_id = Column(Integer, ForeignKey("operarios_atenciones.id"), nullable=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios_atenciones.id"), nullable=False)

    origen = Column(String(80), default="Llamada saliente")
    categoria = Column(String(120), nullable=False)
    criticidad = Column(String(30), default="Media")   # auto-calculado
    problema = Column(Text, nullable=False)
    estado = Column(String(40), default="Abierto")

    requiere_seguimiento = Column(Boolean, default=False)
    fecha_proximo_seguimiento = Column(DateTime, nullable=True)

    escalado_a = Column(String(150))
    fecha_cierre = Column(DateTime, nullable=True)
    solucion_final = Column(Text)
    observaciones = Column(Text)

    maquina = relationship("Maquina")
    operario = relationship("Operario")
    creado_por = relationship("Usuario")
    gestiones = relationship("Gestion", back_populates="caso", cascade="all, delete-orphan")


class Gestion(Base):
    """
    Registro de cada interacción/seguimiento sobre un caso.
    """
    __tablename__ = "gestiones_atenciones"

    id = Column(Integer, primary_key=True)
    caso_id = Column(Integer, ForeignKey("casos_atenciones.id"), nullable=False)
    fecha_hora = Column(DateTime, default=datetime.now, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios_atenciones.id"), nullable=False)

    tipo_contacto = Column(String(80), default="Llamada saliente")
    resultado_contacto = Column(String(80))
    duracion_minutos = Column(Float, default=0)
    detalle = Column(Text, nullable=False)
    solucion_indicada = Column(Text)
    estado_resultante = Column(String(40))
    requiere_nueva_gestion = Column(Boolean, default=False)
    fecha_nueva_gestion = Column(DateTime, nullable=True)

    caso = relationship("Caso", back_populates="gestiones")
    usuario = relationship("Usuario")


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        try:
            import streamlit as st
            admin_user = st.secrets.get(
                "ADMIN_USER",
                os.getenv("ADMIN_USER", "admin")
            )
            admin_password = st.secrets.get(
                "ADMIN_PASSWORD",
                os.getenv("ADMIN_PASSWORD", "Cambiar_Esta_Clave_2026")
            )
        except Exception:
            admin_user = os.getenv("ADMIN_USER", "admin")
            admin_password = os.getenv(
                "ADMIN_PASSWORD",
                "Cambiar_Esta_Clave_2026"
            )

        existe = (
            db.query(Usuario)
            .filter(Usuario.usuario == admin_user)
            .first()
        )

        if not existe:
            db.add(
                Usuario(
                    usuario=admin_user,
                    nombre="Administrador",
                    password_hash=bcrypt.hash(admin_password),
                    rol="administrador",
                    activo=True,
                )
            )
            db.commit()

    finally:
        db.close()


def get_db():
    return SessionLocal()
