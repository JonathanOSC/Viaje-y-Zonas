# Configuración de GitHub para el equipo

Esta guía complementa `CONTRIBUTING.md`. La rama `develop` ya fue creada y existe junto con `main`. La configuración de reglas de rama y Projects debe activarse en la interfaz de GitHub por una persona con permisos de administración.

## 1. Crear el tablero Kanban

En el repositorio, abrir **Projects → New project → Board**. Nombre sugerido: **Viajes y zonas – Sprint Board**.

Crear las vistas:
- **Sprint actual**: vista Board agrupada por Status y filtrada por la iteración vigente.
- **Backlog**: vista Table/Board filtrada por Status = `Por hacer` y ordenada por Priority.
- **Por responsable**: agrupar por Assignees.
- **Roadmap**: vista Table con Issue, Priority, Sprint, Status y Assignees.

Campos sugeridos:
- `Status` (Single select): **Por hacer**, **En progreso**, **En revisión**, **Hecho**. Mantener estos cuatro estados para cumplir las columnas mínimas del enunciado.
- `Priority` (Single select): P0 - Bloqueante, P1 - Alta, P2 - Media, P3 - Baja.
- `Sprint` (Iteration): configurar iteraciones según las fechas reales del equipo.
- `Estimate` (Number): puntos o tamaño acordado.
- `Area` (Single select): CRUD Viajes, CRUD Zonas, MID, Integración, Calidad, DevOps, Documentación.

Añadir las Issues abiertas del repositorio al Project. Automatizar, cuando esté disponible, el estado al abrir/cerrar Issues y al abrir/mergear PRs. Mantener un responsable por Issue; dividir tareas grandes.

**Límite WIP:** máximo 2 tareas por integrante en `En progreso`. Si una tarea está bloqueada por una dependencia, dejarla en `Por hacer`, añadir una etiqueta `blocked` si está creada y explicar el bloqueo en un comentario de la Issue. No crear una quinta columna para bloqueos.

## 2. Proteger `main` y `develop`

En **Settings → Rules → Rulesets → New branch ruleset** (o Branch protection rules, según la interfaz):

Aplicar a `main` y `develop`:
- Require a pull request before merging.
- Required approvals: 1 como mínimo; preferible 2 para cambios de contrato cuando haya revisores disponibles.
- Dismiss stale approvals when new commits are pushed.
- Require conversation resolution.
- Require status checks to pass (seleccionar el job de CI cuando ya exista y haya ejecutado al menos una vez).
- Require branches to be up to date, si el equipo puede mantenerlo.
- Block force pushes.
- Restrict deletions.
- No permitir bypass, salvo administrador responsable y solo ante una emergencia documentada.

Para `main`, no permitir push directo. Las tareas ordinarias se fusionan a `develop`; solo una publicación revisada pasa de `develop` a `main`.

**Importante:** la rama `develop` ya existe, pero todavía debe comprobarse la configuración efectiva de las reglas de protección. El job CI y su nombre de check deben existir antes de poder marcarlos como requeridos. La protección no queda aplicada por subir este archivo: debe guardarse en Settings.

## 3. Configurar Pull Requests

En **Settings → General → Pull Requests**:
- Mantener habilitada la opción de Pull Requests.
- Habilitar **Allow squash merging** (recomendado para mantener historial legible).
- Opcional: deshabilitar merge commits y rebase si el equipo acuerda usar únicamente squash.
- Activar automáticamente eliminación de ramas head después del merge.

GitHub ya permite abrir PR en repositorios normales; lo que se debe exigir es que las ramas protegidas solo acepten cambios por PR.

## 4. Añadir colaboradores

En **Settings → Collaborators** añadir a cada integrante con permiso **Write**. No compartir cuentas. Cada integrante debe usar su propio usuario GitHub para que las asignaciones, commits y revisiones queden trazables.

## 5. Etiquetas recomendadas

Crear etiquetas con nombres consistentes:
- Tipo: `feature`, `bug`, `documentation`, `testing`, `infrastructure`.
- Área: `area:crud-viajes`, `area:crud-zonas`, `area:mid`, `area:integrations`, `area:devops`.
- Prioridad: `P0`, `P1`, `P2`, `P3`.
- Bloqueo: `blocked`, para identificar Issues que permanecen en `Por hacer` por una dependencia.

El estado de trabajo debe controlarse mediante el campo Status del Project, no duplicarse con etiquetas.

## 6. Flujo por integrante

1. Tomar una Issue de `Por hacer` cuando esté refinada, asignada y tenga prioridad.
2. Crear una rama desde `develop`, por ejemplo `feature/4-crud-viajes`.
3. Implementar y probar.
4. Abrir PR hacia `develop`, referenciar la Issue y completar la plantilla.
5. Un compañero revisa y aprueba; el autor corrige observaciones.
6. Tras CI verde y conversaciones resueltas, fusionar.
7. Verificar que la Issue se cierre y el elemento pase a `Hecho`.

## 7. Cadencia Scrumban y evidencia

- Realizar sincronizaciones cortas de 10–15 minutos varias veces por semana.
- Al cierre de cada semana, realizar revisión y retrospectiva.
- Guardar notas breves en `docs/meetings/` con fecha, avances, bloqueos y acciones acordadas.
- Acordar en el tablero del clúster los trabajos cruzados (contratos, scopes, rutas y gateway).
- Cada integrante debe tener PRs propios y revisar PRs de compañeros. El historial debe reflejar commits, comentarios y aprobaciones de todos.

## 8. Pendientes de configuración

- [x] Crear la rama `develop`.
- [ ] Crear el Project Kanban y sus campos.
- [ ] Añadir las 15 Issues actuales al Project.
- [ ] Aplicar límite WIP de máximo 2 Issues por persona en `En progreso`.
- [ ] Crear carpeta `docs/meetings/` para evidencias de sincronizaciones y retrospectivas.
- [ ] Verificar que LangWuu y Lyttchoide tengan permiso Write.
- [ ] Crear labels de tipo, área, prioridad y `blocked`.
- [ ] Activar reglas de protección en `main` y `develop`.
- [ ] Implementar CI y marcar su check como requerido cuando exista.
