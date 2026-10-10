# Seguimiento de estabilidad de la interfaz

## Actualización de usabilidad — 2026-10-10

- **PR #12:** [simplificar carga y avisos de PDF](https://github.com/JavierGrecco/PDF-Escolar/pull/12), fusionado.
- **Commit integrado:** [`539cf15734fb4385ab3c705c2bcc3ad23dc1a1de`](https://github.com/JavierGrecco/PDF-Escolar/commit/539cf15734fb4385ab3c705c2bcc3ad23dc1a1de).
- El área para agregar archivos se compacta al cargar PDF, pero conserva la opción de arrastrar y soltar.
- Los problemas al abrir múltiples PDF se resumen en una sola advertencia, con detalles técnicos expandibles.
- Los cambios que invalidan un orden manual ahora lo comunican al usuario.
- Se añadieron pruebas de regresión para esos estados. La CI del PR pasó en Ubuntu, Windows, macOS y el conjunto de dependencias para macOS Intel; los tres paquetes y su verificación también pasaron.
- En `main`, las pruebas y los tres paquetes se completaron correctamente. El job `Guardar instaladores en el repositorio` terminó en éxito y las descargas actuales ya están sincronizadas.


Última actualización: 2026-10-10

Este documento mantiene el estado técnico del trabajo para que pueda retomarse sin depender del historial de conversación.

## Estado final en GitHub

- **PR #12:** [UX: simplificar carga y avisos de PDF](https://github.com/JavierGrecco/PDF-Escolar/pull/12), fusionado y cerrado.
- **Commit de integración UX:** [`539cf15734fb4385ab3c705c2bcc3ad23dc1a1de`](https://github.com/JavierGrecco/PDF-Escolar/commit/539cf15734fb4385ab3c705c2bcc3ad23dc1a1de).
- **Último commit de descargas:** [`f52f70c7ecf7d3ae259313174476729862de5618`](https://github.com/JavierGrecco/PDF-Escolar/commit/f52f70c7ecf7d3ae259313174476729862de5618).
- **Versión actual en `descargas/`:** `0.1.0-dev.115`, compilada desde `539cf15734fb4385ab3c705c2bcc3ad23dc1a1de`.
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
- [Tests de `main` tras el PR #11](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38070031705): las cuatro plataformas en verde.
- [Tests de `main` tras el PR #12](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38071224623): las cuatro plataformas en verde.
- [Build y sincronización de descargas tras el PR #12](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38071224574): Windows, macOS Intel y macOS Apple Silicon, y sincronización a `main`, todos en éxito.

## Descargas actuales

El archivo [`descargas/INFORMACION-DE-DESCARGA.txt`](https://github.com/JavierGrecco/PDF-Escolar/blob/main/descargas/INFORMACION-DE-DESCARGA.txt) confirma:

- Versión: `0.1.0-dev.115`.
- Compilación: [Actions run 38071224574](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38071224574).
- Código fuente: `539cf15734fb4385ab3c705c2bcc3ad23dc1a1de`.

SHA-256 verificados en `descargas/INFORMACION-DE-DESCARGA.txt`:
```text
ba330a8e34e3da328946e3cb8f25742bbafacb8e42364810bbc1af5a5a19c9bd  descargas/PDF-Escolar.exe
6da66906906543ded912b009284f9ae4e4180f383cf29e593d9fb0ca950363ca  descargas/PDF-Escolar-Instalador-Windows.exe
cbf0a7bd79fa256961ce942e3372bcadc5e9a4836ca2f216908ec59a870d19a7  descargas/PDF-Escolar-macOS-Intel.dmg
38bb78cf5693e3718879805eeed295cf73e21afa41bf4dc05827de964661c6a8  descargas/PDF-Escolar-macOS-Apple-Silicon.dmg
```

## Pendiente antes de una versión estable

La CI valida el código y compila los paquetes, pero no reemplaza probarlos en equipos reales. Antes de declarar una versión estable, completar `docs/PRUEBAS-MANUALES.md`, en particular: instalar y abrir los paquetes en computadoras limpias con Windows, macOS Intel y Apple Silicon; probar arrastrar con mouse y touchpad; comprobar nombres largos y escalado de pantalla; y confirmar los casos de error y el orden del PDF exportado. También queda por resolver la firma digital/notarización para una distribución pública con menos advertencias de seguridad.

## Criterio de continuidad

No hay PR abiertos pendientes de integrar ni descargas pendientes de sincronizar en este checkpoint. Las versiones `0.1.0-dev` siguen siendo de desarrollo hasta completar las pruebas manuales y la preparación de firma/notarización para una distribución pública. Si aparece un nuevo problema de estabilidad, reproducirlo con la matriz normal, registrar el commit exacto y conservar los códigos de salida reales de cada proceso.
