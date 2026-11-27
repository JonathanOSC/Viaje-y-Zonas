"""Datos semilla deterministas de Viajes y zonas.

Las cuatro zonas son la propuesta de Flota (ApiFlota, docs/semilla.md): una prohibida, una de
recargo y dos de parqueo, sobre la misma cuadrícula de Suba (Bogotá) donde Flota siembra sus
30 vehículos. Son rectángulos que comparten bordes pero no se traslapan.

Una zona prohibida es un lugar donde está estrictamente prohibido transitar en scooter.

No se siembran viajes: el guion de la demostración parte sin historial para que el descuento
del primer viaje de Cuentas pueda comprobarse.

Uso (desde services/viajes-crud, con las migraciones ya aplicadas):

    DATABASE_URL=postgresql+psycopg://... python -m app.db.seed

El comando es idempotente: si las zonas ya existen, las deja con los valores de este archivo.
"""

import json
import os
import sys

from sqlalchemy import create_engine, text


def _rectangulo(lng_min: float, lat_min: float, lng_max: float, lat_max: float) -> dict:
    """Polígono GeoJSON cerrado con el orden [longitud, latitud]."""
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lng_min, lat_min],
                [lng_max, lat_min],
                [lng_max, lat_max],
                [lng_min, lat_max],
                [lng_min, lat_min],
            ]
        ],
    }


ZONAS_SEMILLA = [
    {
        "id": "zona-prohibida-centro",
        "nombre": "Prohibida Centro",
        "tipo": "prohibida",
        "poligono": _rectangulo(-74.0719, 4.7107, -74.0714, 4.7113),
    },
    {
        "id": "zona-recargo-oriente",
        "nombre": "Recargo Oriente",
        "tipo": "recargo",
        "poligono": _rectangulo(-74.0710, 4.7086, -74.0694, 4.7134),
    },
    {
        "id": "zona-parqueo-occidente",
        "nombre": "Parqueo Occidente",
        "tipo": "parqueo",
        "poligono": _rectangulo(-74.0748, 4.7086, -74.0730, 4.7134),
    },
    {
        "id": "zona-parqueo-sur",
        "nombre": "Parqueo Sur",
        "tipo": "parqueo",
        "poligono": _rectangulo(-74.0730, 4.7086, -74.0710, 4.7100),
    },
]

# Puntos de prueba de GET /zonas/verificar?lat&lng y resultado esperado.
# Los cuatro primeros son los acordados con Flota; el quinto cae sobre el borde compartido
# de los dos parqueos (ST_Covers cuenta el borde como dentro).
PUNTOS_DE_PRUEBA = [
    {
        "caso": "Dentro de la zona prohibida",
        "lat": 4.7110,
        "lng": -74.07165,
        "permitida": False,
        "zonas": ["Prohibida Centro"],
    },
    {
        "caso": "En la zona de recargo",
        "lat": 4.7110,
        "lng": -74.0702,
        "permitida": True,
        "zonas": ["Recargo Oriente"],
    },
    {
        "caso": "En una zona de parqueo",
        "lat": 4.7092,
        "lng": -74.0720,
        "permitida": True,
        "zonas": ["Parqueo Sur"],
    },
    {
        "caso": "Fuera de todas las zonas",
        "lat": 4.7125,
        "lng": -74.0721,
        "permitida": True,
        "zonas": [],
    },
    {
        "caso": "Borde compartido entre los dos parqueos",
        "lat": 4.7090,
        "lng": -74.0730,
        "permitida": True,
        "zonas": ["Parqueo Occidente", "Parqueo Sur"],
    },
]

_UPSERT_ZONA = text(
    """
    INSERT INTO zonas (id, nombre, tipo, poligono)
    VALUES (
        :id, :nombre, :tipo,
        ST_SetSRID(ST_GeomFromGeoJSON(CAST(:poligono AS text)), 4326)
    )
    ON CONFLICT (id) DO UPDATE
    SET nombre = EXCLUDED.nombre, tipo = EXCLUDED.tipo, poligono = EXCLUDED.poligono
    """
)


def sembrar(engine) -> int:
    """Inserta o restablece las zonas semilla. Devuelve cuántas quedaron cargadas."""
    with engine.begin() as conexion:
        for zona in ZONAS_SEMILLA:
            conexion.execute(
                _UPSERT_ZONA,
                {
                    "id": zona["id"],
                    "nombre": zona["nombre"],
                    "tipo": zona["tipo"],
                    "poligono": json.dumps(zona["poligono"]),
                },
            )
    return len(ZONAS_SEMILLA)


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Define la variable de entorno DATABASE_URL.", file=sys.stderr)
        return 1
    engine = create_engine(url)
    try:
        cantidad = sembrar(engine)
    finally:
        engine.dispose()
    print(f"Zonas semilla cargadas: {cantidad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
