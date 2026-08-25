from datetime import datetime
import pandas as pd
from sqlalchemy import func
from database import Maquina, Operario, Caso, Gestion, Usuario
from passlib.hash import bcrypt


# ─── Catálogos ───────────────────────────────────────────────────────────────

CATEGORIAS = [
    "Cargue de líneas piloto",
    "Uso de líneas piloto",
    "Máquina sin reportar en John Deere",
    "Problema de conectividad",
    "Monitor de rendimiento",
    "Básculas / sensores de peso",
    "Calibración del sistema",
    "Datos de rendimiento inconsistentes",
    "Configuración del monitor",
    "Capacitación al operario",
    "Otro",
]

# Criticidad asignada automáticamente según la categoría seleccionada
CRITICIDAD_POR_CATEGORIA = {
    "Cargue de líneas piloto":              "Alta",
    "Uso de líneas piloto":                 "Alta",
    "Máquina sin reportar en John Deere":   "Alta",
    "Problema de conectividad":             "Media",
    "Monitor de rendimiento":               "Media",
    "Básculas / sensores de peso":          "Alta",
    "Calibración del sistema":              "Media",
    "Datos de rendimiento inconsistentes":  "Media",
    "Configuración del monitor":            "Baja",
    "Capacitación al operario":             "Baja",
    "Otro":                                 "Media",
}

ESTADOS_CASO = [
    "Abierto",
    "En seguimiento",
    "Pendiente de validación",
    "Escalado",
    "Solucionado",
    "Cerrado sin solución",
]

ESTADOS_ABIERTOS = ["Abierto", "En seguimiento", "Pendiente de validación", "Escalado"]

TIPOS_CONTACTO = [
    "Llamada saliente",
    "Llamada entrante",
    "WhatsApp",
    "Visita en campo",
    "Validación remota",
    "Correo",
    "Otro",
]

RESULTADOS_CONTACTO = [
    "Contacto efectivo",
    "No contesta",
    "Número ocupado",
    "Operario no disponible",
    "Información incompleta",
    "Caso solucionado",
    "Se requiere seguimiento",
    "Escalado",
]

# Badge de color por criticidad (para mostrar en UI)
COLOR_CRITICIDAD = {
    "Baja":    "#22c55e",
    "Media":   "#f59e0b",
    "Alta":    "#ef4444",
    "Crítica": "#7c3aed",
}

# Badge de color por estado
COLOR_ESTADO = {
    "Abierto":                 "#3b82f6",
    "En seguimiento":          "#f59e0b",
    "Pendiente de validación": "#8b5cf6",
    "Escalado":                "#ef4444",
    "Solucionado":             "#22c55e",
    "Cerrado sin solución":    "#6b7280",
}


# ─── Utilidades generales ─────────────────────────────────────────────────────

def limpiar_codigo(valor):
    if pd.isna(valor):
        return ""
    valor = str(valor).strip()
    return valor[:-2] if valor.endswith(".0") else valor


def generar_consecutivo(db):
    anio = datetime.now().year
    ultimo = db.query(func.max(Caso.id)).scalar() or 0
    return f"CASO-{anio}-{ultimo + 1:05d}"


def criticidad_por_categoria(categoria: str) -> str:
    return CRITICIDAD_POR_CATEGORIA.get(categoria, "Media")


# ─── Autenticación ───────────────────────────────────────────────────────────

def autenticar(db, usuario, clave):
    user = (
        db.query(Usuario)
        .filter(Usuario.usuario == usuario, Usuario.activo.is_(True))
        .first()
    )
    if user and bcrypt.verify(clave, user.password_hash):
        return user
    return None


# ─── Importación de maestros ──────────────────────────────────────────────────

def importar_maquinas(db, archivo):
    df = pd.read_excel(archivo)
    requeridas = [
        "REG_EQUIPMENT_COLUMN_ID",
        "REG_EQUIPMENT_COLUMN_DESCRIPTION",
        "REG_EQUIPMENT_COLUMN_MODEL",
        "REG_EQUIPMENT_COLUMN_TYPE",
        "REG_EQUIPMENT_COLUMN_GROUP",
        "REG_EQUIPMENT_COLUMN_STATUS",
    ]
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en máquinas: {faltantes}")

    insertados = 0
    actualizados = 0

    for _, row in df.iterrows():
        codigo = limpiar_codigo(row["REG_EQUIPMENT_COLUMN_ID"])
        if not codigo:
            continue

        registro = db.query(Maquina).filter(Maquina.codigo == codigo).first()
        datos = {
            "descripcion": str(row["REG_EQUIPMENT_COLUMN_DESCRIPTION"]).strip(),
            "modelo":      str(row["REG_EQUIPMENT_COLUMN_MODEL"]).strip(),
            "tipo":        str(row["REG_EQUIPMENT_COLUMN_TYPE"]).strip(),
            "grupo":       str(row["REG_EQUIPMENT_COLUMN_GROUP"]).strip(),
            "estado":      str(row["REG_EQUIPMENT_COLUMN_STATUS"]).strip(),
            "activa":      str(row["REG_EQUIPMENT_COLUMN_STATUS"]).strip().upper()
                           == "REG_EQUIPMENT_FIELD_ACTIVE",
        }

        if registro:
            for k, v in datos.items():
                setattr(registro, k, v)
            actualizados += 1
        else:
            db.add(Maquina(codigo=codigo, **datos))
            insertados += 1

    db.commit()
    return insertados, actualizados


def importar_operarios(db, archivo):
    df = pd.read_excel(archivo)
    requeridas = [
        "REG_EMPLOYEE_COLUMN_ID",
        "REG_EMPLOYEE_COLUMN_NAME",
        "REG_EMPLOYEE_COLUMN_CREDENTIAL",
        "REG_EMPLOYEE_COLUMN_ROLE",
        "REG_EMPLOYYE_COLUMN_LAGUAGE",
        "REG_EMPLOYEE_COLUMN_UNIT",
        "REG_EMPLOYEE_COLUMN_STATUS",
    ]
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en operarios: {faltantes}")

    insertados = 0
    actualizados = 0

    for _, row in df.iterrows():
        codigo = limpiar_codigo(row["REG_EMPLOYEE_COLUMN_ID"])
        if not codigo:
            continue

        registro = db.query(Operario).filter(Operario.codigo == codigo).first()
        estado = str(row["REG_EMPLOYEE_COLUMN_STATUS"]).strip()
        datos = {
            "nombre":     str(row["REG_EMPLOYEE_COLUMN_NAME"]).strip().upper(),
            "credencial": limpiar_codigo(row["REG_EMPLOYEE_COLUMN_CREDENTIAL"]),
            "cargo":      str(row["REG_EMPLOYEE_COLUMN_ROLE"]).strip().upper(),
            "idioma":     str(row["REG_EMPLOYYE_COLUMN_LAGUAGE"]).strip(),
            "unidad":     str(row["REG_EMPLOYEE_COLUMN_UNIT"]).strip().upper(),
            "estado":     estado,
            "activo":     estado.upper() == "ATIVO",
        }

        if registro:
            for k, v in datos.items():
                setattr(registro, k, v)
            actualizados += 1
        else:
            db.add(Operario(codigo=codigo, **datos))
            insertados += 1

    db.commit()
    return insertados, actualizados
