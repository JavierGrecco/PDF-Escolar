# Seguimiento de estabilidad, publicaciones y estado actual

**Última revisión:** 10 de octubre de 2026.

Este documento es el punto de continuidad técnica. La información de la sección «Estado actual» es la vigente; los hitos anteriores son historial y no deben usarse para inferir qué binarios están actualmente en `descargas/`.

## Estado actual

- La aplicación principal funciona y se prueba mediante GitHub Actions en Ubuntu, Windows, macOS Apple Silicon y el conjunto de dependencias heredado de Mac Intel.
- El código ya integrado incluye selección y orden visual de páginas, combinación no destructiva y herramientas PDF nativas de rotación, recorte de márgenes y separación.
- La dirección de producto para el editor visual de composición está documentada en [EDITOR-VISUAL-Y-COMPOSICION.md](EDITOR-VISUAL-Y-COMPOSICION.md). Esa hoja de ruta no implica que la interfaz completa esté disponible en los instaladores.
- La beta OCR usa un complemento separado con OCRmyPDF y Tesseract. El motor se compila para Windows x64 y macOS Apple Silicon (M1 o posterior, macOS 14+). No se ofrecerá OCR para Mac Intel; las herramientas PDF existentes sí siguen estando disponibles allí.
- Los artefactos de CI de un PR prueban ese commit; no son sinónimo de un lanzamiento en GitHub Releases ni de una actualización de los enlaces de `descargas/`.
- Los instaladores no están firmados ni notarizados en esta etapa. La validación de Actions tampoco sustituye las pruebas manuales en equipos reales.
- No debe declararse una versión beta publicada hasta comprobar que existe la release de la aplicación y la release del complemento OCR, que incluyen sus paquetes para todas las plataformas admitidas, y que `descargas/INFORMACION-DE-DESCARGA.txt` identifica la versión sincronizada.

## Comprobaciones a la hora de retomar el trabajo

1. Revisar el [estado de GitHub Actions](https://github.com/JavierGrecco/PDF-Escolar/actions).
2. Consultar [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases) para verificar versiones y activos reales.
3. Abrir [INFORMACION-DE-DESCARGA.txt](../descargas/INFORMACION-DE-DESCARGA.txt) y confirmar versión, commit, ejecución y SHA-256 de los cuatro paquetes.
4. Completar [PRUEBAS-MANUALES.md](PRUEBAS-MANUALES.md) con Windows, Mac Intel y Apple Silicon, según la función que se valida. OCR solo se prueba en Windows x64 y Apple Silicon con macOS 14+.
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
