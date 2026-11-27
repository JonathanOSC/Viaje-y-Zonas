"""Carga datos semilla deterministas en la tabla `zonas`.

Las 4 zonas semilla están acordadas con Flota y cubren la misma área donde
Flota siembra sus vehículos (Bogotá, alrededor de 4.7110, -74.0721).

Tipos: 1 prohibida, 1 recargo, 2 parqueo.

Uso:
    python scripts/seed.py

Es idempotente: reejecutar no duplica zonas.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import psycopg2
from psycopg2.extras import RealDictCursor

# Coordenadas acordadas con Flota (área Bogotá, cerca del punto semilla de vehículos)
ZONAS_SEED = [
    {
        "id": "zona-0001",
        "nombre": "Zona Prohibida - Centro Comercial Andino",
        "tipo": "prohibida",
        "poligono": {
            "type": "Polygon",
            "coordinates": [[
                [-74.0725, 4.7105],
                [-74.0695, 4.7105],
                [-74.0695, 4.7135],
                [-74.0725, 4.7135],
                [-74.0725, 4.7105],
            ]],
        },
    },
    {
        "id": "zona-0002",
        "nombre": "Zona Recargo - Aeropuerto El Dorado",
        "tipo": "recargo",
        "poligono": {
            "type": "Polygon",
            "coordinates": [[
                [-74.0755, 4.7065],
                [-74.0725, 4.7065],
                [-74.0725, 4.7095],
                [-74.0755, 4.7095],
                [-74.0755, 4.7065],
            ]],
        },
    },
    {
        "id": "zona-0003",
        "nombre": "Zona Parqueo - Parque de la 93",
        "tipo": "parqueo",
        "poligono": {
            "type": "Polygon",
            "coordinates": [[
                [-74.0705, 4.7125],
                [-74.0675, 4.7125],
                [-74.0675, 4.7155],
                [-74.0705, 4.7155],
                [-74.0705, 4.7125],
            ]],
        },
    },
    {
        "id": "zona-0004",
        "nombre": "Zona Parqueo - Zona T",
        "tipo": "parqueo",
        "poligono": {
            "type": "Polygon",
            "coordinates": [[
                [-74.0675, 4.7045],
                [-74.0645, 4.7045],
                [-74.0645, 4.7075],
                [-74.0675, 4.7075],
                [-74.0675, 4.7045],
            ]],
        },
    },
]

INSERT_SQL = """
INSERT INTO zonas (id, nombre, tipo, poligono, creado_en, actualizado_en)
VALUES (%s, %s, %s, %s, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    tipo = EXCLUDED.tipo,
    poligono = EXCLUDED.poligono,
    actualizado_en = NOW()
"""


def main() -> int:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL no está definida.")
        return 1

    try:
        conn = psycopg2.connect(database_url)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR conectando a la BD: {exc}")
        return 1

    try:
        with conn.cursor() as cur:
            for zona in ZONAS_SEED:
                cur.execute(
                    INSERT_SQL,
                    (
                        zona["id"],
                        zona["nombre"],
                        zona["tipo"],
                        json.dumps(zona["poligono"]),
                    ),
                )
            conn.commit()
        print(f"Semilla cargada: {len(ZONAS_SEED)} zonas.")
        return 0
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"ERROR cargando semilla: {exc}")
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
