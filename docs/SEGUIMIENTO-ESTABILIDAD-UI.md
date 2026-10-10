# Seguimiento de estabilidad de la interfaz

Última actualización: 2026-10-10

Este archivo es el punto de continuidad del trabajo sobre el ciclo de vida de las miniaturas. Si se interrumpe una sesión, empezar leyendo este documento, revisar el último commit de esta rama y comprobar el CI asociado a [PR #11](https://github.com/JavierGrecco/PDF-Escolar/pull/11).

## Estado del repositorio

- Rama de trabajo: `fix/page-picker-task-lifecycle`.
- PR: [#11 — Endurecer tareas de miniaturas y cierre de ventanas](https://github.com/JavierGrecco/PDF-Escolar/pull/11).
- Estado del PR: abierto, en borrador, sin integrar.
- Rama base: `main`; HEAD observado al iniciar este checkpoint: `f5357729797ed9d1a70ed917434eeead26fdb205`.
- Último HEAD conocido de esta rama antes de guardar este checkpoint: `cb401bb2b5bd8368859e7e2f9e8cabe75be630a4`.
- Las funcionalidades de usuario ya están presentes en `main`: nombre y cantidad de páginas por archivo, reordenamiento de documentos, recuerdo de carpeta, organizador visual de páginas y exportación que respeta la secuencia elegida. El PR #11 es una mejora de estabilidad/rendimiento posterior; no es donde se guardaron por primera vez esas cuatro funciones.

## Cambios propuestos en el PR #11

1. El selector visual de páginas y el organizador de páginas difieren miniaturas solo cuando las ventanas están visibles; cancelan solicitudes obsoletas.
2. Los trabajos `QRunnable` retienen explícitamente sus wrappers y usan señales de finalización con un token de texto; se eliminó el uso de lambdas como única forma de retirar referencias a tareas.
3. Las tareas de inspección y exportación informan su finalización desde `finally`, y la ventana principal retira explícitamente la tarea finalizada.
4. El exportador mantiene una caché LRU acotada (máximo 8 documentos fuente abiertos) para no reabrir un PDF en cada alternancia de páginas entre documentos.
5. Se agregaron pruebas de cancelación y de reutilización de fuentes intercaladas.
6. El manejo de errores inesperados al preparar miniaturas garantiza que la tarea emita su señal de finalización.

## Hallazgo de CI que bloquea la integración

En Ubuntu, Ruff termina correctamente y las aserciones de las pruebas gráficas terminan en verde, pero el proceso Python se cae durante la salida con el mensaje de Qt `QObject: shared QObject was deleted directly` y un `Segmentation fault` o `Bus error`. En ejecuciones previas del conjunto completo llegaron a pasar 39 tests antes de que el proceso fallara al salir.

En la ejecución diagnóstica con HEAD `1e2d5e482fdd79fd962617e09ef68467f1878d30`:
- Windows: éxito.
- macOS: éxito.
- macOS Intel / conjunto de dependencias antiguo: éxito.
- Ubuntu: falla en la salida del proceso; el job conservó el código de salida y falló como corresponde.
- El job de Ubuntu ejecutó cada uno de los seis tests GUI en procesos independientes y luego prefijos acumulativos.

Resultados individuales:
- `test_main_window_starts_in_a_safe_empty_state`: 1 passed, salida 0.
- `test_document_card_displays_the_full_pdf_name_and_page_count`: 1 passed, luego el warning de Qt y salida `-11` (SIGSEGV).
- `test_page_order_dialog_supports_drag_and_button_reordering`: 1 passed, salida 0.
- `test_last_open_directory_uses_a_saved_existing_folder`: 1 passed, salida 0.
- `test_document_cards_can_be_reordered_by_drop_and_buttons`: 1 passed, salida 0.
- `test_hidden_page_order_dialog_does_not_start_thumbnail_tasks`: 1 passed, salida 0.

El prefijo de los primeros dos tests terminó bien, pero al agregar el tercero hubo SIGSEGV; los prefijos posteriores también fallaron al salir. Esto muestra que no basta con decir que “se cae la combinación de diálogos”: el test de la tarjeta también reproduce el problema cuando se ejecuta aislado como primer widget del proceso.

Como referencia, el CI histórico de `main` en la ejecución [38064894022](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38064894022) acabó con Ruff verde y `33 passed` en Ubuntu, sin crash. Aún falta una comparación controlada de la prueba de tarjeta sobre el mismo commit base y con el mismo entorno.

HEAD posterior `6fddf937004931771977edd51035d640bb7d897d` mueve imports auxiliares a los tests que realmente los necesitan, para comprobar si retener referencias de clases Qt en el módulo de tests contribuye al crash. Esa hipótesis aún no está confirmada; su CI está ejecutándose. No considerar resuelto el problema ni ignorar el código de salida.

## Próximos pasos obligatorios

- [x] Guardar este checkpoint en un commit (no depender solo del historial de conversación).
- [x] Aislar el cierre anómalo ejecutando cada una de las seis pruebas GUI en procesos independientes en Ubuntu; anotar cuál reproduce el fallo.\n- [ ] Comparar la prueba de tarjeta de manera aislada en la rama base con el mismo entorno y la misma versión de PySide6.
- [ ] Comparar con la misma prueba aislada sobre `main` antes de atribuir el defecto a estos cambios.
- [ ] Corregir la causa raíz y añadir una regresión que falle antes de la corrección.
- [ ] Restaurar `.github/workflows/tests.yml` a una matriz normal que ejecute `ruff` y el conjunto completo de tests; retirar los filtros y comandos de diagnóstico.
- [ ] Ejecutar la matriz completa en Ubuntu, Windows, macOS y macOS Intel, y confirmar la creación de instaladores antes de sacar el PR de borrador.
- [ ] No integrar este PR hasta que el proceso pytest termine con código 0 en todos los jobs. La interacción de arrastrar/soltar también necesita una comprobación manual en un equipo real.

## Criterio de finalización

El PR se puede considerar listo únicamente cuando: el código está guardado en esta rama, el workflow normal está restaurado, todas las pruebas y builds terminan correctamente (sin crash durante la salida), y los cambios quedan revisables como un diff claro contra `main`.
