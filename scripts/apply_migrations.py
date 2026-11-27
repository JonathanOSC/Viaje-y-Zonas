"""Aplica las migraciones de Alembic sobre una BD vacía.

Uso:
    python scripts/apply_migrations.py

Requiere DATABASE_URL definida en el entorno o en .env.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

# Asegurar que se lea .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL no está definida. Configure .env o la variable de entorno.")
        return 1

    alembic_cfg = Config(str(ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    try:
        command.upgrade(alembic_cfg, "head")
        print("Migraciones aplicadas correctamente.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR aplicando migraciones: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
