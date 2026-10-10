# Avisos de terceros — complemento OCR

El complemento OCR se distribuye separado de PDF Escolar y contiene componentes de terceros. Las licencias y versiones exactas se incluyen en cada paquete, dentro de `licenses/`.

| Componente | Uso | Licencia | Fuente |
|---|---|---|---|
| OCRmyPDF 17.13.0 | Orquestación OCR y reconstrucción de la capa de texto | MPL-2.0 | https://github.com/ocrmypdf/OCRmyPDF/tree/v17.13.0 |
| Tesseract | Reconocimiento óptico de caracteres | Apache-2.0 | https://github.com/tesseract-ocr/tesseract |
| `tessdata_fast` (`spa`, `eng`, `osd`) | Modelos de idioma y orientación | Apache-2.0 | https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd |
| Dependencias Python | Procesamiento de PDF, imágenes y texto | Varias licencias permisivas y de código abierto | Inventario en `licenses/PYTHON-DEPENDENCIES.md` |

Los archivos de licencia originales de OCRmyPDF, Tesseract y `tessdata_fast`, así como el inventario de paquetes Python, deben incluirse en cada ZIP publicado. No se deben eliminar esos archivos ni los avisos de copyright.

OCRmyPDF está bajo MPL-2.0. PDF Escolar no modifica su código fuente: lo usa como componente separado. Si se distribuye una modificación de archivos fuente cubiertos por MPL, deberán cumplirse las obligaciones de publicación de esas modificaciones indicadas en la licencia.

Este inventario no sustituye una revisión de licencias antes de cada publicación. Al actualizar una dependencia o un modelo, debe regenerarse el inventario y comprobarse que la licencia sigue siendo compatible con la distribución.
