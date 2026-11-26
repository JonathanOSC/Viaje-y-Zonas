# Guía de contribución

## Ramas

El repositorio utiliza un flujo GitFlow simplificado:

- `main`: versión estable y entregable. No se trabaja directamente sobre esta rama.
- `develop`: integración del trabajo aprobado.
- `feature/<issue>-<descripcion>`: nuevas funcionalidades.
- `fix/<issue>-<descripcion>`: correcciones.
- `test/<issue>-<descripcion>`: pruebas.
- `docs/<issue>-<descripcion>`: documentación.
- `chore/<descripcion>`: configuración y mantenimiento.

Toda rama de trabajo debe partir de `develop). Las funcionalidades se integran mediante Pull Request hacia `develop). La publicación estable se realiza desde `develop) hacia `main).

## Commits

Usar Conventional Commits, en español o inglés, con mensajes concretos:

- `feat: agregar consulta paginada de viajes`
- `fix: compensar reserva cuando falla la persistencia`
- `test: cubrir finalización en zona prohibida`
- `docs: documentar integración con Flota`
- `ci: validar contrato OpenAPI`

Un commit debe representar un cambio lógico pequeño. No incluir secretos, archivos `.env), tokens, credenciales ni datos personales.

## Pull Requests obligatorios

1. Crear una rama desde `develop) y relacionarla con una Issue.
2. Mantener la rama enfocada en una sola tarea.
3. Abrir un Pull Request hacia `develop). No hacer push directo a `main) ni a `develop).
4. Usar la plantilla de PR y escribir `Closes #<issue>` cuando corresponda.
5. Solicitar al menos una revisión de otro integrante que no sea el autor.
6. Resolver comentarios y volver a solicitar revisión cuando se actualice el PR.
7. Esperar que los checks de CI terminen correctamente.
8. Fusionar con **Squash and merge** o el método acordado por el equipo. Eliminar la rama una vez fusionada.

No aprobar ni fusionar el propio PR. Los cambios de contrato que afecten a Flota o Cuentas requieren revisión del equipo consumidor/proveedor correspondiente.

## Definition of Ready (antes de iniciar una Issue)

- La historia y su alcance son comprensibles.
- Hay criterios de aceptación verificables.
- Se conocen las dependencias con Cuentas, Flota y Gateway.
- Los cambios del contrato están acordados o identificados como pendientes.
- La Issue tiene responsable y prioridad en el tablero.

## Definition of Done

- Implementación coherente con el contrato OpenAPI acordado.
- Validaciones y errores con el formato común del clúster.
- Pruebas unitarias y de integración relevantes.
- Sin secretos ni URLs de otros servicios codificadas en duro.
- Docker/local run documentado cuando aplique.
- CI aprobado.
- Pull Request revisado y fusionado.
- README/contrato actualizados si cambió el comportamiento.

## Reglas técnicas de integración

- Toda comunicación entre microservicios pasa por el API Gateway, según el proyecto.
- El gateway agrega `X-Gateway-Secret`; los clientes externos no deben conocerla.
- Las URLs, scopes y credenciales se configuran por variables de entorno o secretos.
- No consultar directamente la base de datos de otro grupo.
- Para errores: respetar `401`, `403`, `404` y `503` según el significado acordado. No reintentar un `403`; limitar reintentos ante fallos transitorios.
- Coordenadas GeoJSON siempre en orden `[longitud, latitud]`; parámetros de consulta separados `lat` y `lng`.

## Estrategia de integración

Los contratos son la fuente de verdad. Antes de cambiar un endpoint, request, response, scope o código de error, abrir una Issue y coordinar el cambio con los consumidores. Actualizar el contrato y las pruebas en el mismo PR o en PR coordinados.
