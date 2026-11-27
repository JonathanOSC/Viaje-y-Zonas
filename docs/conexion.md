# Conexión a PostgreSQL — Viajes y zonas

## Resumen

El servicio **Viajes y zonas** usa **PostgreSQL administrado** con la extensión **PostGIS** para
consultas geoespaciales. Las credenciales y URLs se proporcionan exclusivamente por
**variables de entorno** (o secretos de la plataforma de despliegue). Nunca se publican secretos
en el repositorio.

## Variables de entorno

Copie `.env.example` a `.env` y complete los valores reales antes de ejecutar.

| Variable | Descripción | Ejemplo local | Requerido |
|---|---|---|---|
| `DATABASE_URL` | URL de conexión SQLAlchemy a PostgreSQL | `postgresql+psycopg://viajes_zonas:viajes_zonas_dev@localhost:5433/viajes_zonas` | Sí |
| `DATABASE_SSL_MODE` | Modo SSL (`prefer`, `require`, `disable`) | `prefer` | No |
| `APP_ENV` | Entorno de ejecución (`local`, `managed`, `production`) | `local` | No |
| `API_CRUD_PORT` | Puerto de la API CRUD | `8100` | No |
| `API_MID_PORT` | Puerto de la API MID | `8101` | No |

Las demás variables son reglas de negocio y configuración del gateway (ver `.env.example`).

## Ejecución local (Docker)

```bash
# 1. Copie el ejemplo y complete valores (nunca suba secretos)
cp .env.example .env
# Edite .env con DATABASE_URL y demás valores

# 2. Levanta PostgreSQL + PostGIS local
docker compose up -d

# 3. Verifique que la base esté lista
docker compose exec db pg_isready -U viajes_zonas -d viajes_zonas

# 4. Aplica migraciones desde una BD vacía
python scripts/apply_migrations.py

# 5. Carga datos semilla deterministas
python scripts/seed.py

# 6. Inicia la API CRUD
uvicorn services.viajes_crud.app.main:app --reload --port 8100
```

La API queda en `http://localhost:8100`. El endpoint `/health` responde `200`.

## Base de datos administrada (Azure / producción)

Para una base administrada (por ejemplo Azure Database for PostgreSQL con PostGIS):

1. Cree el servidor y la base de datos en la plataforma.
2. Habilite la extensión `postgis` en la base de datos.
3. Obtenga la cadena de conexión (con `sslmode=require`).
4. Defina `DATABASE_URL` como variable de entorno o secreto de la plataforma.
5. Defina `DATABASE_SSL_MODE=require`.
6. Ejecute `python scripts/apply_migrations.py` y `python scripts/seed.py` desde el pipeline
   o desde una máquina con acceso a la base.

**No guarde la cadena de conexión con contraseña en el repositorio.** Use GitHub Secrets o el
almacén de secretos de la plataforma de despliegue.

## Aplicar migraciones y semilla

```bash
# Desde una BD vacía, aplicar migraciones versionadas (Alembic)
python scripts/apply_migrations.py

# Cargar datos semilla deterministas (4 zonas acordadas con Flota)
python scripts/seed.py
```

Ambos scripts son idempotentes y seguros de volver a ejecutar.

## Reconectar tras reinicio

La base de datos local usa un volumen Docker (`viajes_zonas_data`). Al reiniciar el contenedor,
los datos persisten. Si se borra el volumen, se debe volver a ejecutar `apply_migrations.py`
y `seed.py` desde una BD vacía.

## Seguridad

- Las credenciales de la base de datos viajan solo por variables de entorno/secretos.
- La API rechaza peticiones sin la cabecera `X-Gateway-Secret` agregada por el gateway.
- Este servicio no almacena usuarios, billeteras ni vehículos (pertenecen a Cuentas y Flota).
