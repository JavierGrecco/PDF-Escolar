# PDF Escolar

[![Pruebas automatizadas](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/tests.yml)
[![Compilación de instaladores](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml/badge.svg?branch=main)](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)

**Elegí páginas de varios PDF, ordenalas y guardalas en un documento nuevo.**

Soy Javier, programador, y estoy desarrollando PDF Escolar para hacer más simple una tarea concreta: armar el PDF que necesitás sin depender de herramientas complicadas. Es una aplicación gratuita, de código abierto y con la interfaz en español, para Windows y macOS.

Los documentos se procesan en tu computadora. No tenés que subirlos a una página web, crear una cuenta ni instalar Python.

## Antes de descargar

La versión oficial disponible es **0.1.0-beta.1**. Es una beta, no una versión estable. En otras palabras: ya se puede probar y usar, pero todavía puede tener errores.

**Los instaladores no tienen firma digital y la aplicación para macOS no está notarizada.** Windows o macOS pueden mostrar advertencias al abrirlos. No desactives las protecciones del equipo para instalar un archivo que te genere dudas.

Aclaración importante: ya incorporé mejoras en la vista previa y en la revisión del orden dentro del código de la rama principal, pero **todavía no están incluidas en la beta pública**. Más abajo explico cuáles son.

## Descargar PDF Escolar

No hace falta descargar el código fuente para usar la aplicación. Elegí el archivo para tu equipo:

### Windows

- **[PDF-Escolar.exe — versión portable](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar.exe):** descargalo y hacé doble clic. No requiere instalación.
- **[Instalador para Windows](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-Instalador-Windows.exe):** abrilo y seguí los pasos en pantalla.

### macOS

- **[Mac con procesador Intel](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-macOS-Intel.dmg)**
- **[Mac con chip Apple Silicon](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-macOS-Apple-Silicon.dmg)** — M1, M2, M3, M4 y posteriores.

En Mac, abrí el archivo DMG y arrastrá PDF Escolar a la carpeta **Aplicaciones**.

También podés consultar los archivos y las notas de la versión en [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases). La versión de los enlaces directos se detalla en [la información de descarga](descargas/INFORMACION-DE-DESCARGA.txt), junto con el commit de origen y los SHA-256 de los archivos.

## Qué podés hacer con la beta pública

- **Combinar PDF:** reunir páginas de distintos archivos en un solo documento.
- **Elegir las páginas:** marcar miniaturas o indicar números y rangos, por ejemplo, 1-8, 12, 20-25.
- **Ordenar el resultado:** cambiar el orden de los documentos y reorganizar páginas individuales de distintos PDF.
- **Crear un archivo nuevo:** elegir dónde guardarlo. Los PDF originales no se modifican.
- **Girar páginas:** rotar páginas completas que elijas.
- **Recortar márgenes:** quitar márgenes uniformes indicando la medida.
- **Separar un PDF:** generar un archivo independiente por cada página.
- **Crear PDF buscables con OCR (beta):** reconocer texto en documentos escaneados para buscarlo, seleccionarlo y copiarlo. Es un complemento opcional.

Las herramientas de giro, recorte y separación trabajan sobre archivos nuevos. **El recorte de márgenes no borra de forma segura la información que queda fuera del área visible**; no lo uses como método para ocultar datos confidenciales.

## Cómo empezar

1. Abrí PDF Escolar y agregá uno o varios archivos PDF. También podés arrastrarlos a la ventana.
2. Elegí las páginas visualmente o escribí los números y rangos que necesitás.
3. Entrá en **Ordenar páginas…** para acomodar la secuencia antes de exportar.
4. Pulsá **Crear PDF final** y elegí dónde guardar el documento nuevo.

Para girar, recortar o separar páginas, abrí **Herramientas PDF** desde la ventana principal.

## OCR: qué necesitás saber

El reconocimiento de texto es opcional y está en beta.

- La primera vez necesitás conexión a Internet para descargar el complemento desde GitHub. Después, el reconocimiento funciona sin conexión.
- El documento se procesa en tu computadora; no se sube a un servidor para hacer el reconocimiento.
- Está disponible para **Windows x64** y **Mac con Apple Silicon (M1 o posterior) con macOS 15 o posterior**.
- **No está disponible en Mac Intel.** Las demás herramientas de PDF siguen disponibles en esos equipos.
- El resultado puede necesitar revisión, sobre todo si el escaneo está inclinado, borroso o tiene una calidad baja. Probalo primero con una copia de un documento.

El complemento y sus avisos de licencia están en la [publicación del motor OCR](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1).

## Qué estoy mejorando

Ya incorporé en el código principal:

- Miniaturas pequeñas, medianas y grandes.
- Una vista detallada de la página seleccionada, con su posición final, el archivo de origen y el número de página original.
- Una ventana para ampliar la página y examinarla con más detalle.
- Una revisión interactiva del orden final antes de elegir dónde guardar el PDF.
- Cada miniatura muestra su posición en el PDF final y el número de página original. Si varios archivos tienen el mismo nombre, se identifica también su carpeta de origen; la ruta completa queda disponible al pasar el cursor.
- Ventanas que ajustan su tamaño al espacio disponible; «Herramientas PDF» permite desplazarse por las opciones sin perder los botones de acción.
- Un menú **Ayuda → Licencias y componentes** para consultar las versiones y los avisos de licencia recopilados para esa compilación.

Las pruebas del cambio de identificación de miniaturas pasaron en Ubuntu, Windows, macOS y el entorno de macOS Intel; también se compilaron y verificaron los instaladores de Windows, Mac Intel y Apple Silicon. Las ejecuciones de validación son [Tests del PR #40](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38103933954) y [Build installers del PR #40](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38103933871). Tras integrar el cambio, las ejecuciones de `main` están volviendo a ejecutarse: [tests](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38110027412) y [compilación](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38110027394). **Estas mejoras todavía no forman parte de la beta descargable**. Antes de publicarlas en una nueva beta, falta comprobar visualmente su comodidad con documentos reales y distintos escalados de pantalla, y revisar los avisos generados para cada plataforma.

Si querés probar los cambios de interfaz antes de la próxima beta, podés descargar el artefacto temporal **pdf-escolar-windows** en la sección **Artifacts** de la [compilación de validación](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38092037060). Es solo para Windows, no es una publicación oficial y caduca el 8 de enero de 2027.

Más adelante quiero mejorar los temas claro y oscuro y desarrollar la edición visual de regiones y fragmentos de páginas. **Esas funciones todavía no están disponibles** en la aplicación.

## Ayuda y código fuente

Si encontrás un error o algo que podría ser más sencillo, podés [abrir un issue](https://github.com/JavierGrecco/PDF-Escolar/issues/new). Me sirve conocer qué estabas intentando hacer y qué ocurrió.

PDF Escolar está escrito en Python y usa Qt para la interfaz. Las notas para preparar el entorno y publicar una versión están en [docs](docs/). El código se distribuye bajo la [licencia MIT](LICENSE).
