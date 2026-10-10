# Seguimiento de estabilidad de la interfaz

Última actualización: 2026-10-10

Este documento conserva el contexto técnico para poder retomar el trabajo aunque se interrumpa la sesión. Revisar primero el estado de [PR #11](https://github.com/JavierGrecco/PDF-Escolar/pull/11), el último commit de la rama y el CI actual.

## Estado del repositorio

- Rama de trabajo: `fix/page-picker-task-lifecycle`.
- PR: [#11 — Endurecer tareas de miniaturas y cierre de ventanas](https://github.com/JavierGrecco/PDF-Escolar/pull/11).
- Estado del PR: abierto, en borrador, no integrado.
- Base: `main`; HEAD observado: `f5357729797ed9d1a70ed917434eeead26fdb205`.
- La matriz habitual de `.github/workflows/tests.yml` fue restaurada en el commit `7f5b6e79f5f7f7e15d3f359235c9062b0faa7992`. Ya no incluye el script de diagnóstico temporal.
- Las mejoras funcionales solicitadas están en `main`: nombre y páginas por archivo, reordenamiento de PDFs, recuerdo de la última carpeta y organizador visual de páginas con exportación en el orden elegido. Este PR es un seguimiento de estabilidad y rendimiento, no la primera implementación de esas cuatro funciones.

## Cambios propuestos en el PR #11

1. Selector visual y organizador con tareas de miniaturas limitadas a ventanas visibles y cancelación de trabajos obsoletos.
2. Retención/liberación explícita de tareas `QRunnable`, señal de finalización y manejo de excepciones en el hilo de miniaturas.
3. Finalización explícita de tareas de inspección/exportación en `finally`.
4. Caché LRU acotada (máximo 8 PDFs fuente abiertos) para exportar páginas intercaladas sin reabrir cada PDF en cada transición.
5. Prueba de exportación intercalada que comprueba el uso de fuentes.
6. Pruebas de cancelación y limpieza de widgets Qt; los widgets de pruebas se cierran y destruyen explícitamente con `deleteLater` y procesamiento de `DeferredDelete`.
7. El pool local del selector vuelve a estar asociado al diálogo (`QThreadPool(self)`), de modo que su ciclo de vida coincide con el del dueño.

## Historial de CI y diagnóstico Qt

CI histórico de `main`:
- [Run 38064894022](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38064894022): matriz habitual verde. El job Ubuntu ejecutó Ruff con éxito y reportó `33 passed`.

Diagnóstico temporal en la rama:
- Run [38068544414](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38068544414), HEAD `d251ea5906205ad2b7583b7d2d65662f1fd9475b`.
- En la rama, el módulo GUI entero pasó las 11 aserciones, pero el proceso terminó con `QObject: shared QObject was deleted directly` y SIGBUS (`exit=-7`). La suite entera pasó sus 39 tests y luego terminó con SIGSEGV (`exit=-11`).
- El mismo job creó un worktree del `main` real y lo comparó bajo el mismo entorno. El módulo GUI base pasó 6 tests y terminó con salida 0; la suite base reportó `33 passed`, pero terminó con SIGSEGV al ejecutarse dentro del script diagnóstico como subproceso.
- Tests nuevos del selector visual también mostraron SIGBUS intermitente en ejecución aislada: `test_page_picker_does_not_start_thumbnail_tasks_before_becoming_visible` y `test_page_picker_keeps_the_current_page_group_responsive`. Los tests de cancelación directa pasaron con salida 0.
- En otras ejecuciones completas de la rama, macOS también reportó `39 passed` antes de caer al salir. Windows reportó `39 passed` y código de salida 1. En macOS Intel, algunas ejecuciones sí fueron verdes.

Interpretación: hay una inestabilidad de cierre de Qt en los runners, pero los subprocesos del diagnóstico también reprodujeron SIGSEGV sobre la suite base, mientras que la matriz normal histórica de `main` finalizó correctamente. No afirmar todavía que toda la falla viene de una regresión específica del PR, y tampoco darla por resuelta. La evidencia nueva obliga a distinguir: resultado de las aserciones, código de salida del proceso y comportamiento en el workflow normal.

## Cambios después del diagnóstico

- Se agregó destrucción explícita de widgets de pruebas con `QEvent.Type.DeferredDelete` en `tests/test_gui_smoke.py`.
- Se volvió a asociar el pool del selector a su diálogo.
- Se restauró el workflow normal completo para Ubuntu, Windows, macOS y macOS Intel.
- Al guardar este checkpoint, el último HEAD de trabajo es `7f5b6e79f5f7f7e15d3f359235c9062b0faa7992`. Las acciones de ese commit deben revisarse antes de decidir el siguiente cambio.

## Próximos pasos obligatorios

- [ ] Verificar CI de HEAD `7f5b6e79f5f7f7e15d3f359235c9062b0faa7992` en la matriz habitual (no el diagnóstico).
- [ ] Si el cierre anómalo persiste, reducir primero el nuevo test o cambio de producción que lo introduce; no esconder el código de salida ni convertirlo en éxito.
- [ ] Si solo se reproduce en la matriz/runner con subprocesos pero no en el workflow normal, anotar evidencia de ambos caminos y evaluar una estrategia de limpieza de tests mínima y estable.
- [ ] Añadir una regresión específica para cualquier causa raíz confirmada.
- [ ] Confirmar build de instaladores y revisar diff final antes de sacar el PR de borrador.
- [ ] Comprobar arrastre/soltar real con touchpad o mouse en un equipo físico.
- [ ] No integrar el PR hasta que el workflow habitual y los builds estén verdes.

## Criterio de finalización

Cambios guardados en GitHub, workflow normal restaurado, tests y builds con código de salida 0, exportación validada en orden intercalado y diff final limpio y revisable contra `main`.
