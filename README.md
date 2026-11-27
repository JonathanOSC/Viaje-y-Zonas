# Grupo Viajes y zonas — Persistencia propia (PostgreSQL + PostGIS)

Servicio **CRUD de Viajes y zonas** del clúster **Rodar**. Administra las tablas propias `viajes` y `zonas` sobre
**PostgreSQL administrado** con la extensión **PostGIS** para consultas punto-en-polígono (geocercas).

## Qué entrega este grupo (issue #3)

| Componente | Descripción |
|---|---|
| API CRUD (`services/viajes-crud/`) | `viajes` y `zonas`: crear, leer, actualizar, borrar, filtros y paginación |
| API MID (`services/viajes-mid/`) | Iniciar y finalizar viaje (consume Cuentas y Flota a través del gateway) |
| Persistencia | PostgreSQL administrado, credenciales por variables de entorno |
| Migraciones | Alembic versionadas, aplicables desde una BD vacía |
| Semilla | Datos semilla deterministas (4 zonas acordadas con Flota) |
| Índices | Por `usuario_id`, `estado`, fechas y geometrías (GIST) |
| PostGIS | `ST_Contains` / `ST_Within` para `GET /zonas/verificar` |

## Estructura

```
.
├── docker-compose.yml              # PostGIS local para desarrollo
├── .env.example                    # Variables de entorno (sin secretos)
├── requirements.txt
├── Dockerfile
├── alembic.ini                     # Configuración de Alembic
├── alembic/                        # Migraciones versionadas (Alembic)
├── services/
│   ├── viajes-crud/                # API CRUD de Viajes y zonas (FastAPI + SQLAlchemy)
│   │   └── app/
│   │       ├── api/routers/        # Endpoints: zonas, viajes, health
│   │       ├── core/               # Configuración
│   │       ├── models/             # Modelos SQLAlchemy (zona, viaje)
│   │       ├── schemas/            # Esquemas Pydantic de petición/respuesta
│   │       ├── repositories/       # Acceso a datos (CRUD SQL)
│   │       ├── services/           # Lógica de aplicación
│   │       └── db/                 # Sesión y base de SQLAlchemy
│   └── viajes-mid/                 # API MID de Viajes (iniciar/finalizar viaje)
│       └── app/
│           ├── api/routers/        # Endpoints: iniciar, finalizar
│           ├── core/               # Configuración
│           ├── schemas/            # Esquemas Pydantic
│           ├── services/           # Lógica de negocio (reglas de viaje)
│           ├── clients/            # Clientes HTTP a Cuentas y Flota
│           └── integrations/       # Integraciones mediante gateway
├── scripts/
│   ├── apply_migrations.py         # Aplica migraciones Alembic sobre una BD vacía
│   └── seed.py                     # Carga datos semilla deterministas
├── tests/
│   ├── conftest.py
│   └── test_puntos.py              # Puntos de prueba con resultado esperado
└── docs/
    ├── conexion.md                 # Conexión local y administrada (sin secretos)
    ├── zonas-semilla.md            # Zonas semilla acordadas con Flota
    ├── puntos-prueba.md            # Puntos de prueba y resultado esperado
    ├── evaluacion-postgis.md       # Evaluación de PostGIS vs alternativa
    └── openapi.json                # Contrato OpenAPI aprobado
```

## Ejecutar en local

```bash
# Copie el ejemplo y complete valores (nunca suba secretos)
cp .env.example .env

# Levanta PostgreSQL + PostGIS local
docker compose up -d

# Aplica migraciones y carga semilla desde una BD vacía
python scripts/apply_migrations.py
python scripts/seed.py

# Inicia la API CRUD
uvicorn services.viajes_crud.app.main:app --reload --port 8100
```

La API queda en `http://localhost:8100` y `/health` responde `200`.

## Repositorios relacionados (clúster Rodar)

- **Gateway:** `gateway/` (KrakenD + tokens) — enruta `/viajes` a este servicio.
- **Flota:** CRUD de vehículos (no relacional) y MID de recomendación.
- **Cuentas:** CRUD de usuarios/billetera y MID de liquidación.

Este servicio **no almacena** usuarios, billeteras ni vehículos; esos datos pertenecen a Cuentas y Flota y se consumen por sus APIs a través del gateway.
