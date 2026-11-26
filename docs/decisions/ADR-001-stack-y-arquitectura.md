# ADR-001: Stack, arquitectura y reglas técnicas

- Estado: Aceptado para la fase inicial
- Fecha: 2026-11-26
- Relacionadas: Issue #1, Issue #2

## Contexto

Viajes y zonas forma parte del clúster Rodar y entrega dos responsabilidades
separadas:

1. CRUD de Viajes y Zonas: persistencia y administración propia.
2. MID de Viajes: inicio y finalización del viaje mediante Cuentas y Flota.

Los contratos son la fuente de verdad y las comunicaciones entre servicios se
realizan a través del API Gateway. Viajes y zonas no debe consultar
directamente bases de datos de Cuentas o Flota.

## Decisión de stack

| Componente | Decisión |
|---|---|
| Lenguaje | Python 3.12 |
| Framework | FastAPI |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migraciones | Alembic |
| Validación | Pydantic 2.x |
| Configuración | pydantic-settings |
| Cliente HTTP | HTTPX |
| Pruebas | Pytest |
| Contenedores | Docker |
| Geoespacial | PostGIS, sujeto a validación técnica durante el diseño de persistencia |

Las versiones de paquetes se fijarán en el manifiesto de dependencias al
comenzar la implementación. Python 3.12 es el objetivo acordado en la guía del
clúster y debe validarse contra los requisitos de Cuentas, Gateway y Flota.

## Arquitectura

Se mantienen dos aplicaciones FastAPI independientes dentro del mismo
repositorio:

```text
services/
├── viajes-crud/
│   └── app/
│       ├── api/routers/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       ├── repositories/
│       ├── services/
│       ├── db/
│       └── main.py
└── viajes-mid/
    └── app/
        ├── api/routers/
        ├── core/
        ├── schemas/
        ├── services/
        ├── clients/
        ├── integrations/
        └── main.py
```

Responsabilidades:

- Routers: transporte HTTP y validación de entrada.
- Schemas: contratos Pydantic de entrada y salida.
- Models: representación SQLAlchemy de la persistencia propia.
- Repositories: operaciones de PostgreSQL.
- Services: reglas de negocio y coordinación.
- Clients e integrations: consumo aislado de Cuentas y Flota.

No se crearán consultas SQL ni lógica de ciclo de vida directamente en los
routers. El CRUD no ejecuta transiciones propias del flujo MID.

## PostgreSQL y datos

- PostgreSQL será la persistencia propia de viajes y zonas.
- SQLAlchemy 2.x administrará modelos y sesiones.
- Alembic versionará el esquema.
- No se duplicará información completa de usuarios, billeteras o vehículos.
- Las coordenadas GeoJSON se representan internamente y externamente como
  `[longitud, latitud]`.
- Los índices geográficos y la decisión final sobre PostGIS deben coordinarse
  con el responsable del esquema PostgreSQL.

## Configuración

La configuración obligatoria se leerá desde variables de entorno:

```dotenv
DATABASE_URL=
SALDO_MINIMO=5000
BATERIA_MINIMA=15
TARIFA_DESBLOQUEO=1000
TARIFA_POR_MINUTO=350
RECARGO_ZONA_PCT=20
DESCUENTO_PRIMER_VIAJE_PCT=50
GATEWAY_URL=
GATEWAY_CLIENT_ID=
GATEWAY_CLIENT_SECRET=
GATEWAY_SECRET=
CUENTAS_URL=
FLOTA_URL=
MID_GEMINI_API_KEY=
```

`MID_GEMINI_API_KEY` será opcional y solo podrá usarse en integración optativa,
nunca como reemplazo de Cuentas o Flota.

Los secretos no se versionarán. Los archivos locales de configuración deben
quedar excluidos por `.gitignore`.

## Reglas de negocio adoptadas

- El saldo mínimo de referencia es `5000` COP y se configura mediante
  `SALDO_MINIMO`.
- El inicio exige batería igual o superior al 15 %.
- Al reservar, Flota debe cambiar el vehículo a `en_viaje`.
- La persistencia de inicio ocurre únicamente después de validar saldo y
  reservar el vehículo.
- `PATCH /viajes/{id}` solo modifica `observacion`.
- El viaje no puede finalizarse dos veces.
- El destino final fuera de Bogotá se rechaza con
  `409 ubicacion_fuera_de_bogota`, sujeto a confirmación formal de Flota y
  Gateway.
- Una zona prohibida al finalizar genera multa, pero no impide finalizar.
- Las operaciones parciales deben informar explícitamente qué dependencias
  confirmaron y cuáles quedaron pendientes.

## Pendientes externos

| Pendiente | Responsable | Impacto |
|---|---|---|
| Confirmar cuerpo exacto de liquidación | Cuentas | Integración MID |
| Confirmar la regla exacta de redondeo de minutos | Cuentas | Duración cobrada |
| Conceder scopes y credenciales OAuth2 | Líder del Gateway | Despliegue e integración |
| Defender `POST /viajes` como ruta interna MID | Gateway | Exposición accidental del CRUD |
| Confirmar responsabilidad de administrar zonas | Equipo de zonas | Scope `zonas:escribir` |
| Confirmar diversidad tecnológica del clúster | Líder técnico | Cumplimiento académico |

Las siguientes decisiones ya quedaron resueltas por los documentos entregados:

| Decisión | Evidencia |
|---|---|
| Saldo mínimo `5000` COP | `X1.cluster-rodar.md`, sección 6.2 |
| Batería mínima de inicio `15 %` y reserva atómica | `X1.cluster-rodar.md`, sección 6.2 |
| Cambio de vehículo a `en_viaje` y liberación concurrente segura | Contrato formal de Flota `openapi.json` |
| Finalización fuera de Bogotá rechazada | Contrato y documentación de Flota: `dentroDeBogota: false` y `400 fuera_de_bogota` |
| Tarifa base: `1000 COP` de desbloqueo más `350 COP` por minuto | `X1.cluster-rodar.md`, sección 5.2 |
| Recargo de zona: `20 %`; descuento del primer viaje: `50 %` | `X1.cluster-rodar.md`, sección 5.2 |
| El MID debe consultar localidad y geocercas por servicios separados | Contrato de Flota y contrato de Viajes y zonas |
| `PATCH /viajes/{id}` mantiene solo `observacion` | Contrato específico v1.1.0 de Viajes y zonas |
| Coordenadas GeoJSON en `[longitud, latitud]` y parámetros separados `lat`/`lng` | Contrato de Flota y contrato de Viajes y zonas |
| Scopes propuestos del clúster | `X1.cluster-rodar.md`, sección 3 |
| Comunicación obligatoria entre servicios por Gateway | `X1.proyecto_final.md`, sección 4 |

Existe una discrepancia que queda formalmente resuelta en favor del contrato
específico: `X1.cluster-rodar.md` todavía indica que `PATCH /viajes/{id}`
actualiza estado, destino y minutos, mientras el contrato específico v1.1.0
limita la operación a `observacion`. Las transiciones del ciclo de vida se
ejecutan exclusivamente por el MID. Esta excepción debe reflejarse en una
corrección coordinada del documento general.

## Contratos y exposición

- `docs/openapi-crud.yaml` define Viajes y Zonas.
- `docs/openapi-mid.yaml` define inicio y finalización.
- `POST /viajes` existe únicamente como operación interna del MID. El Gateway
  debe protegerla y no publicarla para clientes finales hasta acordar
  explícitamente lo contrario.
- `POST /viajes/iniciar` y `POST /viajes/{id}/finalizar` son operaciones MID.
- Los consumidores reciben `Authorization: Bearer`.
- `X-Gateway-Secret` es una cabecera interna del Gateway al microservicio y
  nunca debe ser conocida por consumidores externos.

## Consecuencias

Ventajas:

- Separación clara entre persistencia y orquestación.
- Contratos verificables independientemente.
- Configuración sin secretos versionados.
- Persistencia propia sin duplicar datos de otros dominios.

Costes y riesgos:

- Requiere coordinación adicional con Cuentas, Flota y Gateway.
- La finalización puede producir operaciones parciales que necesitan
  reconciliación.
- PostGIS podría añadir infraestructura y complejidad si se adopta.

