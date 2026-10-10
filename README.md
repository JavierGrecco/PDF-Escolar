# PDF Escolar

[![Pruebas automatizadas](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/tests.yml)
[![Compilación de instaladores](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)

**Una aplicación de escritorio gratuita y de código abierto para seleccionar, ordenar y combinar páginas de varios PDF en un documento nuevo.** Funciona en Windows y macOS, tiene la interfaz en español y está pensada para docentes, familias y cualquier persona que necesite organizar documentos sin usar herramientas complicadas.

Los archivos se procesan **localmente en tu computadora**: no hace falta subir documentos a una página web, crear una cuenta ni instalar Python.

## Descargar y empezar

No descargues el código fuente para usar la aplicación. Elegí el archivo correspondiente a tu equipo:

### Windows

- **[PDF-Escolar.exe — versión portable](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar.exe):** descargalo y hacé doble clic. No requiere instalación.
- **[Instalador de Windows](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-Instalador-Windows.exe):** seguí los pasos que aparecen en pantalla.

### macOS

- **[Mac con procesador Intel](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-macOS-Intel.dmg)**
- **[Mac con chip Apple Silicon](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-macOS-Apple-Silicon.dmg)** — M1, M2, M3, M4 y posteriores.

En Mac, abrí el archivo DMG y arrastrá **PDF Escolar** a la carpeta **Aplicaciones**.

## Qué podés hacer

- **Trabajar con varios archivos:** reunir páginas de distintos PDF en un mismo documento final.
- **Elegir páginas:** seleccionar miniaturas visualmente o ingresar números y rangos, como `1-8, 12, 20-25`.
- **Reordenar con libertad:** cambiar el orden de los documentos y mezclar páginas individuales mediante miniaturas de distintos tamaños, arrastre o botones, con vista previa detallada de la página seleccionada.
- **Guardar un PDF nuevo:** elegir dónde guardarlo, sin alterar los documentos originales.
- **Herramientas PDF:** rotar páginas, recortar márgenes y separar páginas en archivos independientes, con operaciones que conservan el contenido del PDF sin convertirlo en imagen.
- **OCR local (beta):** convertir documentos escaneados en PDF buscables, para localizar, seleccionar y copiar texto reconocido. Requiere instalar un complemento opcional.
- **Seguir trabajando con facilidad:** la aplicación recuerda la última carpeta usada para elegir archivos.

## Cómo usarlo

1. Abrí PDF Escolar y agregá uno o más archivos PDF.
2. Entrá en **Elegir visualmente** para marcar las páginas o escribí los números y rangos que necesitás.
3. Elegí **Ordenar páginas…** para ajustar el tamaño de las miniaturas y reorganizar las hojas; o pulsá directamente **Crear PDF final** para revisar la secuencia antes de guardarla.
4. En la revisión, inspeccioná la página seleccionada y corregí el orden desde esa misma vista.
5. Confirmá y elegí dónde guardar el documento nuevo.

Para otras tareas, abrí **Herramientas PDF** desde la ventana principal. Podés girar páginas, recortar márgenes en milímetros o generar un PDF por página. Estas operaciones crean archivos nuevos y no reemplazan los originales.

## Seguridad y estado de los instaladores

Los PDF se procesan en el equipo y los originales no se modifican. La integración continua ejecuta pruebas automatizadas y comprueba los paquetes de Windows y macOS; también se recomienda completar las [pruebas manuales](docs/PRUEBAS-MANUALES.md) en computadoras de uso habitual.

**Importante:** los instaladores actuales no están firmados digitalmente. Windows o macOS pueden mostrar un aviso de seguridad al abrirlos. No desactives el antivirus ni las protecciones del sistema para abrir un archivo que te genere dudas.

## Ayuda, errores y sugerencias

- ¿Encontraste un problema o querés proponer una mejora? [Abrí un issue](https://github.com/JavierGrecco/PDF-Escolar/issues/new).
- ¿Querés comprobar el funcionamiento antes de distribuir una versión? Consultá la [lista de pruebas manuales](docs/PRUEBAS-MANUALES.md).
- ¿Buscás el código fuente? [Explorá el repositorio](https://github.com/JavierGrecco/PDF-Escolar).

## OCR local — versión beta

La beta incorpora **Crear PDF buscable (OCR)** en «Herramientas PDF». El complemento opcional permite reconocer texto de documentos escaneados, conservando la imagen de la página con una capa de texto que se puede buscar, seleccionar y copiar.

- En la primera instalación se necesita conexión a Internet para descargar el complemento desde GitHub. Después, el reconocimiento funciona sin conexión.
- Los documentos se procesan en la computadora; no se suben a ningún servidor.
- Disponible para **Windows x64** y **Mac con Apple Silicon (M1 o posterior) con macOS 15 o posterior**.
- **OCR no está disponible en Mac Intel**. La aplicación principal y sus herramientas de rotación, recorte y separación siguen funcionando en esos equipos.
- Esta es una versión beta: recomendamos comprobar el resultado con documentos propios no confidenciales antes de confiar en OCR para trabajos importantes. Los instaladores todavía no están firmados ni notarizados.

El complemento y sus avisos de licencia se distribuyen en una publicación separada: [Descargas OCR en Releases](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1).

## Hacia dónde va el proyecto

La experiencia de ordenamiento ya incluye **miniaturas pequeñas, medianas y grandes**, una vista detallada de la página seleccionada con su archivo y número de origen, y una ventana para ampliarla. Al pulsar **Crear PDF final**, la aplicación muestra la secuencia para revisarla y corregir el orden antes de elegir dónde guardar el documento. El área vacía de documentos también tiene un fondo explícito y coherente con la ventana principal.

También estamos definiendo una experiencia visual consistente para Windows y macOS: respetar el tema del sistema por defecto, ofrecer alternativas clara y oscura, mejorar la legibilidad y conservar el aspecto original de las páginas PDF en pantalla. La elección de temas y el editor visual descritos en la documentación son propuestas de evolución; no forman parte de la beta actual.

Las próximas etapas son el sistema de temas Sistema/Claro/Oscuro y, después, la rotación y el recorte visual en la previsualización. A más largo plazo, el modo de creación permitirá seleccionar regiones, excluir zonas, recomponer fragmentos de varios documentos e insertar consignas con texto enriquecido. Esas funciones avanzadas todavía no están implementadas.

- [Hoja de ruta de experiencia, previsualización y temas](docs/EXPERIENCIA-PREVISUALIZACION-Y-TEMAS.md)
- [Editor visual y composición](docs/EDITOR-VISUAL-Y-COMPOSICION.md)
- [Arquitectura de herramientas PDF y OCR](docs/ARQUITECTURA-HERRAMIENTAS-Y-OCR.md)

## Para desarrolladores

PDF Escolar está escrito en Python y usa Qt para la interfaz. Las instrucciones del entorno de desarrollo y de publicación están en la carpeta [docs](docs/).

El proyecto se distribuye bajo la [licencia MIT](LICENSE). El código fuente es público y las contribuciones que mejoren de forma concreta la utilidad, seguridad, compatibilidad o facilidad de uso son bienvenidas.
