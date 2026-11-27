"""Configuración de entorno de Alembic."""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Lee .env para DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

import os  # noqa: E402

# Interpretar el archivo de configuración de Alembic
config = context.config

# Sobrescribir la URL de SQLAlchemy desde el entorno
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Configurar logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para autogeneración (aquí no usamos modelos SQLAlchemy con
# tipos geometry, por lo que dejamos target_metadata = None y escribimos SQL
# manual en cada migración).
target_metadata = None


def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo 'offline' (sin conexión a la BD)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecutar migraciones en modo 'online' (conectado a la BD)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
