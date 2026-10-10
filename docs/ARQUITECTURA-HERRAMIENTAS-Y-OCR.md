# Arquitectura de herramientas PDF y OCR local

**Estado revisado:** 10 de octubre de 2026. Esta guía distingue las funciones ya implementadas del trabajo de composición visual en desarrollo.

## Principios del producto

- Interfaz en español, directa y accesible para docentes, estudiantes y personas sin conocimientos técnicos.
- Procesamiento de los documentos en la computadora del usuario; no se suben PDF ni se envía contenido a servicios remotos.
- Instaladores para Windows y macOS que no exigen instalar Python manualmente.
- Edición no destructiva: los PDF de origen no se reemplazan. Las salidas se validan antes de publicarse.
- Compatibilidad consciente: la aplicación principal continúa compilándose para Windows x64, Mac Intel y Apple Silicon. El complemento OCR tiene una matriz de plataformas más acotada y no debe obligar a degradar las dependencias de la aplicación principal.

## Funciones PDF implementadas

Las herramientas nativas están en `src/pdf_escolar/pdf_tools.py` y usan `pikepdf`, que ya forma parte del proyecto.

- **Rotar páginas seleccionadas:** actualiza la rotación del PDF sin rasterizar el contenido.
- **Recortar márgenes:** ajusta el área visible a partir de medidas en milímetros.
- **Separar páginas:** genera un PDF por página seleccionada y evita sobrescribir archivos de salida existentes.
- **Integridad:** los resultados se preparan en ubicaciones temporales, se vuelven a abrir para su validación y recién entonces se publican. La ruta de origen y la ruta de salida no pueden ser iguales.

El recorte normal de PDF puede dejar datos fuera del área visible. No es una forma segura de censurar información confidencial; cualquier futura función de redacción debe eliminar el contenido y tener sus propias pruebas.

No se copia el código de PDF Arranger. Tomamos ideas funcionales como referencia, pero conservamos nuestra interfaz y nuestra implementación. Así evitamos introducir código GPL-3.0 en la aplicación MIT sin una decisión deliberada de licencia.

Referencia técnica: https://pikepdf.readthedocs.io/en/stable/topics/page.html

## Decisión para OCR

El OCR no es simplemente detectar letras. Hace falta reconocer páginas escaneadas, conservar su aspecto, colocar una capa de texto invisible y tratar páginas que ya contienen texto digital. No conviene implementar desde cero todo ese motor para la primera versión.

### Motor elegido: OCRmyPDF con Tesseract

OCRmyPDF aporta el flujo probado de reconocimiento y creación de PDF buscables; Tesseract hace el reconocimiento mediante modelos de idioma. PDF Escolar aporta la experiencia en español, la integración, la instalación del complemento, la validación de archivos y los mensajes para usuarios.

- OCRmyPDF: https://github.com/ocrmypdf/OCRmyPDF
- Documentación de instalación: https://ocrmypdf.readthedocs.io/en/latest/installation.html
- API: https://ocrmypdf.readthedocs.io/en/latest/api.html
- Licencia principal de OCRmyPDF: MPL-2.0.
- Tesseract y los modelos `tessdata_fast` utilizados por el complemento: Apache-2.0.

### Por qué el complemento se distribuye separado

La versión moderna de OCRmyPDF necesita un `pikepdf` reciente, incompatible con la versión antigua que la aplicación principal fija para el conjunto legado de Mac Intel. Por eso el motor se construye en un entorno separado; no altera las dependencias principales ni agranda todos los instaladores con Tesseract y los modelos OCR.

La aplicación invoca el complemento como un proceso separado, usando argumentos sin shell. El complemento crea el resultado en una ubicación temporal, verifica que sea un PDF legible y solo entonces publica el archivo final. El usuario conserva el PDF original.

El ZIP se descarga desde una publicación de GitHub, se verifica con el digest SHA-256 publicado por GitHub y se extrae con protección ante rutas inseguras. Se instala en el perfil del usuario, sin permisos de administrador. Tras instalarlo, el reconocimiento funciona sin conexión.

### Plataformas OCR admitidas

El complemento OCR se compila y prueba para:

- **Windows x64.**
- **macOS con Apple Silicon (M1 o posterior), macOS 15 o posterior.**

**Mac Intel no forma parte de la matriz OCR.** El motivo es mantener el motor moderno y sus dependencias nativas sin imponer versiones antiguas ni reducir la calidad de la integración. PDF Escolar sigue pudiéndose usar en Mac Intel para sus otras funciones PDF; la interfaz debe explicar que OCR no está disponible en ese equipo.

### Publicación, estado y límites

El flujo independiente `.github/workflows/build-ocr.yml` construye los dos paquetes y genera una prueba real de extremo a extremo: crea un PDF escaneado que solo contiene una imagen, ejecuta OCR en el paquete y verifica que el texto esperado se puede extraer. La beta inicial ya está publicada como [aplicación v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/v0.1.0-beta.1) y [complemento OCR v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1). Los SHA-256 de los dos paquetes OCR están publicados por GitHub y se verifican durante la instalación; los cuatro instaladores directos están sincronizados y enumerados en `descargas/INFORMACION-DE-DESCARGA.txt`.

Las pruebas automáticas demuestran que el complemento funciona con el documento de prueba, pero **no reemplazan la validación manual con escaneos reales**. Antes de considerar estable la función, hay que probar calidad con fotocopias, páginas rotadas, documentos mixtos (texto y escaneo), archivos extensos, PDF dañados o protegidos, y comprobar el resultado visual y la búsqueda/copia de texto.

## Alternativa evaluada: RapidOCR

RapidOCR es una alternativa con licencias permisivas en sus componentes principales, pero usarlo aquí también exigiría construir y mantener nosotros la generación de la capa de texto, el alineamiento de las palabras, la geometría de páginas y la preservación de la estructura del PDF. Se mantiene como opción futura si el empaquetado o la licencia de alguna dependencia de OCRmyPDF se vuelve inviable; no es el camino elegido para esta entrega.

- Proyecto: https://github.com/RapidAI/RapidOCR
- Licencias y procedencia de modelos: https://rapidai.github.io/RapidOCRDocs/main/en/model_licenses/
- Modelos e idiomas: https://rapidai.github.io/RapidOCRDocs/main/en/model_list/

## Editor visual de composición: dirección de producto

La rotación actual actúa sobre páginas enteras seleccionadas mediante números/rangos; no ofrece rotación libre arrastrando ni transformaciones de un fragmento. El recorte actual ajusta márgenes uniformes de una página; no permite seleccionar múltiples regiones arbitrarias ni excluir una zona dejando o recolocando automáticamente las demás. Esas herramientas actuales no deben confundirse con la composición visual futura.

Ya está integrado el primer modelo de composición en `src/pdf_escolar/document_model.py`: representa fuentes, páginas, fragmentos, bloques de texto, rectángulos normalizados y proyectos `.pdfescolar`, e incluye la operación geométrica de exclusión de regiones. Aún no está conectado a una interfaz de edición ni a un exportador de páginas compuestas.

La siguiente evolución de cara al usuario contempla:

- seleccionar una o varias regiones de una página mediante arrastre;
- conservar las regiones escogidas o excluir una zona sin seleccionar manualmente todo el resto;
- dividir el material en fragmentos independientes y mezclarlos en el orden que el usuario prefiera;
- crear páginas de composición con varios recortes y bloques de texto enriquecido;
- insertar consignas, títulos y carátulas; y guardar el trabajo como proyecto editable separado del PDF final.

La propuesta de interacción, modelo conceptual, arquitectura técnica y etapas están documentados en [EDITOR-VISUAL-Y-COMPOSICION.md](EDITOR-VISUAL-Y-COMPOSICION.md). Esa guía es una hoja de ruta, no una afirmación de que el editor completo ya esté en el instalador. El trabajo se implementará por etapas y no debe perjudicar la sencillez de la ventana inicial.

## Experiencia de orden, previsualización y apariencia

La ventana de ordenamiento ya incluye tres tamaños de miniatura, una vista detallada asíncrona de la página seleccionada y una vista ampliada que identifica archivo y página de origen. Las miniaturas siguen permitiendo arrastre para cambiar el orden y botones Subir/Bajar como alternativa. Al pulsar «Crear PDF final» se abre la revisión interactiva antes del selector de destino, salvo que la misma selección ya haya sido revisada y aplicada en «Ordenar páginas…». El orden confirmado es el que se entrega al exportador.

El área vacía de documentos tiene un color de fondo explícito para que no aparezca negra antes de cargar archivos. La solución completa de temas todavía está pendiente: respetar Sistema por defecto, ofrecer Claro y Oscuro como elecciones explícitas y mantener una paleta semántica centralizada. En cualquier tema, la página PDF debe conservar el aspecto real de su contenido.

La especificación, etapas y criterios de aceptación están en [EXPERIENCIA-PREVISUALIZACION-Y-TEMAS.md](EXPERIENCIA-PREVISUALIZACION-Y-TEMAS.md). Esta primera implementación no incluye aún zoom libre dentro del panel, eliminación de páginas desde la vista previa, edición de regiones, recomposición de fragmentos ni editor de texto enriquecido.

## Criterios de aceptación de OCR

- Los PDF del usuario nunca se envían a un servicio remoto.
- Los idiomas español e inglés están incluidos en el paquete, con versiones fijadas.
- El aspecto de la página se conserva y el texto reconocido se puede buscar, seleccionar y copiar.
- La salida contiene todas las páginas; la selección de páginas limita el procesamiento a las indicadas.
- El original y una salida existente permanecen intactos si ocurre un error.
- La interfaz permanece receptiva, comunica que el reconocimiento puede tardar y no muestra trazas técnicas.
- Los paquetes de Windows x64 y Apple Silicon superan build, smoke test y comprobación de licencias.
- Las pruebas manuales se registran antes de declarar la función estable.

## Referencias principales

- [Lista de pruebas manuales](PRUEBAS-MANUALES.md).
- [Preparación del entorno de desarrollo](ENTORNO-DE-DESARROLLO.md).
- [Guía de publicación](PUBLICAR-UNA-VERSION.md).
- [Seguimiento de estabilidad y compilaciones](SEGUIMIENTO-ESTABILIDAD-UI.md).
