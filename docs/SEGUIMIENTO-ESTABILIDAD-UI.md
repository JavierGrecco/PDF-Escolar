# Seguimiento de estabilidad, publicaciones y estado actual

**Última revisión:** 10 de octubre de 2026.

Este documento es el punto de continuidad técnica. La información de la sección «Estado actual» es la vigente; los hitos anteriores son historial y no deben usarse para inferir qué binarios están actualmente en `descargas/`.

## Estado actual

- **Último commit integrado:** `09417b555813e325cf1a1687cd6f5e851bc10fda`. Integra la adaptación de las ventanas a pantallas pequeñas, además de la corrección de posición de vista previa y las mejoras documentales recientes.
- **Organizador de páginas (PR #25):** incluye tamaños de miniatura, vista detallada y ampliada, y revisión del orden final antes de exportar. [PR #25](https://github.com/JavierGrecco/PDF-Escolar/pull/25).
- **Ventanas adaptables (PR #33):** la ventana principal, el selector de páginas, el organizador y el visor ampliado calculan su tamaño según el espacio disponible. «Herramientas PDF» permite desplazar sus opciones mientras mantiene los botones de acción a la vista. Las pruebas pasaron en Ubuntu, Windows, macOS Apple Silicon y el conjunto de dependencias para Mac Intel ([Tests #38093698702](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38093698702)). Los paquetes de Windows, Mac Intel y Apple Silicon se compilaron y verificaron correctamente ([Build installers #38093698657](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38093698657)).
- **Actualización de publicación (PR #34):** las acciones de publicación de la app y de OCR usan `softprops/action-gh-release@v3`. Las pruebas y compilaciones de validación pasaron; las etapas de publicación estuvieron omitidas, por lo que no se publicó una nueva versión.
- **Diferencia entre código y descarga:** el código de `main` contiene las mejoras mencionadas, pero la descarga oficial todavía apunta a `v0.1.0-beta.1`. No anuncies las nuevas funciones como parte de la beta pública hasta publicar y comprobar una nueva versión. La siguiente beta prevista es `0.1.0-beta.2); verificación manual antes de anunciarla.
- **Versiones descargables vigentes:** la aplicación y el complemento OCR siguen publicados como versiones beta, no estables:
  - [PDF Escolar v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/v0.1.0-beta.1).
  - [Complemento OCR v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1).
- **OCR:** es opcional y separado. Está disponible para Windows x64 y Mac con Apple Silicon (M1 o posterior) y macOS 15 o posterior. No está disponible en Mac Intel.
- **Pendientes antes de una versión estable:** validar el diseño de las ventanas en equipos reales al 100 %, 125 % y 150 % de escalado, y en pantallas de poca altura; probar los instaladores en equipos limpios; revisar los avisos de licencias de terceros; decidir sobre firma digital y notarización. Las pruebas automatizadas no sustituyen estas comprobaciones manuales.
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
