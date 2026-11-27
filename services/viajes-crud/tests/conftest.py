"""Fixtures de las pruebas de base de datos.

Necesitan PostgreSQL con PostGIS y una base DEDICADA a pruebas, indicada en TEST_DATABASE_URL
(por ejemplo postgresql+psycopg://usuario:clave@localhost:5432/viajes_zonas_test). El usuario
debe poder ejecutar CREATE EXTENSION postgis. La base se borra y se recrea en cada ejecución.
Sin esa variable, las pruebas se omiten.
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]
URL_PRUEBAS = os.environ.get("TEST_DATABASE_URL")

_LIMPIEZA_TOTAL = [
    "DROP TABLE IF EXISTS viajes CASCADE",
    "DROP TABLE IF EXISTS zonas CASCADE",
    "DROP TABLE IF EXISTS alembic_version",
    "DROP FUNCTION IF EXISTS fn_tocar_actualizado_en()",
    "DROP EXTENSION IF EXISTS postgis CASCADE",
]


def configuracion_alembic() -> Config:
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ / "alembic"))
    config.set_main_option("sqlalchemy.url", URL_PRUEBAS)
    return config


def vaciar_base(engine) -> None:
    """Deja la base como una recién creada, sin tablas ni PostGIS."""
    with engine.begin() as conexion:
        for sentencia in _LIMPIEZA_TOTAL:
            conexion.execute(text(sentencia))


@pytest.fixture(scope="session")
def engine():
    if not URL_PRUEBAS:
        pytest.skip("Define TEST_DATABASE_URL con una base dedicada a pruebas (con PostGIS).")
    eng = create_engine(URL_PRUEBAS)
    vaciar_base(eng)
    command.upgrade(configuracion_alembic(), "head")
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def datos_limpios(engine):
    with engine.begin() as conexion:
        conexion.execute(text("TRUNCATE viajes, zonas RESTART IDENTITY CASCADE"))
