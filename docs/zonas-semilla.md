# Zonas semilla — Acuerdo con Flota

## Resumen

Este documento registra las **4 zonas semilla** deterministas acordadas con el grupo **Flota**
desde el primer día, para el grupo **Viajes y zonas** (issue #3).

Las coordenadas están en **GeoJSON [longitud, latitud]**, **SRID 4326** (WGS 84), con anillo
cerrado (primer punto = último punto). Cubren la misma área de Bogotá donde Flota siembra sus
vehículos (punto de referencia: `4.7110, -74.0721`).

## Zonas semilla

| id | nombre | tipo | coordenadas aproximadas (centro) |
|---|---|---|---|
| `zona-0001` | Zona Prohibida - Centro Comercial Andino | prohibida | `4.7120, -74.0710` |
| `zona-0002` | Zona Recargo - Aeropuerto El Dorado | recargo | `4.7080, -74.0740` |
| `zona-0003` | Zona Parqueo - Parque de la 93 | parqueo | `4.7140, -74.0690` |
| `zona-0004` | Zona Parqueo - Zona T | parqueo | `4.7060, -74.0660` |

## Detalle de polígonos

### zona-0001 — Prohibida (Centro Comercial Andino)

Polígono cuadrado alrededor de `(-74.0710, 4.7120)`.

```json
{
  "type": "Polygon",
  "coordinates": [[
    [-74.0725, 4.7105],
    [-74.0695, 4.7105],
    [-74.0695, 4.7135],
    [-74.0725, 4.7135],
    [-74.0725, 4.7105]
  ]]
}
```

### zona-0002 — Recargo (Aeropuerto El Dorado)

Polígono cuadrado alrededor de `(-74.0740, 4.7080)`.

```json
{
  "type": "Polygon",
  "coordinates": [[
    [-74.0755, 4.7065],
    [-74.0725, 4.7065],
    [-74.0725, 4.7095],
    [-74.0755, 4.7095],
    [-74.0755, 4.7065]
  ]]
}
```

### zona-0003 — Parqueo (Parque de la 93)

Polígono cuadrado alrededor de `(-74.0690, 4.7140)`.

```json
{
  "type": "Polygon",
  "coordinates": [[
    [-74.0705, 4.7125],
    [-74.0675, 4.7125],
    [-74.0675, 4.7155],
    [-74.0705, 4.7155],
    [-74.0705, 4.7125]
  ]]
}
```

### zona-0004 — Parqueo (Zona T)

Polígono cuadrado alrededor de `(-74.0660, 4.7060)`.

```json
{
  "type": "Polygon",
  "coordinates": [[
    [-74.0675, 4.7045],
    [-74.0645, 4.7045],
    [-74.0645, 4.7075],
    [-74.0675, 4.7075],
    [-74.0675, 4.7045]
  ]]
}
```

## Reglas de negocio por tipo

| Tipo | Significado | Efecto en viajes |
|---|---|---|
| `prohibida` | Zona por la que el scooter no puede andar | `GET /zonas/verificar` devuelve `permitida: false`. Al finalizar un viaje en esta zona se marca `multa: true`. |
| `recargo` | Zona con recargo de tarifa | `GET /zonas/verificar` devuelve `permitida: true`. La liquidación aplica +20%. |
| `parqueo` | Zona donde se puede dejar el vehículo | `GET /zonas/verificar` devuelve `permitida: true`. Sin recargo ni multa. |

## Idempotencia

La semilla se carga con `ON CONFLICT (id) DO UPDATE`, por lo que reejecutar
`python scripts/seed.py` no duplica zonas y mantiene los datos deterministas.

## Acuerdo con Flota

Estas coordenadas deben acordarse con el grupo **Flota desde el primer día** y cubrir la misma
área donde Flota siembra sus vehículos (30 vehículos semilla repartidos en una zona de la ciudad,
según el contrato de Flota). Cualquier cambio debe coordinarse entre ambos grupos y reflejarse
en este documento y en `scripts/seed.py`.
