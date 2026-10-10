# Arquitectura de herramientas PDF y OCR local

## Objetivo

Ampliar PDF Escolar sin perder sus prioridades:

- Interfaz en español para personas que no usan herramientas de programación.
- Procesamiento local de los documentos; no se suben PDF a ningún servicio.
- Instaladores utilizables con doble clic en Windows y macOS.
- Los originales no se modifican y un error no debe destruir un archivo de salida previo.
- Compatibilidad de macOS Intel: el proyecto mantiene un conjunto de dependencias antiguo para seguir admitiendo equipos que no pueden usar los wheels más recientes de algunas bibliotecas PDF.

## Operaciones que implementa PDF Escolar

Las herramientas de rotación, recorte de márgenes y separación se implementan en el módulo `src/pdf_escolar/pdf_tools.py` sobre `pikepdf`, que ya forma parte de la aplicación.

- **Rotar:** modifica el atributo de rotación de las páginas seleccionadas; no rasteriza el documento.
- **Recortar márgenes:** ajusta la `CropBox` en unidades PDF a partir de márgenes en milímetros. Esto oculta contenido fuera del área visible, pero **no lo borra de forma segura**. No debe utilizarse como herramienta de censura o redacción de datos confidenciales.
- **Separar páginas:** crea un PDF por página seleccionada, prepara los archivos en un directorio temporal y evita reemplazar nombres de salida existentes.
- **Integridad:** los resultados se escriben primero en archivos temporales y se vuelven a abrir para comprobar que el PDF tiene páginas antes de reemplazar el destino. La ruta de origen y la ruta de salida deben ser diferentes.

No copiamos el código de PDF Arranger. Su licencia GPL-3.0 implica obligaciones que preferimos no introducir sin una necesidad técnica y un análisis legal explícitos. Podemos implementar operaciones equivalentes usando nuestras propias interfaces y las bibliotecas que ya usa el proyecto.

Referencia técnica de pikepdf: https://pikepdf.readthedocs.io/en/stable/topics/page.html

## Decisión para el OCR

El OCR es un problema distinto de la edición de páginas. Reconocer letras, evaluar la orientación y construir una capa de texto invisible con posiciones correctas exige un motor entrenado y un tratamiento cuidadoso del PDF de entrada.

### Motor preferido para el primer prototipo: OCRmyPDF

OCRmyPDF ya resuelve problemas difíciles que no conviene volver a implementar a ciegas: reconocer páginas con texto existente, crear una capa de texto buscable, conservar en general el contenido visual, procesar idiomas, corregir orientación y enderezar páginas.

- Proyecto: https://github.com/ocrmypdf/OCRmyPDF
- Instalación y requisitos: https://ocrmypdf.readthedocs.io/en/latest/installation.html
- API: https://ocrmypdf.readthedocs.io/en/latest/api.html
- Licencia principal: MPL-2.0. Antes de redistribuir el paquete final hay que conservar los avisos y comprobar las licencias de todos los componentes incluidos.

**No conviene agregar OCRmyPDF como dependencia del entorno principal**: su versión más reciente requiere una versión de pikepdf considerablemente más nueva que la que mantenemos para el conjunto de dependencias de Mac Intel/Catalina. Tampoco sirve pedir a docentes y familias que instalen Python, Tesseract o Ghostscript manualmente.

### Arquitectura de distribución propuesta

La aplicación principal y el motor OCR deben construirse como componentes desacoplados:

1. PDF Escolar mantiene sus dependencias actuales y las nuevas operaciones de página.
2. Un componente OCR autónomo por plataforma se construye en un entorno separado. Incluye una versión fijada de OCRmyPDF, Tesseract y los datos de idioma que distribuyamos; debe utilizar rasterización por pypdfium2 para evitar una dependencia obligatoria de Ghostscript para el flujo común.
3. La aplicación detectará ese componente y lo invocará mediante argumentos separados, no a través de una cadena de comandos de shell. La salida se escribirá en un archivo temporal, se validará y recién entonces se publicará en la ubicación elegida.
4. La distribución del componente incluirá la licencia MPL-2.0 y los avisos de los componentes y modelos redistribuidos. Cada artefacto publicado debe tener un SHA-256 verificable.
5. El complemento OCR será opcional y descargable por separado para no aumentar innecesariamente los instaladores base. La primera instalación podrá descargarse desde una versión oficial del repositorio; después deberá poder trabajar sin conexión.
6. Antes de ofrecerlo como disponible se probará en Windows, macOS Intel y Apple Silicon, con PDF escaneados en español, documentos mixtos con texto ya existente y PDF dañados/protegidos.

Documentación oficial confirma que OCRmyPDF requiere Tesseract y que en Windows la instalación nativa requiere varios pasos; por eso empaquetar y validar el componente por plataforma forma parte del trabajo de ingeniería, no es un detalle que deba resolver cada persona usuaria.

### Alternativa evaluada: RapidOCR

RapidOCR y sus modelos actuales tienen licencias Apache-2.0 y ofrecen rutas para texto en escrituras latinas, incluido español. Sin embargo, elegirlo significa construir, probar y mantener nosotros mismos la creación de la capa invisible, el alineamiento de los cuadros de texto, la geometría de páginas rotadas y la preservación de detalles del PDF. Eso puede ser una buena alternativa si el empaquetado independiente de OCRmyPDF resulta inviable, pero no es la primera opción para obtener una primera versión fiable.

- Proyecto: https://github.com/RapidAI/RapidOCR
- Licencias de los modelos y procedencia: https://rapidai.github.io/RapidOCRDocs/main/en/model_licenses/
- Modelos e idiomas: https://rapidai.github.io/RapidOCRDocs/main/en/model_list/

## Criterios de aceptación para OCR

- Se trabaja completamente en la computadora del usuario.
- El idioma español funciona con un paquete de idioma incluido y fijado en la versión.
- La apariencia de las páginas escaneadas se mantiene; el texto reconocido es invisible, buscable y copiable.
- Las páginas que ya contienen texto no se vuelven a rasterizar de forma innecesaria.
- La operación no modifica el original y no reemplaza una salida previa cuando ocurre un error.
- La interfaz muestra el progreso, permite entender fallos y no expone trazas técnicas.
- Los PDFs de prueba demuestran que se puede extraer el texto reconocido en Linux, Windows y macOS.
- El componente OCR y sus licencias quedan documentados, versionados y verificables por SHA-256.

## Secuencia de entrega

1. Incorporar las herramientas nativas y sus pruebas automatizadas.
2. Prototipar el componente OCR autónomo y medir tamaño, compatibilidad y dependencias reales en CI.
3. Integrar la detección, instalación segura y ejecución del complemento en la interfaz.
4. Validar OCR manualmente con documentos reales en español y equipos limpios.
5. Publicar el componente OCR y actualizar la aplicación solo cuando la experiencia completa sea fiable.
