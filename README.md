# Sistema de Gestión de Soporte a Cosechadoras

Aplicación Streamlit para registrar y demostrar la gestión de soporte relacionada con:

- Líneas piloto.
- Máquinas sin reporte en John Deere.
- Conectividad.
- Monitor de rendimiento.
- Básculas y sensores.
- Calibración.
- Capacitación a operarios.
- Seguimiento, escalamiento y cierre de casos.

## Estructura funcional

1. Inicio de sesión.
2. Importación de maestros desde Excel.
3. Registro de casos.
4. Registro de múltiples llamadas o gestiones por caso.
5. Seguimiento de pendientes.
6. Consulta histórica.
7. Indicadores y exportación a Excel.
8. Administración de usuarios.

## Preparación

Copie `.env.example` como `.env`.

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Cambie la contraseña inicial en `.env`.

## Ejecución local

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Abra:

```text
http://localhost:8501
```

## Usuario inicial

Se crea automáticamente con los valores definidos en `.env`:

```text
Usuario: admin
Contraseña: Cambiar_Esta_Clave_2026
```

Cambie la contraseña antes de producción.

## Archivos maestros

### maquinas.xlsx

Columnas obligatorias:

- REG_EQUIPMENT_COLUMN_ID
- REG_EQUIPMENT_COLUMN_DESCRIPTION
- REG_EQUIPMENT_COLUMN_MODEL
- REG_EQUIPMENT_COLUMN_TYPE
- REG_EQUIPMENT_COLUMN_GROUP
- REG_EQUIPMENT_COLUMN_STATUS

### operarios.xlsx

Columnas obligatorias:

- REG_EMPLOYEE_COLUMN_ID
- REG_EMPLOYEE_COLUMN_NAME
- REG_EMPLOYEE_COLUMN_CREDENTIAL
- REG_EMPLOYEE_COLUMN_ROLE
- REG_EMPLOYYE_COLUMN_LAGUAGE
- REG_EMPLOYEE_COLUMN_UNIT
- REG_EMPLOYEE_COLUMN_STATUS

## Despliegue con Docker

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

## Base de datos

Por defecto se utiliza SQLite:

```text
data/soporte.db
```

Para producción multiusuario se recomienda PostgreSQL. Solo debe cambiar `DB_URL` en `.env`, por ejemplo:

```text
DB_URL=postgresql+psycopg2://usuario:clave@servidor:5432/soporte
```

En ese caso agregue `psycopg2-binary` a `requirements.txt`.

## Recomendaciones de producción

- Publicar detrás de HTTPS.
- Cambiar la contraseña del administrador.
- Realizar copia diaria del archivo `data/soporte.db`.
- Usar PostgreSQL cuando haya varios usuarios concurrentes.
- Restringir el acceso mediante VPN, red corporativa o autenticación empresarial.
- Mantener los maestros de máquinas y operarios actualizados.
