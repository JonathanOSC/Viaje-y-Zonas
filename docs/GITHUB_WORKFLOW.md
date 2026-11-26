# Configuración de GitHub para el equipo

Esta guía complementa `CONTRIBUTING.md`. La configuración de reglas de rama y Projects debe activarse en la interfaz de GitHub por una persona con permisos de administración.

## 1. Crear el tablero Kanban

En el repositorio, abrir **Projects → New project → Board**. Nombre sugerido: **Viajes y zonas – Sprint Board**.

Crear las vistas:
- **Board / Sprint actual**: agrupar por Status y filtrar por Sprint actual.
- **Backlog**: ordenar por Priority y filtrar Status = Backlog.
- **Por responsable**: agrupar por Assignees.
- **Roadmap**: vista Table con Issue, Priority, Sprint, Status y Assignees.

Campos sugeridos:
- `Status` (Single select): Backlog, Ready, In progress, In review, Blocked, Done.
- `Priority` (Single select): P0 - Bloqueante, P1 - Alta, P2 - Media, P3 - Baja.
- `Sprint` (Iteration): configurar iteraciones según las fechas reales del equipo.
- `Estimate` (Number): puntos o tamaño acordado.
- `Area` (Single select): CRUD Viajes, CRUD Zonas, MID, Integración, Calidad, DevOps, Documentación.

Añadir las Issues del repositorio al Project. Automatizar, cuando esté disponible, el estado al abrir/cerrar Issues y al abrir/mergear PRs. Mantener un responsable por Issue; dividir tareas grandes.

## 2. Proteger `main` y `develop`

En **Settings → Rules → Rulesets → New branch ruleset** (o Branch protection rules, según la interfaz):

Aplicar a `main` y `develop`:
- Require a pull request before merging.
- Required approvals: 1 como mínimo; preferible 2 para cambios de contrato.
- Dismiss stale approvals when new commits are pushed.
- Require conversation resolution.
- Require status checks to pass (seleccionar el job de CI cuando ya exista y haya ejecutado al menos una vez).
- Require branches to be up to date, si el equipo puede mantenerlo.
- Block force pushes.
- Restrict deletions.
- No permitir bypass, salvo administrador responsable y solo ante una emergencia documentada.

Para `main), no permitir push directo. Las tareas ordinarias se fusionan a `develop`; solo una publicación revisada pasa de `develop` a `main`.

**Importante:** en este momento el repositorio solo tiene `main`; el job CI y su nombre de check deben existir antes de poder marcarlos como requeridos. La configuración de protección no queda aplicada por subir un archivo al repositorio: debe guardarse en Settings.

## 3. Habilitar Pull Requests

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
- Estado: dejarlo preferiblemente en el campo Status del Project, no duplicarlo con labels.

## 6. Flujo por integrante

1. Mover la Issue de Backlog a Ready cuando esté refinada y tenga responsable.
2. Crear rama desde `develop`, por ejemplo `feature/12-crud-viajes`.
3. Implementar y probar.
4. Abrir PR hacia `develop), referenciar la Issue y completar la plantilla.
5. Un compañero revisa y aprueba; el autor corrige observaciones.
6. Tras CI verde y conversaciones resueltas, fusionar.
7. Verificar que la Issue se cierre y el elemento pase a Done.

## 7. Pendientes de configuración

- [ ] Crear la rama `develop`.
- [ ] Crear el Project Kanban y sus campos.
- [ ] Añadir colaboradores.
- [ ] Crear labels.
- [ ] Activar reglas de protección en `main` y `develop`.
- [ ] Implementar CI y marcar su check como requerido.
