# Complemento OCR de PDF Escolar

Este directorio construye un complemento opcional para crear PDF buscables a partir de documentos escaneados. El complemento se ejecuta como un proceso separado de la aplicación principal.

## Por qué está separado

PDF-Escolar conserva una combinación especial de dependencias para Mac Intel antiguos. OCRmyPDF 17.13.0 necesita `pikepdf[pdfa]` 10.15 o posterior, incompatible con el `pikepdf==8.15.1` fijado para esa compilación. El complemento tiene su propio entorno y no cambia las dependencias del editor principal.

Usamos OCRmyPDF porque implementa la creación de la capa de texto y el tratamiento de PDFs complejos. PDF-Escolar proporciona una interfaz propia en español, empaquetado y validación locales. No copiamos el código de PDF Arranger.

## Idiomas y contenido

La primera distribución incluye Tesseract con los modelos `spa`, `eng` y `osd` de `tessdata_fast`. No requiere subir documentos: solo se descarga el complemento opcional desde una publicación oficial. Una vez instalado, el procesamiento del PDF funciona sin conexión.

## Construcción y restricciones de plataforma

El flujo `.github/workflows/build-ocr.yml` construye y prueba un paquete para Windows x64, Mac Intel y Mac Apple Silicon. El OCR requiere Tesseract, datos de idioma y bibliotecas nativas; no alcanza con empaquetar solamente los módulos de Python.

El complemento macOS se construye en runners modernos y **no debe anunciarse como compatible con macOS Catalina**. La aplicación principal conserva su compatibilidad actual; la disponibilidad del OCR depende de los requisitos mínimos del complemento.

## Prueba de humo

`smoke_test.py` genera un PDF de imagen sin texto digital, ejecuta el complemento empaquetado y comprueba que se puede extraer «PDF ESCOLAR» del resultado. Esto complementa, no sustituye, la prueba manual con escaneos reales.

## Licencias

- OCRmyPDF: MPL-2.0. El código original y los avisos de licencia deben conservarse; cualquier cambio a archivos MPL distribuidos se publica conforme a esa licencia.
- Tesseract: Apache-2.0.
- Modelos `tessdata_fast`: Apache-2.0.
- El paquete final es una redistribución de varias dependencias. La publicación debe incluir sus avisos y licencias, generados por el flujo y verificados antes de cada versión.

No usamos GPL-3.0 de PDF Arranger ni incorporamos su código.
