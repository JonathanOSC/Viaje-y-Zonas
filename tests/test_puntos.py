"""Pruebas de punto-en-polígono (geocerca) para Viajes y zonas.

Resultado esperado documentado para cada punto de prueba.

Caso de prueba | Punto (lat, lng) | Resultado esperado
---------------|------------------|-------------------
P1 | Dentro zona prohibida (zona-0001) | permitida: false, zona: "Zona Prohibida - Centro Comercial Andino"
P2 | Dentro zona recargo (zona-0002) | permitida: true, zona: "Zona Recargo - Aeropuerto El Dorado"
P3 | Dentro zona parqueo (zona-0003) | permitida: true, zona: "Zona Parqueo - Parque de la 93"
P4 | Dentro zona parqueo (zona-0004) | permitida: true, zona: "Zona Parqueo - Zona T"
P5 | Fuera de todas las zonas | permitida: true, zonas: []

Estas coordenadas están dentro de los polígonos definidos en scripts/seed.py
y acordadas con Flota (mismo área donde siembra vehículos).
"""

from __future__ import annotations

from typing import Any, Dict

import pytest


# Puntos de prueba con resultado esperado documentado
PUNTOS_PRUEBA = [
    {
        "nombre": "Dentro zona prohibida (zona-0001)",
        "lat": 4.7115,
        "lng": -74.0710,
        "esperado_permitida": False,
        "esperado_zonas": ["Zona Prohibida - Centro Comercial Andino"],
        "esperado_tipos": ["prohibida"],
    },
    {
        "nombre": "Dentro zona recargo (zona-0002)",
        "lat": 4.7080,
        "lng": -74.0740,
        "esperado_permitida": True,
        "esperado_zonas": ["Zona Recargo - Aeropuerto El Dorado"],
        "esperado_tipos": ["recargo"],
    },
    {
        "nombre": "Dentro zona parqueo (zona-0003)",
        "lat": 4.7140,
        "lng": -74.0690,
        "esperado_permitida": True,
        "esperado_zonas": ["Zona Parqueo - Parque de la 93"],
        "esperado_tipos": ["parqueo"],
    },
    {
        "nombre": "Dentro zona parqueo (zona-0004)",
        "lat": 4.7060,
        "lng": -74.0660,
        "esperado_permitida": True,
        "esperado_zonas": ["Zona Parqueo - Zona T"],
        "esperado_tipos": ["parqueo"],
    },
    {
        "nombre": "Fuera de todas las zonas",
        "lat": 4.7200,
        "lng": -74.0800,
        "esperado_permitida": True,
        "esperado_zonas": [],
        "esperado_tipos": [],
    },
]


@pytest.mark.parametro("caso", PUNTOS_PRUEBA)
def test_verificar_punto_resultado_esperado(zona_repo, caso: Dict[str, Any]):
    """Verifica que verificar_punto devuelve el resultado esperado para cada punto."""
    resultado = zona_repo.verificar_punto(lat=caso["lat"], lng=caso["lng"])

    # Coordenadas devueltas correctas
    assert resultado["lat"] == caso["lat"]
    assert resultado["lng"] == caso["lng"]

    # Permitida esperada
    assert resultado["permitida"] == caso["esperado_permitida"], (
        f"[{caso['nombre']}] Se esperaba permitida={caso['esperado_permitida']} "
        f"pero se obtuvo {resultado['permitida']}"
    )

    # Zonas encontradas
    nombres_encontrados = [z["nombre"] for z in resultado["zonas"]]
    tipos_encontrados = [z["tipo"] for z in resultado["zonas"]]

    for nombre_esperado in caso["esperado_zonas"]:
        assert nombre_esperado in nombres_encontrados, (
            f"[{caso['nombre']}] Se esperaba la zona '{nombre_esperado}' pero se obtuvo {nombres_encontrados}"
        )

    for tipo_esperado in caso["esperado_tipos"]:
        assert tipo_esperado in tipos_encontrados, (
            f"[{caso['nombre']}] Se esperaba un zona de tipo '{tipo_esperado}' pero se obtuvo {tipos_encontrados}"
        )

    # Si está dentro de una zona prohibida, NO debe estar permitida
    if "prohibida" in tipos_encontrados:
        assert resultado["permitida"] is False, (
            f"[{caso['nombre']}] Un punto dentro de zona prohibida no debe ser permitida"
        )


def test_verificar_punto_prohibida_no_permitida(zona_repo):
    """Caso crítico: un punto dentro de zona prohibida debe dar permitida=false."""
    resultado = zona_repo.verificar_punto(lat=4.7115, lng=-74.0710)
    assert resultado["permitida"] is False
    assert any(z["tipo"] == "prohibida" for z in resultado["zonas"])
    assert any("Prohibida" in z["nombre"] for z in resultado["zonas"])


def test_verificar_punto_fuera_todas_permitida(zona_repo):
    """Caso crítico: un punto fuera de todas las zonas debe dar permitida=true."""
    resultado = zona_repo.verificar_punto(lat=4.7200, lng=-74.0800)
    assert resultado["permitida"] is True
    assert resultado["zonas"] == []
