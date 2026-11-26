# Viajes y zonas — Clúster Rodar

Microservicios responsables de la administración de viajes y geocercas, y de la coordinación del inicio y finalización de viajes dentro de la plataforma de micromovilidad Rodar.

## Alcance del grupo

El grupo entrega dos APIs:

- **CRUD de Viajes y Zonas:** persistencia propia en PostgreSQL, consultas paginadas, validaciones geográficas y administración de zonas.
- **MID de Viajes:** orquesta el ciclo de vida del viaje y consume Cuentas y Flota a través del API Gateway.

El contrato OpenAPI acordado es la fuente de verdad para rutas, modelos, scopes, respuestas y errores. No se debe acceder directamente a la base de datos de otro grupo.

## Flujo principal

1. Iniciar viaje: validar usuario y saldo en Cuentas, consultar y reservar el vehículo en Flota, y persistir el viaje.
2. Finalizar viaje: verificar localidad con Flota, verificar geocercas propias, persistir el cierre, liberar el vehículo y solicitar la liquidación a Cuentas.
3. Manejar errores parciales sin afirmar que una liberación o liquidación se completó cuando el servicio dependiente no la confirmó.

## Integraciones

| Consumidor / proveedor | Operación |
| --- | --- |
| MID Flota → Viajes y zonas | `GET /zonas/verificar?lat&lng` |
| MID Cuentas → Viajes y zonas | `GET /viajes/{id}`, `GET /zonas/{id}` |
| MID Viajes → Cuentas | `GET /usuarios/{id}/billetera`, `POST /liquidaciones` |
| MID Viajes → Flota | `GET /vehiculos/{id}`, `PATCH /vehiculos/{id}/estado`, `GET /localidades/verificar` |

Las llamadas entre servicios pasan por el gateway. El gateway agrega `X-Gateway-Secret`; no se expone a consumidores.

## Documentación del repositorio

- [Issue #2: incorporar y validar contratos OpenAPI CRUD y MID](https://github.com/JonathanOSC/Viaje-y-Zonas/issues/2) — pendiente de incorporar los dos contratos OpenAPI.
- [Decisiones técnicas y arquitectura: ADR-001](docs/decisions/ADR-001-stack-y-arquitectura.md).
- [Variables de entorno](.env.example).
- [Contribución y Pull Requests](CONTRIBUTING.md).
- [Configuración de GitHub, tablero y protección de ramas](docs/GITHUB_WORKFLOW.md).

## Estado del desarrollo

El repositorio se encuentra en fase inicial. La documentación entregada ya fija el saldo mínimo de **5.000 COP**, la batería mínima de **15 %**, la reserva atómica de Flota, la tarifa base y los recargos/promociones descritos por el clúster. Antes de implementar deben acordarse el redondeo exacto de minutos, el cuerpo definitivo de liquidación, la exposición interna de `POST /viajes`, los scopes y credenciales del Gateway, la administración de zonas y el API de tercero que consumirá el MID. Las decisiones pendientes se registran en el ADR y deben resolverse por Issue.

## Flujo de trabajo

- `main`: estable.
- `develop`: integración.
- ramas `feature/*`, `fix/*`, `test/*`, `docs/*` y `chore/*`: trabajo por Issue.
- Todo cambio entra mediante Pull Request revisado y CI aprobado.

Ver [CONTRIBUTING.md](CONTRIBUTING.md) y [docs/GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md).

## Requisitos del proyecto

Cada grupo debe entregar CRUD, MID (mínimo dos endpoints), contratos OpenAPI, persistencia propia, pruebas, pipeline, consumo de API de tercero y documentación para la integración a través del gateway. La sustentación requiere que cada integrante pueda explicar y modificar lo implementado.
