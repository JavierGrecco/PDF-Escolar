# Seguimiento de estabilidad de la interfaz

Última actualización: 2026-10-10

Este documento conserva el contexto del trabajo técnico aunque se interrumpa la sesión. Si se retoma, revisar este archivo, el [PR #11](https://github.com/JavierGrecco/PDF-Escolar/pull/11) y el último commit de la rama.

## Estado real en GitHub

- Rama del PR: `fix/page-picker-task-lifecycle`.
- PR: [#11 — Endurecer tareas de miniaturas y cierre de ventanas](https://github.com/JavierGrecco/PDF-Escolar/pull/11).
- Rama base `main` observada: `f5357729797ed9d1a70ed917434eeead26fdb205`.
- Historial de la implementación conservado en [`archive/pr11-ui-task-lifecycle-before-squash`](https://github.com/JavierGrecco/PDF-Escolar/tree/archive/pr11-ui-task-lifecycle-before-squash).
- Commit consolidado con CI verde conservado en [`archive/pr11-squashed-ci-passed`](https://github.com/JavierGrecco/PDF-Escolar/tree/archive/pr11-squashed-ci-passed).
- La matriz habitual de `.github/workflows/tests.yml` está restaurada, sin comandos temporales de diagnóstico.
- Aún no marcar como integrado hasta que pase la CI del último commit y se complete la fusión del PR.

## Funcionalidades y cambios

Las cuatro mejoras funcionales solicitadas están en `main`: nombre y cantidad de páginas por PDF, reordenar documentos, recordar última carpeta y ordenar páginas visualmente entre varios PDF. Este PR #11 es un seguimiento de estabilidad/rendimiento, no la primera implementación de esas funciones.

1. El selector visual y el organizador cancelan tareas de miniaturas obsoletas y limitan el trabajo cuando los diálogos no están visibles.
2. Las tareas `QRunnable` retienen sus wrappers hasta la señal de finalización; inspección/exportación liberan sus tareas explícitamente.
3. El motor tiene una caché LRU acotada (máximo 8 PDF fuente abiertos) para exportar secuencias intercaladas.
4. Las pruebas cubren orden, cancelación, reutilización de fuentes y limpieza explícita de widgets Qt.
5. El pool del selector está asociado al propio diálogo. Al terminar cada diálogo modal, se detienen/cancelan las miniaturas, se espera a que el pool termine, se captura la selección y se llama a `deleteLater()` para evitar acumular ventanas hijas ocultas.
6. El checklist manual ya no promete un aviso al cerrar la aplicación durante la exportación, comportamiento que no está implementado.

## Evidencia de CI ya comprobada

En el commit consolidado anterior `8b87b96966bd76e932fd5d7a6b1d1ae8c1c77031`:
- [Tests run 38069169063](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38069169063): Ubuntu, Windows, macOS y macOS Intel, todos en éxito. Ubuntu/macOS reportaron `39 passed`, Ruff verde y sin crash de Qt al salir.
- [Build run 38069169154](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38069169154): instalador de Windows, DMG Intel y DMG Apple Silicon en éxito, y `Verify generated installers` también pasó.
- Durante el diagnóstico previo aparecieron SIGSEGV/SIGBUS en algunos subprocesos, incluso en ciertas comparaciones contra un worktree real de `main`. La matriz habitual normal fue la que confirmó estabilidad; no se ocultaron códigos de salida ni se omitieron pruebas.
- La ejecución de PR no publica los paquetes dentro de `descargas/`; eso se ejecuta tras un push a `main`. Después de fusionar hay que verificar que el workflow de `main` actualice los binarios y `descargas/INFORMACION-DE-DESCARGA.txt`.

## Próximos pasos

- [ ] Ejecutar y verificar CI/tests/paquetes sobre el commit actual, que añade la eliminación diferida de los diálogos tras capturar la selección.
- [ ] Si la matriz normal y los builds están verdes, sacar el PR de borrador y fusionar.
- [ ] Confirmar el workflow posterior a la fusión y la actualización de `descargas/`.
- [ ] Hacer la prueba manual real de arrastrar/soltar con mouse y touchpad.

## Criterio de finalización

PR integrado, CI y builds verdes, descargas actualizadas, suite sin crash al finalizar y validación manual del arrastre/soltar documentada.
