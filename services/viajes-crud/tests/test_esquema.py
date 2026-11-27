"""Pruebas del esquema: migración, restricciones, índices y comportamiento de las claves."""

import json

import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import configuracion_alembic, vaciar_base

CUADRADO = {
    "type": "Polygon",
    "coordinates": [
        [
            [-74.0700, 4.7100],
            [-74.0690, 4.7100],
            [-74.0690, 4.7110],
            [-74.0700, 4.7110],
            [-74.0700, 4.7100],
        ]
    ],
}


def insertar_zona(conexion, id="z-1", nombre="Zona de prueba", tipo="parqueo", geojson=CUADRADO, srid=4326):
    conexion.execute(
        text(
            """
            INSERT INTO zonas (id, nombre, tipo, poligono)
            VALUES (:id, :nombre, :tipo,
                    ST_SetSRID(ST_GeomFromGeoJSON(CAST(:geojson AS text)), :srid))
            """
        ),
        {"id": id, "nombre": nombre, "tipo": tipo, "geojson": json.dumps(geojson), "srid": srid},
    )


def insertar_viaje(
    conexion,
    usuario="usr-1",
    vehiculo="veh-0001",
    estado="iniciado",
    inicio="2026-11-26T10:00:00Z",
    fin=None,
    destino=None,
    minutos=None,
    zona=None,
    observacion=None,
):
    """Inserta un viaje. Los puntos van en WKT, que usa el orden POINT(longitud latitud)."""
    conexion.execute(
        text(
            """
            INSERT INTO viajes (usuario_id, vehiculo_id, estado, inicio_en, fin_en, origen,
                                destino, minutos, zona_destino_id, observacion)
            VALUES (:usuario, :vehiculo, :estado, CAST(:inicio AS timestamptz),
                    CAST(:fin AS timestamptz), ST_GeomFromText('POINT(-74.0721 4.7110)', 4326),
                    ST_GeomFromText(CAST(:destino AS text), 4326), :minutos, :zona, :observacion)
            """
        ),
        {
            "usuario": usuario,
            "vehiculo": vehiculo,
            "estado": estado,
            "inicio": inicio,
            "fin": fin,
            "destino": destino,
            "minutos": minutos,
            "zona": zona,
            "observacion": observacion,
        },
    )


def finalizado(**extra):
    datos = {
        "estado": "finalizado",
        "fin": "2026-11-26T10:20:00Z",
        "destino": "POINT(-74.0702 4.7110)",
        "minutos": 20,
    }
    datos.update(extra)
    return datos


# ----------------------------------------------------------------- migración


def test_las_tablas_son_solo_las_propias(engine):
    with engine.connect() as conexion:
        tablas = {
            fila[0]
            for fila in conexion.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
                )
            )
        }
    # spatial_ref_sys la crea PostGIS. No debe haber usuarios, billeteras ni vehículos.
    assert tablas - {"spatial_ref_sys"} == {"zonas", "viajes", "alembic_version"}


def test_las_geometrias_declaran_srid_4326_y_tipo(engine):
    with engine.connect() as conexion:
        filas = conexion.execute(
            text(
                "SELECT f_table_name, f_geometry_column, srid, type FROM geometry_columns "
                "WHERE f_table_schema = 'public'"
            )
        ).all()
    esperado = {
        ("zonas", "poligono", 4326, "POLYGON"),
        ("viajes", "origen", 4326, "POINT"),
        ("viajes", "destino", 4326, "POINT"),
    }
    assert set(filas) == esperado


def test_migracion_sube_baja_y_vuelve_a_subir_desde_una_base_vacia(engine):
    config = configuracion_alembic()
    try:
        vaciar_base(engine)
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        with engine.connect() as conexion:
            quedan = conexion.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name IN ('zonas', 'viajes')"
                )
            ).scalar_one()
        assert quedan == 0
    finally:
        vaciar_base(engine)
        command.upgrade(config, "head")


def test_los_indices_esperados_existen(engine):
    with engine.connect() as conexion:
        indices = {
            nombre: definicion
            for nombre, definicion in conexion.execute(
                text("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'")
            )
        }
    assert "USING gist (poligono)" in indices["zonas_poligono_gix"]
    for nombre in (
        "zonas_tipo_idx",
        "viajes_usuario_inicio_idx",
        "viajes_vehiculo_inicio_idx",
        "viajes_estado_inicio_idx",
        "viajes_inicio_idx",
        "viajes_zona_destino_idx",
        "viajes_un_activo_por_vehiculo_uidx",
    ):
        assert nombre in indices


# -------------------------------------------------------------------- zonas


def test_zona_valida_se_guarda(engine):
    with engine.begin() as conexion:
        insertar_zona(conexion)
        srid = conexion.execute(text("SELECT ST_SRID(poligono) FROM zonas")).scalar_one()
    assert srid == 4326


def test_zona_con_tipo_desconocido_se_rechaza(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, tipo="peligrosa")


def test_zona_con_nombre_vacio_se_rechaza(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, nombre="   ")


def test_zona_con_srid_distinto_se_rechaza(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, srid=3857)


def test_zona_que_no_es_poligono_se_rechaza(engine):
    punto = {"type": "Point", "coordinates": [-74.07, 4.71]}
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, geojson=punto)


def test_poligono_sin_cerrar_se_rechaza(engine):
    abierto = {
        "type": "Polygon",
        "coordinates": [[[-74.07, 4.71], [-74.06, 4.71], [-74.06, 4.72], [-74.07, 4.72]]],
    }
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, geojson=abierto)


def test_poligono_con_menos_de_cuatro_puntos_se_rechaza(engine):
    triangulo_incompleto = {
        "type": "Polygon",
        "coordinates": [[[-74.07, 4.71], [-74.06, 4.71], [-74.07, 4.71]]],
    }
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, geojson=triangulo_incompleto)


def test_poligono_que_se_cruza_a_si_mismo_se_rechaza(engine):
    corbata = {
        "type": "Polygon",
        "coordinates": [
            [[-74.07, 4.71], [-74.06, 4.72], [-74.06, 4.71], [-74.07, 4.72], [-74.07, 4.71]]
        ],
    }
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, geojson=corbata)


def test_poligono_con_longitud_fuera_de_rango_se_rechaza(engine):
    fuera = {
        "type": "Polygon",
        "coordinates": [[[200, 4.71], [201, 4.71], [201, 4.72], [200, 4.72], [200, 4.71]]],
    }
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, geojson=fuera)


def test_el_identificador_de_zona_es_unico(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_zona(conexion, id="z-1")
        insertar_zona(conexion, id="z-1", nombre="Otra")


# ------------------------------------------------------------------- viajes


def test_viaje_iniciado_valido_se_guarda_con_identificador_numerico(engine):
    with engine.begin() as conexion:
        insertar_viaje(conexion)
        fila = conexion.execute(text("SELECT id, estado FROM viajes")).one()
    assert fila.id == 1
    assert fila.estado == "iniciado"


def test_viaje_con_estado_desconocido_se_rechaza(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, estado="en_curso")


@pytest.mark.parametrize("faltante", ["fin", "destino", "minutos"])
def test_viaje_finalizado_exige_fin_destino_y_minutos(engine, faltante):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, **finalizado(**{faltante: None}))


def test_viaje_finalizado_completo_se_guarda(engine):
    with engine.begin() as conexion:
        insertar_viaje(conexion, **finalizado())
        assert conexion.execute(text("SELECT count(*) FROM viajes")).scalar_one() == 1


@pytest.mark.parametrize(
    "extra",
    [
        {"fin": "2026-11-26T10:20:00Z"},
        {"destino": "POINT(-74.0702 4.7110)"},
        {"minutos": 5},
    ],
)
def test_viaje_iniciado_no_admite_datos_de_cierre(engine, extra):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, **extra)


def test_el_fin_no_puede_ser_anterior_al_inicio(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, **finalizado(fin="2026-11-26T09:00:00Z"))


def test_minutos_negativos_se_rechazan(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, **finalizado(minutos=-1))


def test_observacion_vacia_o_demasiado_larga_se_rechaza(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, observacion="  ")
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, observacion="x" * 501)


def test_destino_con_coordenadas_fuera_de_rango_se_rechaza(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, **finalizado(destino="POINT(-200 4.7110)"))


def test_un_vehiculo_no_puede_tener_dos_viajes_iniciados(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, vehiculo="veh-0001", usuario="usr-1")
        insertar_viaje(conexion, vehiculo="veh-0001", usuario="usr-2")


def test_el_vehiculo_vuelve_a_estar_disponible_tras_finalizar(engine):
    with engine.begin() as conexion:
        insertar_viaje(conexion, vehiculo="veh-0001", **finalizado())
        insertar_viaje(conexion, vehiculo="veh-0001")
        insertar_viaje(conexion, vehiculo="veh-0002")
        assert conexion.execute(text("SELECT count(*) FROM viajes")).scalar_one() == 3


def test_la_zona_destino_debe_existir(engine):
    with pytest.raises(DBAPIError), engine.begin() as conexion:
        insertar_viaje(conexion, **finalizado(zona="no-existe"))


def test_borrar_una_zona_conserva_el_viaje_y_deja_la_zona_destino_en_nulo(engine):
    with engine.begin() as conexion:
        insertar_zona(conexion, id="z-1")
        insertar_viaje(conexion, **finalizado(zona="z-1"))
    with engine.begin() as conexion:
        conexion.execute(text("DELETE FROM zonas WHERE id = 'z-1'"))
    with engine.connect() as conexion:
        fila = conexion.execute(text("SELECT estado, zona_destino_id FROM viajes")).one()
    assert fila.estado == "finalizado"
    assert fila.zona_destino_id is None


def test_actualizado_en_se_renueva_al_modificar(engine):
    with engine.begin() as conexion:
        insertar_viaje(conexion)
    with engine.begin() as conexion:
        conexion.execute(text("UPDATE viajes SET observacion = 'Revisado por administración'"))
    with engine.connect() as conexion:
        fila = conexion.execute(text("SELECT creado_en, actualizado_en FROM viajes")).one()
    assert fila.actualizado_en > fila.creado_en
