# Base de datos de Viajes y zonas

Este documento describe la persistencia propia del CRUD de Viajes y zonas (Issue #3): modelo, convenciones geográficas, migraciones, datos semilla y conexión local y administrada. El código está en `services/viajes-crud/`.

## Alcance

La base guarda solo viajes y zonas. No hay tablas de usuarios, billeteras ni vehículos: `usuario_id` y `vehiculo_id` son referencias de texto a datos que pertenecen a Cuentas y a Flota, y se consultan por el Gateway. Ningún servicio lee esta base directamente.

## Convenciones geográficas

- Todas las geometrías usan SRID 4326 (WGS 84), declarado en el tipo de la columna (`geometry(Point, 4326)` y `geometry(Polygon, 4326)`). PostgreSQL rechaza una geometría con otro SRID.
- El orden de coordenadas es siempre longitud y luego latitud, igual que GeoJSON. En SQL se escribe `ST_MakePoint(lng, lat)` o `POINT(lng lat)`.
- Los endpoints reciben el punto como parámetros separados `lat` y `lng`.
- Una zona prohibida es un lugar donde está estrictamente prohibido transitar en scooter.

## Modelo

### zonas

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | varchar(64) | Clave primaria |
| nombre | varchar(200) | No vacío |
| tipo | varchar(20) | `prohibida`, `recargo` o `parqueo` |
| poligono | geometry(Polygon, 4326) | Válido (`ST_IsValid`), no vacío y dentro de rango geográfico |
| creado_en, actualizado_en | timestamptz | `actualizado_en` se renueva con un trigger |

### viajes

| Columna | Tipo | Notas |
| --- | --- | --- |
| id | integer | Identidad generada, clave primaria |
| usuario_id, vehiculo_id | varchar(64) | No vacíos |
| estado | varchar(12) | `iniciado`, `finalizado` o `cancelado` |
| inicio_en, fin_en | timestamptz | `fin_en` nunca es anterior a `inicio_en` |
| origen, destino | geometry(Point, 4326) | `origen` obligatorio, `destino` solo al finalizar |
| minutos | integer | Mayor o igual a cero |
| zona_destino_id | varchar(64) | Referencia a `zonas.id` con `ON DELETE SET NULL` |
| observacion | varchar(500) | Opcional, no vacía si existe |
| creado_en, actualizado_en | timestamptz | `actualizado_en` se renueva con un trigger |

Reglas de coherencia que aplica la propia base:

- Un viaje `iniciado` no tiene fin, destino, minutos ni zona de destino.
- Un viaje `finalizado` tiene fin, destino y minutos.
- Un vehículo no puede tener dos viajes `iniciado` al mismo tiempo (índice único parcial). Esto protege contra dos peticiones concurrentes sobre el mismo vehículo.
- Al borrar una zona, los viajes que la tenían como destino se conservan y quedan con `zona_destino_id` en nulo.

### Índices

| Índice | Uso |
| --- | --- |
| `zonas_poligono_gix` (GIST) | Consulta de punto dentro de polígono |
| `zonas_tipo_idx` | Filtro de zonas por tipo |
| `viajes_usuario_inicio_idx` | Historial de un usuario ordenado por fecha |
| `viajes_vehiculo_inicio_idx` | Viajes de un vehículo |
| `viajes_estado_inicio_idx` | Filtro por estado |
| `viajes_inicio_idx` | Filtro por rango de fechas |
| `viajes_zona_destino_idx` | Viajes por zona de destino |
| `viajes_un_activo_por_vehiculo_uidx` | Un solo viaje iniciado por vehículo |

## Verificar un punto

La verificación de `GET /zonas/verificar?lat&lng` usa PostGIS:

```sql
SELECT id, nombre, tipo
FROM zonas
WHERE ST_Covers(poligono, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326));
```

`ST_Covers` cuenta el borde como dentro de la zona. El campo `permitida` es falso solo si alguna de las zonas devueltas es de tipo `prohibida`.

PostGIS se eligió por encima de una librería del lenguaje porque deja la consulta cerca de los datos, usa el índice GIST y valida los polígonos al guardarlos. Si el servidor administrado no permite la extensión, la alternativa es guardar el polígono como `jsonb` y resolver el punto en la aplicación con Shapely. Eso implicaría una migración nueva y probar de nuevo los puntos de la sección siguiente.

## Migraciones

Las migraciones se versionan con Alembic y se escriben en SQL explícito, porque el esquema geoespacial se controla a mano.

```bash
cd services/viajes-crud
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://USUARIO:CLAVE@HOST:5432/NOMBRE
alembic upgrade head      # crea la extensión PostGIS, las tablas y los índices
alembic downgrade base    # elimina las tablas (la extensión PostGIS se conserva)
```

La migración `0001` parte de una base vacía. No hace falta crear tablas a mano.

## Datos semilla

```bash
python -m app.db.seed
```

El comando es idempotente: si las zonas ya existen, las deja con los valores del archivo `app/db/seed.py`. No siembra viajes, para que la demostración parta sin historial y el descuento del primer viaje de Cuentas pueda comprobarse.

Las cuatro zonas son la propuesta de Flota (`ApiFlota`, `docs/semilla.md`). Son rectángulos en Suba, Bogotá, que cubren la cuadrícula de 30 vehículos de Flota, no se traslapan y dejan una franja libre.

| Zona | Tipo | Longitud | Latitud | Vehículos de Flota dentro |
| --- | --- | --- | --- | --- |
| Prohibida Centro | prohibida | -74.0719 a -74.0714 | 4.7107 a 4.7113 | veh-0016 |
| Recargo Oriente | recargo | -74.0710 a -74.0694 | 4.7086 a 4.7134 | 10 |
| Parqueo Occidente | parqueo | -74.0748 a -74.0730 | 4.7086 a 4.7134 | 10 |
| Parqueo Sur | parqueo | -74.0730 a -74.0710 | 4.7086 a 4.7100 | veh-0003, veh-0004 |

### Puntos de prueba y resultado esperado

| Caso | lat | lng | permitida | Zonas |
| --- | --- | --- | --- | --- |
| Dentro de la zona prohibida | 4.7110 | -74.07165 | false | Prohibida Centro |
| En la zona de recargo (paso 7 de la demostración) | 4.7110 | -74.0702 | true | Recargo Oriente |
| En una zona de parqueo | 4.7092 | -74.0720 | true | Parqueo Sur |
| Fuera de todas las zonas | 4.7125 | -74.0721 | true | ninguna |
| Borde compartido de los dos parqueos | 4.7090 | -74.0730 | true | Parqueo Occidente y Parqueo Sur |

Estos casos están automatizados en `tests/test_semilla.py`, junto con una prueba que ubica los 30 vehículos de Flota y comprueba el reparto de la tabla anterior.

## Conexión local

El archivo `services/viajes-crud/docker-compose.db.yml` levanta PostgreSQL con PostGIS y un volumen con nombre, así que los datos sobreviven a `docker compose down`.

```bash
cd services/viajes-crud
export POSTGRES_PASSWORD=una-clave-local
docker compose -f docker-compose.db.yml up -d
export DATABASE_URL=postgresql+psycopg://viajes:$POSTGRES_PASSWORD@localhost:5432/viajes_zonas
alembic upgrade head
python -m app.db.seed
```

Para borrar los datos a propósito se usa `docker compose -f docker-compose.db.yml down -v`. El puerto solo se publica en `127.0.0.1`.

## Conexión administrada

El servidor PostgreSQL compartido entrega una base y un usuario por grupo. La cadena de conexión va en la variable `DATABASE_URL`, definida como secreto de GitHub y como variable segura de la plataforma de despliegue. Nunca se escribe en el repositorio ni en archivos `.env` versionados. Antes del primer despliegue hay que confirmar que el usuario del grupo puede ejecutar `CREATE EXTENSION postgis`. Si no puede, un administrador del servidor debe crearla una vez.

## Pruebas

Las pruebas necesitan una base dedicada con PostGIS y un usuario que pueda crear la extensión. La base se vacía y se recrea en cada ejecución, así que nunca debe apuntar a datos reales.

```bash
cd services/viajes-crud
export TEST_DATABASE_URL=postgresql+psycopg://USUARIO:CLAVE@localhost:5432/viajes_zonas_test
pytest
```

Sin `TEST_DATABASE_URL` las pruebas se omiten. Cubren la migración (subida, bajada y nueva subida desde una base vacía), las restricciones de integridad, los índices, la semilla y los puntos de prueba.
