-- ═══════════════════════════════════════════════════════════════════════
--   Sistema de Gestión de Atenciones Remotas — Ingenio Providencia
--   Script DDL para Supabase / PostgreSQL
--   Tablas con sufijo _atenciones para coexistir con otras soluciones
--   Ejecutar en: Supabase Dashboard -> SQL Editor -> New Query -> Run
-- ═══════════════════════════════════════════════════════════════════════


-- 1. USUARIOS DEL SISTEMA
CREATE TABLE IF NOT EXISTS usuarios_atenciones (
    id            SERIAL PRIMARY KEY,
    usuario       VARCHAR(80)  UNIQUE NOT NULL,
    nombre        VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol           VARCHAR(30)  NOT NULL DEFAULT 'analista',
    activo        BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en     TIMESTAMPTZ           DEFAULT NOW()
);


-- 2. CATALOGO DE MAQUINAS (COSECHADORAS)
CREATE TABLE IF NOT EXISTS maquinas_atenciones (
    id             SERIAL PRIMARY KEY,
    codigo         VARCHAR(80)  UNIQUE NOT NULL,
    descripcion    VARCHAR(255),
    modelo         VARCHAR(150),
    tipo           VARCHAR(100),
    grupo          VARCHAR(100),
    estado         VARCHAR(100),
    activa         BOOLEAN NOT NULL DEFAULT TRUE,
    actualizado_en TIMESTAMPTZ  DEFAULT NOW()
);


-- 3. CATALOGO DE OPERARIOS
CREATE TABLE IF NOT EXISTS operarios_atenciones (
    id             SERIAL PRIMARY KEY,
    codigo         VARCHAR(80)  UNIQUE NOT NULL,
    nombre         VARCHAR(180) NOT NULL,
    credencial     VARCHAR(100),
    cargo          VARCHAR(120),
    idioma         VARCHAR(80),
    unidad         VARCHAR(100),
    estado         VARCHAR(80),
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    actualizado_en TIMESTAMPTZ  DEFAULT NOW()
);


-- 4. CASOS DE SOPORTE
CREATE TABLE IF NOT EXISTS casos_atenciones (
    id                        SERIAL PRIMARY KEY,
    consecutivo               VARCHAR(40)  UNIQUE NOT NULL,
    fecha_apertura            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    maquina_id                INTEGER      NOT NULL REFERENCES maquinas_atenciones(id),
    operario_id               INTEGER               REFERENCES operarios_atenciones(id),
    creado_por_id             INTEGER      NOT NULL REFERENCES usuarios_atenciones(id),

    origen                    VARCHAR(80)  DEFAULT 'Llamada saliente',
    categoria                 VARCHAR(120) NOT NULL,
    criticidad                VARCHAR(30)  DEFAULT 'Media',
    problema                  TEXT         NOT NULL,
    estado                    VARCHAR(40)  DEFAULT 'Abierto',

    requiere_seguimiento      BOOLEAN      DEFAULT FALSE,
    fecha_proximo_seguimiento TIMESTAMPTZ,

    escalado_a                VARCHAR(150),
    fecha_cierre              TIMESTAMPTZ,
    solucion_final            TEXT,
    observaciones             TEXT
);


-- 5. GESTIONES / SEGUIMIENTOS
CREATE TABLE IF NOT EXISTS gestiones_atenciones (
    id                     SERIAL PRIMARY KEY,
    caso_id                INTEGER NOT NULL REFERENCES casos_atenciones(id) ON DELETE CASCADE,
    fecha_hora             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario_id             INTEGER NOT NULL REFERENCES usuarios_atenciones(id),

    tipo_contacto          VARCHAR(80) DEFAULT 'Llamada saliente',
    resultado_contacto     VARCHAR(80),
    duracion_minutos       FLOAT       DEFAULT 0,
    detalle                TEXT        NOT NULL,
    solucion_indicada      TEXT,
    estado_resultante      VARCHAR(40),
    requiere_nueva_gestion BOOLEAN     DEFAULT FALSE,
    fecha_nueva_gestion    TIMESTAMPTZ
);


-- INDICES DE RENDIMIENTO
CREATE INDEX IF NOT EXISTS idx_atenciones_casos_estado    ON casos_atenciones(estado);
CREATE INDEX IF NOT EXISTS idx_atenciones_casos_maquina   ON casos_atenciones(maquina_id);
CREATE INDEX IF NOT EXISTS idx_atenciones_casos_operario  ON casos_atenciones(operario_id);
CREATE INDEX IF NOT EXISTS idx_atenciones_casos_fecha     ON casos_atenciones(fecha_apertura);
CREATE INDEX IF NOT EXISTS idx_atenciones_gestiones_caso  ON gestiones_atenciones(caso_id);
CREATE INDEX IF NOT EXISTS idx_atenciones_gestiones_fecha ON gestiones_atenciones(fecha_hora);


-- VERIFICACION: confirma que se crearon las 5 tablas
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'usuarios_atenciones',
      'maquinas_atenciones',
      'operarios_atenciones',
      'casos_atenciones',
      'gestiones_atenciones'
  )
ORDER BY table_name;


DB_URL="postgresql+psycopg2://postgres:[YOUR-PASSWORD]@db.yfvyskjoybuukbqhwpqf.supabase.co:5432/postgres"