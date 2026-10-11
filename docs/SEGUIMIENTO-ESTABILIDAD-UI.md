# Seguimiento de estabilidad, publicaciones y estado actual

**Última revisión:** 11 de octubre de 2026.

Este documento es el punto de continuidad técnica. La información de la sección «Estado actual» es la vigente; los hitos anteriores son historial y no deben usarse para inferir qué binarios están actualmente en `descargas/`.

## Estado actual

- **Último commit integrado en `main`:** `eaa4915dcf88c4cccb646f89484c1eccf24d0420` (PR #45, endurecimiento del flujo de publicación). Los checks previos a la fusión pasaron: [Tests #38111824211](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38111824211), [Build installers #38111824231](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38111824231) y [política del repositorio #38111824206](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38111824206). Las ejecuciones post-merge se dispararon para ese commit: [Tests #38112070867](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38112070867) y [Build installers #38112070884](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38112070884); consultá esos enlaces para el estado actualizado.
- **Organizador de páginas (PR #25 y PR #40):** incorpora tamaños de miniatura, vista detallada y ampliada y revisión interactiva del orden final antes de exportar. Cada miniatura muestra el número que ocupa en el PDF final y su página original. Si distintos PDF tienen el mismo nombre, la miniatura y la vista previa muestran también una etiqueta de carpeta; el tooltip conserva la ruta completa. Los avisos de miniaturas que no se pudieron generar se mantienen al reordenar, y la página sigue incluida en el documento final.
- **Ventanas adaptables (PR #33):** la ventana principal, el selector visual, el organizador y el visor ampliado calculan sus tamaños según el espacio disponible. «Herramientas PDF» permite desplazar las opciones sin ocultar los botones de acción. Las pruebas y la compilación de instaladores pasaron en Ubuntu, Windows, macOS Apple Silicon y el entorno de dependencias de Mac Intel: [Tests #38093698702](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38093698702), [Build installers #38093698657](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38093698657). Sigue pendiente la comprobación visual en equipos reales; está detallada en [PRUEBAS-MANUALES.md](PRUEBAS-MANUALES.md).
- **Actualización de la publicación (PR #34):** las acciones de publicación de la aplicación y del complemento OCR usan `softprops/action-gh-release@v3`. Se integró sin publicar una nueva versión.
- **Protecciones de publicación (PR #45):** antes de crear una Release, el workflow valida los cuatro instaladores de la versión exacta, calcula y adjunta `SHA256SUMS.txt`, rechaza una Release que ya exista y comprueba el commit de un tag existente. La sincronización de `descargas/` exige una versión explícita y la casilla de sincronización, y solo se ejecuta si la publicación terminó correctamente. El PR pasó pruebas, compilación de los tres instaladores y verificación conjunta; en las ejecuciones de validación las etapas de publicación y sincronización quedaron omitidas. La guía de mantenimiento está en [PUBLICAR-UNA-VERSION.md](PUBLICAR-UNA-VERSION.md).
- **Avisos de licencias (PR #36):** el menú «Ayuda → Licencias y componentes» muestra el manifiesto generado para cada compilación. El generador registra versiones y licencias declaradas, reúne los textos legibles localizados y adjunta los textos base oficiales de PySide con el commit upstream fijado. Las pruebas y compilaciones pasaron en todas las plataformas, y la verificación de instaladores fue correcta: [Tests #38095614894](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38095614894), [Build installers #38095614933](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38095614933). **La revisión legal manual sigue abierta**: el manifiesto automático no determina por sí solo la licencia aplicable a cada componente nativo.
- **Política de repositorio (PR #37):** un workflow de CI rechaza cambios manuales a `descargas/` desde PR y archivos nuevos o modificados de más de 20 MiB. Pasaron el control de política, las pruebas y la compilación/verificación de instaladores: [Policy #38095725409](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38095725409), [Tests #38095725368](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38095725368), [Build installers #38095725336](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38095725336). Esto evita parte del crecimiento accidental futuro, pero **no elimina los blobs que ya están en el historial**.
- **Medición del repositorio:** la API de GitHub reportó 720,906 KiB en el momento de la revisión. Los cuatro binarios de `descargas/` pesan aproximadamente 275 MB en el árbol actual. El [PR #43](https://github.com/JavierGrecco/PDF-Escolar/pull/43) ya integró un primer paso no destructivo: los enlaces principales del README usan los assets versionados de `v0.1.0-beta.1`, mientras los archivos de `descargas/` y sus rutas se conservan para compatibilidad con enlaces externos. Esto mejora la fijación de la versión servida por la guía, pero **no reduce el historial de Git**; para ello sigue pendiente una decisión separada sobre respaldo, coordinación y reescritura histórica. [Issue #32](https://github.com/JavierGrecco/PDF-Escolar/issues/32) sigue abierto.
- **Identificación de miniaturas (PR #40):** se agregó información visible del orden final, el número de página de origen y una distinción para nombres de archivos repetidos. Las pruebas de regresión comprueban el refresco de las etiquetas al mover páginas y la persistencia de los avisos de miniaturas. La CI del PR pasó y verificó los instaladores; queda pendiente la comprobación visual manual con documentos reales.
- **Pruebas manuales (PR #38):** el checklist ahora especifica escalado 100 %, 125 % y 150 %, una pantalla de 1366 × 768, miniaturas, ventanas sin maximizar, desplazamiento de herramientas y verificación del manifiesto de licencias. La ejecución física en equipos reales todavía no se ha realizado desde CI.
- **Diferencia entre código y descarga:** la descarga pública sigue en `v0.1.0-beta.1`; el PR #45 no publicó otra versión ni modificó los binarios actuales. **No anunciar las mejoras integradas en `main` como parte de la beta descargable todavía.** La próxima versión propuesta sigue siendo `0.1.0-beta.2`; ejecutá manualmente [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml) con esa versión, dejá desmarcada la sincronización directa salvo que necesites los enlaces raw antiguos, revisá `SHA256SUMS.txt` y confirmá la Release antes de anunciarla.
- **Versiones descargables actuales:** [PDF Escolar v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/v0.1.0-beta.1) y [complemento OCR v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1). Son versiones beta, no estables.
- **OCR:** es opcional y separado. Está disponible para Windows x64 y Mac con Apple Silicon (M1 o posterior) y macOS 15 o posterior. No está disponible en Mac Intel.
- **Editor visual:** el modelo de composición está integrado, pero la selección visual de regiones, el montaje de fragmentos y el editor de texto enriquecido siguen en desarrollo. Ver [EDITOR-VISUAL-Y-COMPOSICION.md](EDITOR-VISUAL-Y-COMPOSICION.md).

## Comprobaciones a la hora de retomar el trabajo

1. Revisar el [estado de GitHub Actions](https://github.com/JavierGrecco/PDF-Escolar/actions) y el commit objetivo de cada ejecución.
2. Consultar [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases) para verificar las versiones y los activos reales; no deducir una publicación solo porque un job comenzó.
3. Abrir [INFORMACION-DE-DESCARGA.txt](../descargas/INFORMACION-DE-DESCARGA.txt) y comprobar que la versión, el commit, la ejecución y los cuatro SHA-256 corresponden a los activos de `v0.1.0-beta.1`.
4. Completar [PRUEBAS-MANUALES.md](PRUEBAS-MANUALES.md) con equipos Windows, Mac Intel y Apple Silicon, según la función que se valida. OCR solo se prueba en Windows x64 y Apple Silicon con macOS 15+.
5. Reproducir fallos desde el log específico y el SHA exacto. No resumir una ejecución fallida como «CI verde» porque otros sistemas hayan terminado con éxito.

## Historial técnico previo

Los siguientes hitos documentan la evolución anterior de la interfaz y el motor; los enlaces son registros históricos:

- **PR #11:** estabilidad del ciclo de vida de miniaturas y tareas de interfaz, caché limitada de PDF fuente y limpieza al cerrar los diálogos.
- **PR #12:** simplificación de la carga de archivos, agrupación de errores y comunicación de cambios que invalidan el orden manual.
- Las ejecuciones anteriores de tests y builds verificaron Ubuntu, Windows, macOS Apple Silicon y el conjunto legado de macOS Intel. Para el estado actual, consultá las ejecuciones enlazadas en Actions, no solo los IDs históricos de este apartado.

## Descargas y checksums

La fuente de verdad para la compilación que está en los enlaces directos es el contenido actual de [descargas/INFORMACION-DE-DESCARGA.txt](../descargas/INFORMACION-DE-DESCARGA.txt). No copies checksums históricos en esta guía: al sincronizar nuevos binarios, ese manifiesto se regenera con el commit, la ejecución y los SHA-256 del lote publicado.

## Criterio de salida de beta

Antes de quitar la etiqueta beta:
- probar instalación, apertura y desinstalación en Windows y apertura desde Aplicaciones en macOS;
- comprobar en PDF reales la calidad de OCR, páginas giradas, documentos mixtos, escaneos inclinados y errores de entrada;
- confirmar que la capa de texto permite buscar, seleccionar y copiar sin degradar la imagen;
- cerrar los problemas críticos de integridad y de instalación;
- definir firma/notarización y notas de publicación para los instaladores públicos.
