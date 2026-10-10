# Seguimiento de estabilidad de la interfaz

Última actualización: 2026-10-10

Este documento mantiene el estado técnico del trabajo para que pueda retomarse sin depender del historial de conversación.

## Estado final en GitHub

- **PR #11:** [Endurecer tareas de miniaturas y cierre de ventanas](https://github.com/JavierGrecco/PDF-Escolar/pull/11), fusionado y cerrado.
- **Commit de integración:** [`ff5a949b077e23b58e8bfb434dc8fc3e22c00f64`](https://github.com/JavierGrecco/PDF-Escolar/commit/ff5a949b077e23b58e8bfb434dc8fc3e22c00f64).
- **Commit que actualizó las descargas:** [`c5d65c45b30db30a44d55a9e07e4d0be2793a4a2`](https://github.com/JavierGrecco/PDF-Escolar/commit/c5d65c45b30db30a44d55a9e07e4d0be2793a4a2).
- **Versión de los instaladores en `descargas/`:** `0.1.0-dev.113`, compilada desde `ff5a949b077e23b58e8bfb434dc8fc3e22c00f64`.
- **Historial incremental previo al squash:** [`archive/pr11-ui-task-lifecycle-before-squash`](https://github.com/JavierGrecco/PDF-Escolar/tree/archive/pr11-ui-task-lifecycle-before-squash).
- **Snapshot del commit squash previo a la última limpieza de diálogos:** [`archive/pr11-squashed-ci-passed`](https://github.com/JavierGrecco/PDF-Escolar/tree/archive/pr11-squashed-ci-passed).

## Funcionalidades de usuario conservadas

Las cuatro mejoras pedidas ya estaban en `main` antes del PR #11 y permanecen allí:
1. Mostrar el nombre y la cantidad de páginas de cada PDF.
2. Reordenar documentos con arrastrar/soltar y controles para subir/bajar.
3. Recordar la última carpeta utilizada al agregar archivos.
4. Ordenar páginas individuales visualmente, incluso alternando entre distintos PDF, y exportar respetando esa secuencia.

El PR #11 fue la etapa de estabilidad y rendimiento que vino después.

## Cambios fusionados

- Selector y organizador de páginas con cancelación de tareas de miniaturas obsoletas.
- Pools de miniaturas vinculados a sus diálogos; al finalizar los diálogos modales, se detienen las tareas, se espera a que los pools terminen y se marca el diálogo para destrucción diferida.
- Retención y liberación explícita de tareas `QRunnable`, con señales de finalización y manejo de excepciones.
- Tareas de inspección/exportación gestionadas hasta su finalización.
- Caché LRU limitada a ocho PDF fuente abiertos para evitar reabrir repetidamente archivos al exportar secuencias intercaladas.
- Pruebas de cancelación, limpieza de widgets y reutilización de fuentes; actualización de las pruebas manuales.

## Validación de CI

Las ejecuciones siguientes finalizaron con éxito:

- [Tests del commit final del PR](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38069733708): Ubuntu, Windows, macOS y macOS Intel.
- [Builds del commit final del PR](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38069733710): portable/instalador de Windows, DMG macOS Intel, DMG macOS Apple Silicon y verificación de artefactos.
- [Tests de `main` tras la integración](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38070031705): las cuatro plataformas en verde.
- [Build y sincronización de descargas tras la integración](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38070031656): los tres paquetes compilados y el job `Guardar instaladores en el repositorio` en éxito.

## Descargas actuales

El archivo [`descargas/INFORMACION-DE-DESCARGA.txt`](https://github.com/JavierGrecco/PDF-Escolar/blob/main/descargas/INFORMACION-DE-DESCARGA.txt) confirma:

- Versión: `0.1.0-dev.113`.
- Compilación: [Actions run 38070031656](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38070031656).
- Código fuente: `ff5a949b077e23b58e8bfb434dc8fc3e22c00f64`.

SHA-256 de los archivos visibles en `descargas/`:
```text
f0570580fd7cde162a9eebf1aaeac4cdf1a4fecb492936d152210c22c628e0ff  descargas/PDF-Escolar.exe
e2909f7255896cca780cc826065ca70e6865822e86796586abc8eaac07a71d34  descargas/PDF-Escolar-Instalador-Windows.exe
91b324d8d12ee5fa9847d959275573a4e491407d5ca216c1c4c01a9ba27f888f  descargas/PDF-Escolar-macOS-Intel.dmg
24065cef8cf33943cbe7bcb4ddca7c4fe3095a3a9954192eda455a04d057f02c  descargas/PDF-Escolar-macOS-Apple-Silicon.dmg
```

## Único pendiente manual

Probar en un equipo físico el arrastre para reordenar documentos y páginas, tanto con mouse como con touchpad. La CI verifica las pruebas automatizadas, pero no puede sustituir esa comprobación de interacción real.

## Criterio de continuidad

No hay cambios de código del PR pendientes de integrar ni descargas pendientes de sincronizar en este checkpoint. Si aparece un nuevo problema de estabilidad, reproducirlo con la matriz normal, registrar el commit exacto y conservar los códigos de salida reales de cada proceso.
