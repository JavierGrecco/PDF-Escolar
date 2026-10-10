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

En la ejecución de diagnóstico con HEAD `cb401bb2b5bd8368859e7e2f9e8cabe75be630a4`:
- Windows: éxito.
- macOS: éxito.
- macOS Intel / conjunto de dependencias antiguo: éxito.
- Ubuntu: fallo al finalizar el primer grupo de tres pruebas gráficas, pese a que las tres aserciones pasan.

Las pruebas del organizador ejecutadas individualmente pasaron. Eso todavía no identifica una causa raíz; podría ser la combinación de pruebas/objetos Qt al terminar el proceso. No considerar resuelto el problema ni ignorar el código de salida del proceso.

## Próximos pasos obligatorios

- [ ] Guardar este checkpoint en un commit (no depender solo del historial de conversación).
- [ ] Aislar el cierre anómalo ejecutando cada una de las seis pruebas GUI en procesos independientes en Ubuntu; anotar cuál reproduce el fallo.
- [ ] Comparar con la misma prueba aislada sobre `main` antes de atribuir el defecto a estos cambios.
- [ ] Corregir la causa raíz y añadir una regresión que falle antes de la corrección.
- [ ] Restaurar `.github/workflows/tests.yml` a una matriz normal que ejecute `ruff` y el conjunto completo de tests; retirar los filtros y comandos de diagnóstico.
- [ ] Ejecutar la matriz completa en Ubuntu, Windows, macOS y macOS Intel, y confirmar la creación de instaladores antes de sacar el PR de borrador.
- [ ] No integrar este PR hasta que el proceso pytest termine con código 0 en todos los jobs. La interacción de arrastrar/soltar también necesita una comprobación manual en un equipo real.

## Criterio de finalización

El PR se puede considerar listo únicamente cuando: el código está guardado en esta rama, el workflow normal está restaurado, todas las pruebas y builds terminan correctamente (sin crash durante la salida), y los cambios quedan revisables como un diff claro contra `main`.
