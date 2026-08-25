import os
import io
import base64
from datetime import datetime, timedelta, time

import streamlit as st
import pandas as pd
import plotly.express as px
from passlib.hash import bcrypt
from dotenv import load_dotenv

from database import init_db, get_db, Maquina, Operario, Caso, Gestion, Usuario
from utils import (
    CATEGORIAS, ESTADOS_CASO, ESTADOS_ABIERTOS, TIPOS_CONTACTO,
    RESULTADOS_CONTACTO, COLOR_CRITICIDAD, COLOR_ESTADO,
    criticidad_por_categoria, generar_consecutivo,
    autenticar, importar_maquinas, importar_operarios,
)

load_dotenv()
init_db()

# ─── Configuración de página ──────────────────────────────────────────────────

APP_NAME   = "Sistema de Gestión de Atenciones Remotas"
APP_SUB    = "Ingenio Providencia"
LOGO_PATH  = os.path.join(os.path.dirname(__file__), "logo_ipsa.JPG")
ICO_PATH   = os.path.join(os.path.dirname(__file__), "logo_ipsa.ico")


def _logo_b64():
    """Devuelve el logo en base64 para incrustarlo en HTML sin depender de servidor."""
    try:
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


LOGO_B64 = _logo_b64()

st.set_page_config(
    page_title=APP_NAME,
    page_icon=ICO_PATH if os.path.exists(ICO_PATH) else "🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS Corporativo Providencia ──────────────────────────────────────────────
# Paleta: verde corporativo #4BAE4B, amarillo/naranja acento #F5A623,
#         texto oscuro #1C3A1C, fondo claro #F4F8F4
# SIN Google Fonts — usa stack de sistema seguro (Segoe UI / system-ui)

st.markdown("""
<style>
/* Fuentes del sistema — sin petición externa */
:root {
    --verde:        #4BAE4B;
    --verde-dark:   #2d7a2d;
    --verde-darker: #1C3A1C;
    --verde-light:  #6ec46e;
    --acento:       #F5A623;
    --acento-dk:    #d4841a;
    --gris-bg:      #F4F8F4;
    --gris-card:    #ffffff;
    --gris-border:  #d8e8d8;
    --texto:        #1C3A1C;
    --texto-soft:   #4a6a4a;
    --texto-muted:  #7a9a7a;
    --shadow-sm:    0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.04);
    --shadow-md:    0 4px 14px rgba(0,0,0,.10), 0 2px 4px rgba(0,0,0,.06);
    --radius:       10px;
    --font:         "Segoe UI", system-ui, -apple-system, Arial, sans-serif;
}

* { font-family: var(--font) !important; box-sizing: border-box; }

/* Ocultar chrome de Streamlit */
#MainMenu, footer, header { visibility: hidden; height: 0; }
[data-testid="stSidebarNav"]   { display: none !important; }
[data-testid="collapsedControl"]{ display: none !important; }
section[data-testid="stSidebar"]{ display: none !important; }

/* Fondo y contenedor */
.stApp { background: var(--gris-bg) !important; }
.block-container {
    padding: 0.8rem 1.6rem 3rem 1.6rem !important;
    max-width: 1380px !important;
}

/* ── HEADER ── */
.corp-header {
    background: linear-gradient(120deg, var(--verde-darker) 0%, var(--verde-dark) 55%, var(--verde) 100%);
    border-radius: var(--radius);
    padding: 14px 24px;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow-md);
    flex-wrap: wrap;
    gap: 10px;
}
/* Logo: sin filtro para mantener colores originales */
.corp-header-logo {
    height: 46px;
    width: auto;
    object-fit: contain;
    border-radius: 4px;
    background: white;
    padding: 4px 8px;
    display: block;
}
/* Centro: título grande centrado */
.corp-header-center {
    flex: 1;
    text-align: center;
    padding: 0 16px;
}
.corp-header-center h1 {
    color: white !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    margin: 0 0 3px 0 !important;
    letter-spacing: -0.3px;
    line-height: 1.2;
    text-shadow: 0 1px 3px rgba(0,0,0,.2);
}
.corp-header-center .sub {
    color: rgba(255,255,255,.70);
    font-size: 0.75rem;
    font-weight: 400;
}
/* Derecha: usuario + botón salir */
.corp-header-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.user-badge {
    background: rgba(255,255,255,.13);
    border: 1px solid rgba(255,255,255,.22);
    border-radius: 50px;
    padding: 5px 14px;
    color: white;
    font-size: 0.78rem;
    font-weight: 500;
    white-space: nowrap;
}
.logout-btn {
    background: rgba(255,255,255,.15);
    border: 1.5px solid rgba(255,255,255,.35);
    border-radius: 8px;
    padding: 6px 14px;
    color: white !important;
    text-decoration: none !important;
    font-size: 0.78rem;
    font-weight: 600;
    transition: background .18s, border-color .18s;
    white-space: nowrap;
    cursor: pointer;
}
.logout-btn:hover {
    background: rgba(255,255,255,.28);
    border-color: rgba(255,255,255,.6);
    color: white !important;
}

/* ── TABS ── */
[data-testid="stTabs"] > div:first-child {
    background: white;
    border-radius: var(--radius);
    padding: 4px 6px;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--gris-border);
    margin-bottom: 1rem;
    flex-wrap: wrap !important;
}
button[data-baseweb="tab"] {
    border-radius: 7px !important;
    padding: 6px 14px !important;
    font-size: 0.80rem !important;
    font-weight: 500 !important;
    color: var(--texto-soft) !important;
    background: transparent !important;
    border: none !important;
    transition: all .18s ease !important;
    white-space: nowrap !important;
}
button[data-baseweb="tab"]:hover {
    background: var(--gris-bg) !important;
    color: var(--verde-dark) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: var(--verde) !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 6px rgba(75,174,75,.35) !important;
}
[data-testid="stTabContent"] { padding-top: 0.4rem !important; }

/* ── MÉTRICAS ── */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid var(--gris-border) !important;
    border-radius: var(--radius) !important;
    padding: 14px 18px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow .2s, transform .2s;
}
[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px);
}
[data-testid="metric-container"] label {
    color: var(--texto-muted) !important;
    font-size: 0.70rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: .6px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--verde-darker) !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
}

/* ── FORMULARIOS ── */
[data-testid="stForm"] {
    background: white !important;
    border: 1px solid var(--gris-border) !important;
    border-radius: var(--radius) !important;
    padding: 22px !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── BOTONES ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    transition: all .18s ease !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: var(--verde) !important;
    color: white !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--verde-dark) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(75,174,75,.35) !important;
}
[data-testid="baseButton-secondary"] {
    border: 1.5px solid var(--verde) !important;
    color: var(--verde-dark) !important;
    background: white !important;
}
[data-testid="stDownloadButton"] button {
    background: var(--verde) !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: none !important;
}

/* ── SECTION TITLE ── */
.section-title {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.1px;
    color: var(--verde-dark);
    border-bottom: 2px solid var(--acento);
    padding-bottom: 5px;
    margin: 18px 0 12px 0;
}

/* ── INFO PANEL ── */
.info-panel {
    background: linear-gradient(135deg, #eef6ee, #e5f1e5);
    border-left: 4px solid var(--verde);
    border-radius: var(--radius);
    padding: 13px 17px;
    margin: 8px 0 14px 0;
    font-size: 0.84rem;
    color: var(--texto);
    line-height: 1.65;
}

/* ── ALERTAS ── */
[data-testid="stAlert"] { border-radius: var(--radius) !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid var(--gris-border) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── DIVIDER ── */
hr { border-color: var(--gris-border) !important; margin: 14px 0 !important; }

/* ── SELECT / INPUT ── */
[data-testid="stSelectbox"] > div,
[data-testid="stTextInput"] > div { border-radius: 8px !important; }

/* ── LOGIN ── */
.login-wrap {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 80vh;
    padding-top: 60px;
}
.login-box {
    width: 100%;
    max-width: 400px;
    background: white;
    border-radius: 16px;
    padding: 36px 36px 30px 36px;
    box-shadow: 0 8px 32px rgba(0,0,0,.12);
    border: 1px solid var(--gris-border);
}
.login-header {
    text-align: center;
    margin-bottom: 24px;
}
.login-header img {
    height: 52px;
    margin-bottom: 12px;
}
.login-header h2 {
    color: var(--verde-darker) !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    margin: 0 0 4px 0 !important;
}
.login-header p {
    color: var(--texto-muted);
    font-size: 0.78rem;
    margin: 0;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
    .block-container { padding: 0.6rem 0.8rem 2rem 0.8rem !important; }
    .corp-header { padding: 12px 14px; }
    .corp-header-center h1 { font-size: 1.05rem !important; }
    .corp-header-center { padding: 0 8px; }
    button[data-baseweb="tab"] { padding: 5px 9px !important; font-size: 0.74rem !important; }
    [data-testid="metric-container"] { padding: 10px 12px !important; }
}
@media (max-width: 480px) {
    .corp-header-logo { height: 32px; }
    .user-badge { display: none; }
    .corp-header-center h1 { font-size: 0.9rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ─── Session state ────────────────────────────────────────────────────────────

for k, v in [("usuario_id", None), ("usuario_nombre", None), ("usuario_rol", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Logout vía query param ───────────────────────────────────────────────────
# El botón Salir del header usa href="?__logout=1" para disparar este bloque
if st.query_params.get("__logout") == "1":
    for k in ["usuario_id", "usuario_nombre", "usuario_rol"]:
        st.session_state[k] = None
    st.query_params.clear()
    st.rerun()


# ─── LOGIN ───────────────────────────────────────────────────────────────────

def pagina_login():
    logo_tag = (
        f'<img src="data:image/jpeg;base64,{LOGO_B64}" class="login-header-logo" '
        f'style="height:54px;margin-bottom:10px;">'
        if LOGO_B64 else '<div style="font-size:2.5rem">🌿</div>'
    )
    st.markdown(f"""
    <div style="display:flex;justify-content:center;padding-top:50px;">
      <div style="width:100%;max-width:400px;background:white;border-radius:16px;
                  padding:36px;box-shadow:0 8px 32px rgba(0,0,0,.12);
                  border:1px solid #d8e8d8;">
        <div style="text-align:center;margin-bottom:22px;">
          {logo_tag}
          <h2 style="color:#1C3A1C;font-weight:700;font-size:1.05rem;margin:6px 0 3px 0;">
            {APP_NAME}
          </h2>
          <p style="color:#7a9a7a;font-size:0.76rem;margin:0;">{APP_SUB}</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        with st.form("login", clear_on_submit=False):
            usuario = st.text_input("Usuario")
            clave   = st.text_input("Contraseña", type="password")
            ingresar = st.form_submit_button("Ingresar →", use_container_width=True, type="primary")

        if ingresar:
            db = get_db()
            try:
                user = autenticar(db, usuario.strip(), clave)
                if user:
                    st.session_state.usuario_id     = user.id
                    st.session_state.usuario_nombre = user.nombre
                    st.session_state.usuario_rol    = user.rol
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            finally:
                db.close()


if not st.session_state.usuario_id:
    pagina_login()
    st.stop()


# ─── HEADER CORPORATIVO ───────────────────────────────────────────────────────
# Todo el header está en un solo bloque HTML. El logout usa ?__logout=1
# para evitar la limitación de no poder poner st.button dentro de HTML.

logo_src = f'data:image/jpeg;base64,{LOGO_B64}' if LOGO_B64 else ""
logo_html = (
    f'<img src="{logo_src}" class="corp-header-logo" alt="Providencia">'
    if logo_src else '<span style="font-size:1.8rem;filter:none;">🌿</span>'
)

st.markdown(f"""
<div class="corp-header">
  <!-- Izquierda: logo -->
  <div>
    {logo_html}
  </div>
  <!-- Centro: título -->
  <div class="corp-header-center">
    <h1>{APP_NAME}</h1>
    <div class="sub">{APP_SUB}</div>
  </div>
  <!-- Derecha: usuario + salir -->
  <div class="corp-header-right">
    <div class="user-badge">
      👤 {st.session_state.usuario_nombre}
      &nbsp;·&nbsp;
      <span style="opacity:.65;font-size:.72rem">{st.session_state.usuario_rol}</span>
    </div>
    <a href="?__logout=1" class="logout-btn">🚪 Salir</a>
  </div>
</div>
""", unsafe_allow_html=True)


# ─── TABS ─────────────────────────────────────────────────────────────────────
# Orden: Casos y Pendientes · Nuevo Caso · Registrar Gestión · Detalle · Indicadores · Usuarios · Maestros

tabs_labels = [
    "📋 Casos y Pendientes",
    "➕ Nuevo Caso",
    "📞 Registrar Gestión",
    "🔎 Detalle del Caso",
    "📊 Indicadores",
]

if st.session_state.usuario_rol == "administrador":
    tabs_labels += ["👥 Usuarios", "📥 Maestros"]
else:
    tabs_labels += ["📥 Maestros"]

tabs = st.tabs(tabs_labels)

# Índices dinámicos
IDX_CASOS    = 0
IDX_NUEVO    = 1
IDX_GESTION  = 2
IDX_DETALLE  = 3
IDX_IND      = 4
IDX_USUARIOS = 5 if st.session_state.usuario_rol == "administrador" else None
IDX_MAESTROS = 6 if st.session_state.usuario_rol == "administrador" else 5


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — CASOS Y PENDIENTES  (dashboard + listado + pendientes)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[IDX_CASOS]:
    db = get_db()
    try:
        hoy = datetime.now().date()

        # ── KPIs globales (siempre visibles arriba) ──
        todos = db.query(Caso).all()
        abiertos_g   = [c for c in todos if c.estado in ESTADOS_ABIERTOS]
        vencidos_g   = [
            c for c in todos
            if c.requiere_seguimiento
            and c.estado in ESTADOS_ABIERTOS
            and c.fecha_proximo_seguimiento
            and c.fecha_proximo_seguimiento.date() < hoy
        ]
        prox_hoy_g   = [
            c for c in todos
            if c.requiere_seguimiento
            and c.estado in ESTADOS_ABIERTOS
            and c.fecha_proximo_seguimiento
            and c.fecha_proximo_seguimiento.date() == hoy
        ]
        semana_g     = [c for c in todos if c.fecha_apertura.date() >= hoy - timedelta(days=7)]

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Casos abiertos",         len(abiertos_g))
        k2.metric("Seguimientos hoy",        len(prox_hoy_g))
        k3.metric("Seguimientos vencidos",   len(vencidos_g),
                  delta=f"-{len(vencidos_g)}" if vencidos_g else None,
                  delta_color="inverse")
        k4.metric("Casos últimos 7 días",    len(semana_g))

        # ── Alerta de vencidos ──
        if vencidos_g:
            st.markdown('<div class="section-title">⚠️ Seguimientos vencidos</div>', unsafe_allow_html=True)
            dfv = pd.DataFrame([{
                "Caso":             c.consecutivo,
                "Máquina":          str(c.maquina.codigo),
                "Operario":         c.operario.nombre if c.operario else "—",
                "Categoría":        c.categoria,
                "Criticidad":       c.criticidad,
                "Fecha prog.":      c.fecha_proximo_seguimiento.strftime("%d/%m/%Y %H:%M"),
                "Estado":           c.estado,
            } for c in sorted(vencidos_g, key=lambda x: x.fecha_proximo_seguimiento)])
            st.dataframe(dfv, use_container_width=True, hide_index=True)

        st.divider()

        # ── Filtros ──
        st.markdown('<div class="section-title">Filtros</div>', unsafe_allow_html=True)
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)

        estados_f = ["Todos"] + ESTADOS_CASO
        f_estado = fc1.selectbox("Estado", estados_f, key="cp_estado")
        f_desde  = fc2.date_input("Desde", value=(datetime.now() - timedelta(days=30)).date(), key="cp_desde")
        f_hasta  = fc3.date_input("Hasta", value=datetime.now().date(), key="cp_hasta")

        maquinas_all  = db.query(Maquina).order_by(Maquina.codigo).all()
        operarios_all = db.query(Operario).order_by(Operario.nombre).all()
        f_maq = fc4.selectbox("🚜 Máquina", ["Todas"] + [str(m.codigo) for m in maquinas_all], key="cp_maq")
        f_op  = fc5.selectbox("👷 Operario", ["Todos"] + [o.nombre for o in operarios_all], key="cp_op")

        q = db.query(Caso).filter(
            Caso.fecha_apertura >= datetime.combine(f_desde, datetime.min.time()),
            Caso.fecha_apertura <= datetime.combine(f_hasta, datetime.max.time()),
        )
        if f_estado != "Todos":
            q = q.filter(Caso.estado == f_estado)
        if f_maq != "Todas":
            maq_obj = db.query(Maquina).filter(Maquina.codigo == f_maq).first()
            if maq_obj:
                q = q.filter(Caso.maquina_id == maq_obj.id)
        if f_op != "Todos":
            op_obj = db.query(Operario).filter(Operario.nombre == f_op).first()
            if op_obj:
                q = q.filter(Caso.operario_id == op_obj.id)

        casos_f = q.order_by(Caso.fecha_apertura.desc()).all()

        # Sub-KPIs del filtro
        sk1, sk2, sk3, sk4 = st.columns(4)
        sk1.metric("Resultados filtro",  len(casos_f))
        sk2.metric("Abiertos",           sum(1 for c in casos_f if c.estado in ESTADOS_ABIERTOS))
        sk3.metric("Solucionados",        sum(1 for c in casos_f if c.estado == "Solucionado"))
        sk4.metric("Con seguimiento",     sum(1 for c in casos_f if c.requiere_seguimiento and c.estado in ESTADOS_ABIERTOS))

        # ── Listado ──
        st.markdown('<div class="section-title">Listado de casos</div>', unsafe_allow_html=True)
        if casos_f:
            df = pd.DataFrame([{
                "Caso":              c.consecutivo,
                "Fecha apertura":    c.fecha_apertura.strftime("%d/%m/%Y %H:%M"),
                "Máquina":           str(c.maquina.codigo),
                "Operario":          c.operario.nombre if c.operario else "—",
                "Categoría":         c.categoria,
                "Criticidad":        c.criticidad,
                "Estado":            c.estado,
                "# Gestiones":       len(c.gestiones),
                "Próx. seguimiento": c.fecha_proximo_seguimiento.strftime("%d/%m/%Y") if c.fecha_proximo_seguimiento else "—",
            } for c in casos_f])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ No hay casos con los filtros seleccionados.")

        # ── Pendientes del filtro ──
        pendientes_f = [
            c for c in casos_f
            if c.requiere_seguimiento
            and c.estado in ESTADOS_ABIERTOS
            and c.fecha_proximo_seguimiento
        ]
        st.markdown('<div class="section-title">📅 Pendientes de seguimiento en el filtro</div>', unsafe_allow_html=True)
        if pendientes_f:
            dfp = pd.DataFrame([{
                "Caso":              c.consecutivo,
                "Máquina":           str(c.maquina.codigo),
                "Operario":          c.operario.nombre if c.operario else "—",
                "Fecha programada":  c.fecha_proximo_seguimiento.strftime("%d/%m/%Y %H:%M"),
                "Vencido":           "⚠️ Sí" if c.fecha_proximo_seguimiento.date() < hoy else "✅ No",
                "Estado":            c.estado,
                "Responsable":       c.creado_por.nombre,
            } for c in sorted(pendientes_f, key=lambda x: x.fecha_proximo_seguimiento)])
            st.dataframe(dfp, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Sin pendientes de seguimiento en el período filtrado.")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NUEVO CASO
# ══════════════════════════════════════════════════════════════════════════════
with tabs[IDX_NUEVO]:
    db = get_db()
    try:
        maquinas = (
            db.query(Maquina)
            .filter(Maquina.activa.is_(True))
            .order_by(Maquina.codigo)
            .all()
        )
        operarios = (
            db.query(Operario)
            .filter(Operario.activo.is_(True))
            .order_by(Operario.nombre)
            .all()
        )

        if not maquinas:
            st.warning(
                "⚠️ Primero importe el archivo maestro de máquinas "
                "en la pestaña **Maestros**."
            )
        else:
            maquina_map = {f"{m.codigo} — {m.descripcion}": m for m in maquinas}
            operario_map = {f"{o.codigo} — {o.nombre}": o for o in operarios}

            with st.form("nuevo_caso", clear_on_submit=True):
                st.markdown(
                    '<div class="section-title">1. Identificación</div>',
                    unsafe_allow_html=True
                )

                c1, c2, c3 = st.columns([3, 1, 1])
                maquina_txt = c1.selectbox(
                    "🚜 Cosechadora *",
                    list(maquina_map.keys()),
                    index=None,
                    placeholder="Seleccione..."
                )
                fecha = c2.date_input("📅 Fecha", value=datetime.now().date())
                hora = c3.time_input(
                    "🕐 Hora",
                    value=datetime.now().time().replace(second=0, microsecond=0)
                )

                c1, c2 = st.columns(2)
                operario_txt = c1.selectbox(
                    "👷 Operario contactado",
                    list(operario_map.keys()),
                    index=None,
                    placeholder="Opcional..."
                )
                origen = c2.selectbox("📡 Canal de contacto", TIPOS_CONTACTO)

                st.markdown(
                    '<div class="section-title">2. Caracterización del problema</div>',
                    unsafe_allow_html=True
                )
                categoria = st.selectbox("📂 Categoría *", CATEGORIAS)
                criticidad_auto = criticidad_por_categoria(categoria)

                col_crit, _ = st.columns([1, 3])
                col_crit.info(
                    f"🎯 Criticidad asignada automáticamente: **{criticidad_auto}**"
                )

                problema = st.text_area(
                    "📝 Descripción del problema *",
                    height=120,
                    placeholder="Describa con claridad el problema reportado o detectado..."
                )
                observaciones = st.text_area(
                    "💬 Observaciones adicionales",
                    height=75,
                    placeholder="Contexto, antecedentes, información extra..."
                )

                st.markdown(
                    '<div class="section-title">3. Seguimiento (opcional)</div>',
                    unsafe_allow_html=True
                )
                requiere = st.checkbox("📅 Programar seguimiento")

                c1, c2 = st.columns(2)
                fecha_seg = c1.date_input(
                    "Fecha seguimiento",
                    value=datetime.now().date(),
                    disabled=not requiere
                )
                hora_seg = c2.time_input(
                    "Hora seguimiento",
                    value=time(8, 0),
                    disabled=not requiere
                )

                guardar = st.form_submit_button(
                    "✅ Crear caso",
                    use_container_width=True,
                    type="primary"
                )

            if guardar:
                if not maquina_txt or not problema.strip():
                    st.error("⚠️ Seleccione la cosechadora y describa el problema.")
                else:
                    maquina = maquina_map[maquina_txt]
                    operario = operario_map.get(operario_txt) if operario_txt else None
                    fecha_hora = datetime.combine(fecha, hora)
                    proximo = datetime.combine(fecha_seg, hora_seg) if requiere else None

                    caso = Caso(
                        consecutivo=generar_consecutivo(db),
                        fecha_apertura=fecha_hora,
                        maquina_id=maquina.id,
                        operario_id=operario.id if operario else None,
                        creado_por_id=st.session_state.usuario_id,
                        origen=origen,
                        categoria=categoria,
                        criticidad=criticidad_auto,
                        problema=problema.strip(),
                        estado="Abierto",
                        requiere_seguimiento=requiere,
                        fecha_proximo_seguimiento=proximo,
                        observaciones=observaciones.strip(),
                    )

                    db.add(caso)
                    db.commit()

                    st.success(
                        f"✅ Caso creado: **{caso.consecutivo}** — "
                        f"Criticidad: **{criticidad_auto}**"
                    )
                    st.balloons()
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — REGISTRAR GESTIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[IDX_GESTION]:
    db = get_db()
    try:
        st.markdown('<div class="section-title">Filtrar casos abiertos</div>', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        maquinas_act  = db.query(Maquina).filter(Maquina.activa.is_(True)).order_by(Maquina.codigo).all()
        operarios_act = db.query(Operario).filter(Operario.activo.is_(True)).order_by(Operario.nombre).all()

        filtro_maq = fc1.selectbox(
            "🚜 Filtrar por máquina",
            ["Todas"] + [f"{str(m.codigo)} — {m.descripcion}" for m in maquinas_act],
            key="gest_maq_filter"
        )
        filtro_op = fc2.selectbox(
            "👷 Filtrar por operario",
            ["Todos"] + [f"{o.codigo} — {o.nombre}" for o in operarios_act],
            key="gest_op_filter"
        )

        q = db.query(Caso).filter(Caso.estado.in_(ESTADOS_ABIERTOS))
        if filtro_maq != "Todas":
            codigo_maq = filtro_maq.split(" — ")[0]
            maq_obj = db.query(Maquina).filter(Maquina.codigo == codigo_maq).first()
            if maq_obj:
                q = q.filter(Caso.maquina_id == maq_obj.id)
        if filtro_op != "Todos":
            codigo_op = filtro_op.split(" — ")[0]
            op_obj = db.query(Operario).filter(Operario.codigo == codigo_op).first()
            if op_obj:
                q = q.filter(Caso.operario_id == op_obj.id)

        casos = q.order_by(Caso.fecha_apertura.desc()).all()

        if not casos:
            st.info("ℹ️ No hay casos abiertos con ese filtro.")
        else:
            opciones = {
                f"{c.consecutivo}  ·  {str(c.maquina.codigo)}  ·  {c.categoria}  ·  [{c.estado}]": c
                for c in casos
            }
            seleccionado = st.selectbox("📋 Seleccione el caso", list(opciones.keys()),
                                        index=None, placeholder="Elija un caso...")

            if seleccionado:
                caso = opciones[seleccionado]
                st.markdown(f"""
                <div class="info-panel">
                    <b>🚜 Máquina:</b> {str(caso.maquina.codigo)} — {caso.maquina.descripcion}<br>
                    <b>👷 Operario:</b> {caso.operario.nombre if caso.operario else 'No definido'}<br>
                    <b>📝 Problema:</b> {caso.problema}<br>
                    <b>🎯 Criticidad:</b> {caso.criticidad} &nbsp;·&nbsp; <b>Estado:</b> {caso.estado}
                </div>
                """, unsafe_allow_html=True)

                with st.form("gestion", clear_on_submit=True):
                    st.markdown('<div class="section-title">Registro de la gestión</div>', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns(3)
                    fecha    = c1.date_input("📅 Fecha", value=datetime.now().date())
                    hora     = c2.time_input("🕐 Hora", value=datetime.now().time().replace(second=0, microsecond=0))
                    duracion = c3.number_input("⏱️ Duración (min)", min_value=0.0, step=1.0, value=0.0)

                    c1, c2   = st.columns(2)
                    tipo     = c1.selectbox("📡 Tipo de contacto", TIPOS_CONTACTO)
                    resultado= c2.selectbox("✅ Resultado del contacto", RESULTADOS_CONTACTO)

                    detalle  = st.text_area("📝 Detalle de la gestión *", height=110,
                                            placeholder="Qué se hizo, qué indicó el operario, qué se verificó...")
                    solucion = st.text_area("💡 Solución o instrucción indicada", height=85,
                                            placeholder="Pasos dados, instrucción entregada al operario...")

                    st.markdown('<div class="section-title">Estado y seguimiento</div>', unsafe_allow_html=True)
                    c1, c2       = st.columns(2)
                    nuevo_estado = c1.selectbox("🔄 Nuevo estado del caso", ESTADOS_CASO,
                                               index=ESTADOS_CASO.index(caso.estado) if caso.estado in ESTADOS_CASO else 0)
                    requiere     = c2.checkbox("📅 Requiere nueva gestión")

                    c1, c2   = st.columns(2)
                    f_seg    = c1.date_input("Fecha próxima gestión", value=datetime.now().date(), disabled=not requiere)
                    h_seg    = c2.time_input("Hora próxima gestión",  value=time(8, 0),            disabled=not requiere)

                    cerrando = nuevo_estado in ["Solucionado", "Cerrado sin solución"]
                    solucion_final = st.text_area(
                        "🏁 Solución final del caso", height=85,
                        disabled=not cerrando,
                        placeholder="Complete al cerrar el caso..." if cerrando else "Solo se habilita al cerrar",
                    )
                    guardar = st.form_submit_button("💾 Guardar gestión", use_container_width=True, type="primary")

                if guardar:
                    if not detalle.strip():
                        st.error("⚠️ Debe registrar el detalle de la gestión.")
                    else:
                        fecha_hora = datetime.combine(fecha, hora)
                        proximo    = datetime.combine(f_seg, h_seg) if requiere else None

                        gestion = Gestion(
                            caso_id              = caso.id,
                            fecha_hora           = fecha_hora,
                            usuario_id           = st.session_state.usuario_id,
                            tipo_contacto        = tipo,
                            resultado_contacto   = resultado,
                            duracion_minutos     = duracion,
                            detalle              = detalle.strip(),
                            solucion_indicada    = solucion.strip(),
                            estado_resultante    = nuevo_estado,
                            requiere_nueva_gestion = requiere,
                            fecha_nueva_gestion  = proximo,
                        )
                        db.add(gestion)

                        caso.estado                    = nuevo_estado
                        caso.requiere_seguimiento      = requiere
                        caso.fecha_proximo_seguimiento = proximo

                        if cerrando:
                            caso.fecha_cierre  = fecha_hora
                            caso.solucion_final= solucion_final.strip() or solucion.strip()
                        else:
                            caso.fecha_cierre  = None

                        db.commit()
                        st.success("✅ Gestión registrada correctamente.")
                        st.rerun()
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — DETALLE DEL CASO
# ══════════════════════════════════════════════════════════════════════════════
with tabs[IDX_DETALLE]:
    db = get_db()
    try:
        st.markdown('<div class="section-title">Buscar caso</div>', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        maquinas_det  = db.query(Maquina).order_by(Maquina.codigo).all()
        operarios_det = db.query(Operario).order_by(Operario.nombre).all()

        det_maq = fc1.selectbox(
            "🚜 Filtrar por máquina",
            ["Todas"] + [f"{str(m.codigo)} — {m.descripcion}" for m in maquinas_det],
            key="det_maq"
        )
        det_op = fc2.selectbox(
            "👷 Filtrar por operario",
            ["Todos"] + [f"{o.codigo} — {o.nombre}" for o in operarios_det],
            key="det_op"
        )

        q = db.query(Caso)
        if det_maq != "Todas":
            cod = det_maq.split(" — ")[0]
            maq_obj = db.query(Maquina).filter(Maquina.codigo == cod).first()
            if maq_obj:
                q = q.filter(Caso.maquina_id == maq_obj.id)
        if det_op != "Todos":
            cod = det_op.split(" — ")[0]
            op_obj = db.query(Operario).filter(Operario.codigo == cod).first()
            if op_obj:
                q = q.filter(Caso.operario_id == op_obj.id)

        casos_det = q.order_by(Caso.fecha_apertura.desc()).all()
        opciones  = {f"{c.consecutivo}  ·  {str(c.maquina.codigo)}  ·  {c.estado}": c for c in casos_det}

        seleccionado = st.selectbox("📋 Seleccione caso", list(opciones.keys()),
                                    index=None, placeholder="Elija un caso...")

        if seleccionado:
            c = opciones[seleccionado]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Caso",      c.consecutivo)
            m2.metric("Máquina",   str(c.maquina.codigo))
            m3.metric("Estado",    c.estado)
            m4.metric("Gestiones", len(c.gestiones))

            st.markdown(f"""
            <div class="info-panel">
                <b>📂 Categoría:</b> {c.categoria} &nbsp;·&nbsp; <b>🎯 Criticidad:</b> {c.criticidad}<br>
                <b>👷 Operario:</b> {c.operario.nombre if c.operario else '—'} &nbsp;·&nbsp;
                <b>📡 Origen:</b> {c.origen}<br>
                <b>📅 Apertura:</b> {c.fecha_apertura.strftime('%d/%m/%Y %H:%M')}
                {'&nbsp;·&nbsp; <b>🔒 Cierre:</b> ' + c.fecha_cierre.strftime('%d/%m/%Y %H:%M') if c.fecha_cierre else ''}<br>
                <b>📝 Problema:</b> {c.problema}
                {'<br><b>🏁 Solución final:</b> ' + c.solucion_final if c.solucion_final else ''}
                {'<br><b>💬 Observaciones:</b> ' + c.observaciones if c.observaciones else ''}
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-title">Historial de gestiones</div>', unsafe_allow_html=True)
            gestiones_det = sorted(c.gestiones, key=lambda x: x.fecha_hora, reverse=True)

            if gestiones_det:
                df = pd.DataFrame([{
                    "Fecha":            g.fecha_hora.strftime("%d/%m/%Y %H:%M"),
                    "Analista":         g.usuario.nombre,
                    "Canal":            g.tipo_contacto,
                    "Resultado":        g.resultado_contacto,
                    "Duración (min)":   g.duracion_minutos,
                    "Estado resultante":g.estado_resultante,
                    "Detalle":          g.detalle,
                    "Solución indicada":g.solucion_indicada or "—",
                    "Próx. gestión":    g.fecha_nueva_gestion.strftime("%d/%m/%Y") if g.fecha_nueva_gestion else "—",
                } for g in gestiones_det])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Este caso aún no tiene gestiones registradas.")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — INDICADORES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[IDX_IND]:
    db = get_db()
    try:
        c1, c2 = st.columns(2)
        desde_ind = c1.date_input("Desde", value=(datetime.now() - timedelta(days=30)).date(), key="ind_desde")
        hasta_ind = c2.date_input("Hasta", value=datetime.now().date(), key="ind_hasta")

        inicio = datetime.combine(desde_ind, datetime.min.time())
        fin    = datetime.combine(hasta_ind, datetime.max.time())

        casos_ind    = db.query(Caso).filter(Caso.fecha_apertura.between(inicio, fin)).all()
        gestiones_ind= db.query(Gestion).filter(Gestion.fecha_hora.between(inicio, fin)).all()

        total_c      = len(casos_ind)
        solucionados = sum(c.estado == "Solucionado" for c in casos_ind)
        pendientes_i = sum(c.estado in ESTADOS_ABIERTOS for c in casos_ind)
        llamadas_c   = len(gestiones_ind)
        minutos_c    = sum(g.duracion_minutos or 0 for g in gestiones_ind)
        maquinas_i   = len(set(c.maquina_id for c in casos_ind))
        tasa         = (solucionados / total_c * 100) if total_c else 0

        kols = st.columns(6)
        kols[0].metric("Casos",        total_c)
        kols[1].metric("Gestiones",    llamadas_c)
        kols[2].metric("Solucionados", solucionados)
        kols[3].metric("Pendientes",   pendientes_i)
        kols[4].metric("Máquinas",     maquinas_i)
        kols[5].metric("% Solución",   f"{tasa:.1f}%")

        if minutos_c > 0:
            st.caption(f"⏱️ Tiempo documentado: **{minutos_c:.0f} min** ({minutos_c/60:.1f} h)")

        if casos_ind:
            # cast explícito a string para evitar que pandas lo trate como número
            df_casos = pd.DataFrame([{
                "Caso":          c.consecutivo,
                "Fecha":         c.fecha_apertura,
                "Máquina":       str(c.maquina.codigo),
                "Operario":      c.operario.nombre if c.operario else "",
                "Categoría":     c.categoria,
                "Criticidad":    c.criticidad,
                "Estado":        c.estado,
                "# Gestiones":   len(c.gestiones),
                "Problema":      c.problema,
                "Solución final":c.solucion_final or "",
            } for c in casos_ind])

            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(
                    df_casos.groupby("Categoría").size().reset_index(name="Casos")
                            .sort_values("Casos", ascending=True),
                    x="Casos", y="Categoría", orientation="h",
                    title="Casos por categoría",
                    color_discrete_sequence=["#4BAE4B"],
                )
                fig1.update_layout(paper_bgcolor="white", plot_bgcolor="white",
                                   height=350, font_family="Segoe UI, Arial")
                st.plotly_chart(fig1, use_container_width=True)

            with g2:
                fig3 = px.pie(
                    df_casos.groupby("Estado").size().reset_index(name="Casos"),
                    names="Estado", values="Casos",
                    title="Distribución por estado",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig3.update_layout(paper_bgcolor="white", height=350,
                                   font_family="Segoe UI, Arial")
                st.plotly_chart(fig3, use_container_width=True)

            # Asegurar que el eje X de máquinas sea texto
            df_maq = (
                df_casos.groupby("Máquina").size()
                        .reset_index(name="Casos")
                        .sort_values("Casos", ascending=False)
                        .head(15)
            )
            df_maq["Máquina"] = df_maq["Máquina"].astype(str)

            fig2 = px.bar(
                df_maq, x="Máquina", y="Casos",
                title="Top máquinas con más casos",
                color_discrete_sequence=["#F5A623"],
                text="Casos",
            )
            fig2.update_traces(textposition="outside")
            fig2.update_xaxes(type="category")   # ← fuerza eje categórico (texto)
            fig2.update_layout(paper_bgcolor="white", plot_bgcolor="#fafafa",
                               height=340, font_family="Segoe UI, Arial",
                               xaxis_title="Código de máquina")
            st.plotly_chart(fig2, use_container_width=True)

            # Exportar Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_casos.to_excel(writer, index=False, sheet_name="Casos")
                df_gest = pd.DataFrame([{
                    "Caso":              g.caso.consecutivo,
                    "Fecha":             g.fecha_hora,
                    "Máquina":           str(g.caso.maquina.codigo),
                    "Analista":          g.usuario.nombre,
                    "Canal":             g.tipo_contacto,
                    "Resultado":         g.resultado_contacto,
                    "Duración (min)":    g.duracion_minutos,
                    "Detalle":           g.detalle,
                    "Solución indicada": g.solucion_indicada or "",
                    "Estado resultante": g.estado_resultante,
                } for g in gestiones_ind])
                df_gest.to_excel(writer, index=False, sheet_name="Gestiones")

            st.download_button(
                "📥 Descargar reporte Excel",
                data=buffer.getvalue(),
                file_name=f"reporte_atenciones_remotas_{desde_ind}_{hasta_ind}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.info("ℹ️ No hay casos en el período seleccionado.")
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB — USUARIOS (solo administrador)
# ══════════════════════════════════════════════════════════════════════════════
if IDX_USUARIOS is not None:
    with tabs[IDX_USUARIOS]:
        db = get_db()
        try:
            st.markdown('<div class="section-title">Crear nuevo usuario</div>', unsafe_allow_html=True)
            with st.form("crear_usuario", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nu_usuario = c1.text_input("👤 Nombre de usuario")
                nu_nombre  = c2.text_input("🪪 Nombre completo")
                c3, c4 = st.columns(2)
                nu_clave   = c3.text_input("🔒 Contraseña (mín. 8 car.)", type="password")
                nu_rol     = c4.selectbox("🔑 Rol", ["analista", "administrador"])
                crear = st.form_submit_button("✅ Crear usuario", type="primary")

            if crear:
                if not nu_usuario.strip() or not nu_nombre.strip() or len(nu_clave) < 8:
                    st.error("Complete todos los campos. La contraseña debe tener mínimo 8 caracteres.")
                elif db.query(Usuario).filter(Usuario.usuario == nu_usuario.strip()).first():
                    st.error("⚠️ El nombre de usuario ya existe.")
                else:
                    db.add(Usuario(
                        usuario      = nu_usuario.strip(),
                        nombre       = nu_nombre.strip(),
                        password_hash= bcrypt.hash(nu_clave),
                        rol          = nu_rol,
                        activo       = True,
                    ))
                    db.commit()
                    st.success(f"✅ Usuario **{nu_nombre.strip()}** creado correctamente.")

            st.markdown('<div class="section-title">Usuarios registrados</div>', unsafe_allow_html=True)
            usuarios = db.query(Usuario).order_by(Usuario.nombre).all()
            df_u = pd.DataFrame([{
                "Usuario": u.usuario,
                "Nombre":  u.nombre,
                "Rol":     u.rol,
                "Activo":  "✅" if u.activo else "❌",
                "Creado":  u.creado_en.strftime("%d/%m/%Y") if u.creado_en else "—",
            } for u in usuarios])
            st.dataframe(df_u, use_container_width=True, hide_index=True)
        finally:
            db.close()


# ══════════════════════════════════════════════════════════════════════════════
# TAB — MAESTROS  (siempre último)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[IDX_MAESTROS]:
    db = get_db()
    try:
        st.markdown('<div class="section-title">Importar archivos maestros</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🚜 Máquinas**")
            arch_maq = st.file_uploader("Archivo maquinas.xlsx", type=["xlsx"], key="up_maq")
            if arch_maq and st.button("Importar máquinas", type="primary"):
                try:
                    ins, act = importar_maquinas(db, arch_maq)
                    st.success(f"✅ Insertadas: {ins} · Actualizadas: {act}")
                except Exception as e:
                    db.rollback()
                    st.error(str(e))

        with col2:
            st.markdown("**👷 Operarios**")
            arch_op = st.file_uploader("Archivo operarios.xlsx", type=["xlsx"], key="up_op")
            if arch_op and st.button("Importar operarios", type="primary"):
                try:
                    ins, act = importar_operarios(db, arch_op)
                    st.success(f"✅ Insertados: {ins} · Actualizados: {act}")
                except Exception as e:
                    db.rollback()
                    st.error(str(e))

        st.divider()

        maquinas_m  = db.query(Maquina).order_by(Maquina.codigo).all()
        operarios_m = db.query(Operario).order_by(Operario.nombre).all()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total máquinas",    len(maquinas_m))
        c2.metric("Máquinas activas",  sum(1 for x in maquinas_m if x.activa))
        c3.metric("Total operarios",   len(operarios_m))
        c4.metric("Operarios activos", sum(1 for x in operarios_m if x.activo))

        ver_tabla = st.radio("Ver registros de:", ["🚜 Máquinas", "👷 Operarios"], horizontal=True, key="rad_maestros")

        if ver_tabla == "🚜 Máquinas":
            df = pd.DataFrame([{
                "Código":      str(x.codigo),
                "Descripción": x.descripcion,
                "Modelo":      x.modelo,
                "Tipo":        x.tipo,
                "Grupo":       x.grupo,
                "Estado":      x.estado,
                "Activa":      x.activa,
            } for x in maquinas_m])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            df = pd.DataFrame([{
                "Código":  str(x.codigo),
                "Nombre":  x.nombre,
                "Cargo":   x.cargo,
                "Unidad":  x.unidad,
                "Estado":  x.estado,
                "Activo":  x.activo,
            } for x in operarios_m])
            st.dataframe(df, use_container_width=True, hide_index=True)
    finally:
        db.close()
