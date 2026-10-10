# Seguimiento de estabilidad, publicaciones y estado actual

**Última revisión:** 10 de octubre de 2026.

Este documento es el punto de continuidad técnica. La información de la sección «Estado actual» es la vigente; los hitos anteriores son historial y no deben usarse para inferir qué binarios están actualmente en `descargas/`.

## Estado actual

- **Código principal posterior a la beta:** el PR [#25](https://github.com/JavierGrecco/PDF-Escolar/pull/25) se integró el 10 de octubre de 2026 en el commit `f0a1f52d337ffc21715c1a56b84944874d6d425c`. Añade tamaños de miniatura, vista detallada/ampliada, revisión interactiva antes de exportar y fondo explícito para el área vacía.
- **CI del PR #25:** todas las pruebas finalizaron correctamente en Ubuntu, Windows, macOS Apple Silicon y macOS Intel ([Tests #38092037062](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38092037062)); las compilaciones de Windows, macOS Intel y Apple Silicon y su verificación final también finalizaron correctamente ([Build installers #38092037060](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38092037060)).
- **Diferencia entre código y publicación:** los artefactos del PR son compilaciones temporales de validación; la ejecución no publicó un Release ni reemplazó `descargas/`. `descargas/INFORMACION-DE-DESCARGA.txt` sigue apuntando a `v0.1.0-beta.1`, por lo que la beta pública no incluye las mejoras visuales recientes. El artefacto `pdf-escolar-windows` puede descargarse desde la ejecución de Build installers anterior para validación; expira el 8 de enero de 2027.
- Para poner las mejoras en manos de usuarios como beta oficial, ejecutar manualmente [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml) desde `main`, con la versión `0.1.0-beta.2`. Verificar la publicación, los activos y el manifiesto de checksums antes de anunciarla.
- La aplicación y el complemento OCR están publicados como versiones **beta** coordinadas; no son versiones estables:
  - [PDF Escolar v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/v0.1.0-beta.1).
  - [Complemento OCR v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1).
- La aplicación principal pasó las pruebas de CI y los checks de empaquetado en Windows x64, macOS Intel y Apple Silicon. Ejecución: [Build installers #38087055313](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38087055313).
- OCR pasó la prueba integral de reconocimiento en Windows x64 y Apple Silicon con macOS 15 o posterior. Ejecución: [Build OCR companion #38087055391](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38087055391).
- Las pruebas automatizadas de la aplicación también finalizaron correctamente en Ubuntu, Windows, macOS Apple Silicon y el conjunto heredado de dependencias de Mac Intel: [Tests #38087055326](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38087055326).
- `descargas/INFORMACION-DE-DESCARGA.txt` se sincronizó con la beta `0.1.0-beta.1`, el commit `fee92b1c39dcce2576bbce8d0acfdf1b21f051d8` y la ejecución 38087055313. Sus cuatro SHA-256 coinciden con los digests de los activos de la release de la aplicación.
- El complemento OCR es opcional y separado. Está disponible para Windows x64 y Mac con Apple Silicon (M1 o posterior) y macOS 15 o posterior. Mac Intel mantiene las demás herramientas de PDF, pero no OCR.
- La dirección de producto para el editor visual de composición está documentada en [EDITOR-VISUAL-Y-COMPOSICION.md](EDITOR-VISUAL-Y-COMPOSICION.md). El modelo de composición está integrado, pero la interfaz de selección de regiones, el montaje de fragmentos y el editor de texto enriquecido siguen en desarrollo.
- Los instaladores no están firmados ni notarizados. La beta necesita validación manual con documentos reales y equipos limpios antes de considerarse estable. Las pruebas automáticas no sustituyen esas comprobaciones.

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
