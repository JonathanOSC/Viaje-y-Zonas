"""Pruebas de los datos semilla y de la verificación de puntos contra las zonas."""

from collections import Counter

import pytest
from sqlalchemy import text

from app.db.seed import PUNTOS_DE_PRUEBA, ZONAS_SEMILLA, sembrar

# Consulta que usará GET /zonas/verificar. ST_MakePoint recibe (longitud, latitud).
_ZONAS_QUE_CUBREN = text(
    """
    SELECT nombre, tipo FROM zonas
    WHERE ST_Covers(poligono, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
    ORDER BY nombre
    """
)

# Reparto de los 30 vehículos de Flota por zona (ApiFlota, docs/semilla.md).
VEHICULOS_POR_ZONA = {
    "Prohibida Centro": {"veh-0016"},
    "Recargo Oriente": {
        "veh-0005", "veh-0006", "veh-0011", "veh-0012", "veh-0017",
        "veh-0018", "veh-0023", "veh-0024", "veh-0029", "veh-0030",
    },  # fmt: skip
    "Parqueo Occidente": {
        "veh-0001", "veh-0002", "veh-0007", "veh-0008", "veh-0013",
        "veh-0014", "veh-0019", "veh-0020", "veh-0025", "veh-0026",
    },  # fmt: skip
    "Parqueo Sur": {"veh-0003", "veh-0004"},
}


def ubicacion_vehiculo(indice: int) -> tuple[float, float]:
    """(lat, lng) del vehículo en la cuadrícula de 6 x 5 que siembra Flota."""
    centro_lat, centro_lng, paso, columnas, filas = 4.7110, -74.0721, 0.0009, 6, 5
    col, fila = indice % columnas, indice // columnas
    lng = round(centro_lng + (col - (columnas - 1) / 2) * paso, 6)
    lat = round(centro_lat + (fila - (filas - 1) / 2) * paso, 6)
    return lat, lng


def test_la_semilla_carga_cuatro_zonas_una_prohibida_una_de_recargo_y_dos_de_parqueo(engine):
    assert sembrar(engine) == 4
    with engine.connect() as conexion:
        tipos = Counter(fila[0] for fila in conexion.execute(text("SELECT tipo FROM zonas")))
    assert tipos == {"prohibida": 1, "recargo": 1, "parqueo": 2}


def test_la_semilla_es_idempotente_y_restablece_los_valores(engine):
    sembrar(engine)
    with engine.begin() as conexion:
        conexion.execute(text("UPDATE zonas SET nombre = 'Editada' WHERE id = 'zona-parqueo-sur'"))
    sembrar(engine)
    with engine.connect() as conexion:
        filas = conexion.execute(text("SELECT id, nombre FROM zonas ORDER BY id")).all()
    assert len(filas) == 4
    assert dict(filas)["zona-parqueo-sur"] == "Parqueo Sur"


def test_los_identificadores_de_la_semilla_son_deterministas(engine):
    sembrar(engine)
    with engine.connect() as conexion:
        ids = {fila[0] for fila in conexion.execute(text("SELECT id FROM zonas"))}
    assert ids == {zona["id"] for zona in ZONAS_SEMILLA}


def test_las_zonas_semilla_no_se_traslapan(engine):
    sembrar(engine)
    with engine.connect() as conexion:
        area_compartida = conexion.execute(
            text(
                """
                SELECT a.nombre, b.nombre
                FROM zonas a JOIN zonas b ON a.id < b.id
                WHERE ST_Area(ST_Intersection(a.poligono, b.poligono)) > 0
                """
            )
        ).all()
    assert area_compartida == []


@pytest.mark.parametrize("punto", PUNTOS_DE_PRUEBA, ids=[p["caso"] for p in PUNTOS_DE_PRUEBA])
def test_los_puntos_de_prueba_dan_el_resultado_documentado(engine, punto):
    sembrar(engine)
    with engine.connect() as conexion:
        filas = conexion.execute(_ZONAS_QUE_CUBREN, {"lat": punto["lat"], "lng": punto["lng"]}).all()
    zonas = [fila.nombre for fila in filas]
    permitida = not any(fila.tipo == "prohibida" for fila in filas)
    assert zonas == punto["zonas"]
    assert permitida == punto["permitida"]


def test_las_zonas_cubren_los_vehiculos_de_flota_como_ellos_documentan(engine):
    sembrar(engine)
    obtenido: dict[str, set[str]] = {nombre: set() for nombre in VEHICULOS_POR_ZONA}
    sin_zona = set()
    with engine.connect() as conexion:
        for indice in range(30):
            lat, lng = ubicacion_vehiculo(indice)
            id_vehiculo = f"veh-{indice + 1:04d}"
            filas = conexion.execute(_ZONAS_QUE_CUBREN, {"lat": lat, "lng": lng}).all()
            assert len(filas) <= 1, f"{id_vehiculo} cae en más de una zona"
            if filas:
                obtenido[filas[0].nombre].add(id_vehiculo)
            else:
                sin_zona.add(id_vehiculo)
    assert obtenido == VEHICULOS_POR_ZONA
    assert sin_zona == {
        "veh-0009", "veh-0010", "veh-0015", "veh-0021", "veh-0022", "veh-0027", "veh-0028"
    }  # fmt: skip
