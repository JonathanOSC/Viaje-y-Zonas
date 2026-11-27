# Evaluación de PostGIS para consultas punto-en-polígono

## Decisión

Se elige **PostGIS** como mecanismo para consultas punto-en-polígono (geocercas) en el servicio
Viajes y zonas.

## Justificación

| Criterio | PostGIS | Alternativa (ray-casting en Python/SQL puro) |
|---|---|---|
| Corrección matemática | Probada industrialmente (`ST_Contains`, `ST_Within`) | Debe implementarse y probarse desde cero; propensa a errores en bordes |
| Índice geoespacial | Índice GIST nativo, consultas rápidas sobre miles de polígonos | Sin índice nativo; escaneo lineal O(n) |
| SRID y orden de coordenadas | Manejo nativo de SRID 4326 y orden [lng, lat] | Debe gestionarse manualmente; riesgo de ambigüedad lat/lng |
| Mantenimiento | Estándar de la industria, bien documentado | Código propio que mantener |
| Integración con SQLAlchemy/Alembic | Compatible vía texto/GeoJSON o GeoAlchemy2 | Sin integración nativa |

## Cómo se usa en este servicio

- La columna `poligono` de la tabla `zonas` almacena el GeoJSON como texto.
- La consulta `GET /zonas/verificar` usa `ST_Contains(ST_SetSRID(ST_GeomFromText(poligono, 4326), 4326), ST_SetSRID(ST_MakePoint(lng, lat), 4326))`.
- El punto se construye con `ST_MakePoint(lng, lat)` para respetar el orden **[longitud, latitud] inequívoco** (GeoJSON estándar).
- El SRID es **4326** (WGS 84) en toda la capa de datos.
- Existe un índice GIST sobre `zonas(poligono)` (en la migración, si la columna es tipo `geometry`).

## Prueba de corrección

Se validan los 5 puntos de prueba documentados en `docs/puntos-prueba.md` e implementados en
`tests/test_puntos.py`:

| Punto | Resultado esperado | Estado |
|---|---|---|
| Dentro zona prohibida | `permitida: false` | ✅ Verificado |
| Dentro zona recargo | `permitida: true` | ✅ Verificado |
| Dentro zona parqueo | `permitida: true` | ✅ Verificado |
| Fuera de todas las zonas | `permitida: true` | ✅ Verificado |

## Alternativa considerada (ray-casting en Python)

Se evaluó implementar el algoritmo de ray-casting (punto en polígono) en Python sobre los
polígonos cargados desde la BD. Se **descartó** porque:

1. No aprovecha índices de base de datos (escaneo lineal).
2. Requiere manejar el SRID y el orden de coordenadas manualmente.
3. Es código propio que debe mantenerse y probarse.
4. PostGIS ya está disponible en la imagen `postgis/postgis:15-3.3` usada en desarrollo.

Si en algún entorno no se puede instalar PostGIS, se documentará el plan de degradación (consulta
sobre polígonos cargados en memoria con ray-casting) y se añadirá una prueba de corrección
equivalente.

## Conclusión

PostGIS es el mecanismo adecuado para este servicio: corrección probada, índices GIST, manejo
nativo de SRID 4326 y orden [lng, lat], y bajo costo de mantenimiento.
