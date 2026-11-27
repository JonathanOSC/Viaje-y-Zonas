# Puntos de prueba — Resultado esperado

## Resumen

Este documento documenta los **puntos de prueba** para la consulta punto-en-polígono
(`GET /zonas/verificar`) y su **resultado esperado**. Estas pruebas están implementadas en
`tests/test_puntos.py`.

Los puntos están dentro o fuera de las 4 zonas semilla acordadas con Flota (ver
`docs/zonas-semilla.md`).

## Puntos de prueba

| # | Nombre | lat | lng | Resultado esperado |
|---|---|---|---|---|
| P1 | Dentro zona prohibida (zona-0001) | 4.7115 | -74.0710 | `permitida: false`, zona: "Zona Prohibida - Centro Comercial Andino", tipo: `prohibida` |
| P2 | Dentro zona recargo (zona-0002) | 4.7080 | -74.0740 | `permitida: true`, zona: "Zona Recargo - Aeropuerto El Dorado", tipo: `recargo` |
| P3 | Dentro zona parqueo (zona-0003) | 4.7140 | -74.0690 | `permitida: true`, zona: "Zona Parqueo - Parque de la 93", tipo: `parqueo` |
| P4 | Dentro zona parqueo (zona-0004) | 4.7060 | -74.0660 | `permitida: true`, zona: "Zona Parqueo - Zona T", tipo: `parqueo` |
| P5 | Fuera de todas las zonas | 4.7200 | -74.0800 | `permitida: true`, `zonas: []` |

## Reglas de verificación

1. **Zona prohibida**: si el punto cae dentro de cualquier zona de tipo `prohibida`, `permitida` = `false`.
2. **Zona recargo / parqueo**: `permitida` = `true`.
3. **Fuera de todas las zonas**: `permitida` = `true` y `zonas` vacío.

## Cómo ejecutar

```bash
# Asegurar que la BD tenga las zonas semilla
python scripts/seed.py

# Ejecutar pruebas
pytest tests/test_puntos.py -v
```

Cada prueba verifica que `resultado.permitida` coincida con lo esperado y que las zonas
devueltas incluyan las esperadas con el tipo correcto.

## Casos críticos

- **P1 (prohibida)**: Un punto dentro de zona prohibida **no debe** ser permitida. Esto valida
  la regla de negocio fundamental: los scooters no pueden andar en zonas prohibidas.
- **P5 (fuera de todas)**: Un punto fuera de todas las zonas **debe** ser permitida. Esto valida
  que no haya falsos positivos al consultar zonas.
