"""Configuración de pruebas para Viajes y zonas.

Pruebas sin red: los adaptadores HTTP se simulan. La capa de acceso a datos
se prueba contra una base de datos real (PostgreSQL + PostGIS) cuando está
disponible, o con dobles cuando no.
"""

from __future__ import annotations

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.viajes_crud.app.db.session import SessionLocal, engine
from services.viajes_crud.app.repositories import ZonaRepository, ViajeRepository


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Sesión de BD para pruebas. Requiere DATABASE_URL definida."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL no definida; omite pruebas de BD")

    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def zona_repo(db_session: Session) -> ZonaRepository:
    return ZonaRepository(db_session)


@pytest.fixture
def viaje_repo(db_session: Session) -> ViajeRepository:
    return ViajeRepository(db_session)
