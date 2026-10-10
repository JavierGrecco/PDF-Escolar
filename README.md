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
- **Reordenar con libertad:** cambiar el orden de los documentos y mezclar páginas individuales mediante miniaturas, arrastre o botones.
- **Guardar un PDF nuevo:** elegir dónde guardarlo, sin alterar los documentos originales.
- **Seguir trabajando con facilidad:** la aplicación recuerda la última carpeta usada para elegir archivos.

## Cómo usarlo

1. Abrí PDF Escolar y agregá uno o más archivos PDF.
2. Entrá en **Elegir visualmente** para marcar las páginas o escribí los números y rangos que necesitás.
3. Ordená los documentos y, si querés mezclar páginas de distintas fuentes, elegí **Ordenar páginas…**.
4. Revisá el orden final y pulsá **Crear PDF final**.
5. Elegí dónde guardar el documento nuevo.

## Seguridad y estado de los instaladores

Los PDF se procesan en el equipo y los originales no se modifican. La integración continua ejecuta pruebas automatizadas y comprueba los paquetes de Windows y macOS; también se recomienda completar las [pruebas manuales](docs/PRUEBAS-MANUALES.md) en computadoras de uso habitual.

**Importante:** los instaladores actuales no están firmados digitalmente. Windows o macOS pueden mostrar un aviso de seguridad al abrirlos. No desactives el antivirus ni las protecciones del sistema para abrir un archivo que te genere dudas.

## Ayuda, errores y sugerencias

- ¿Encontraste un problema o querés proponer una mejora? [Abrí un issue](https://github.com/JavierGrecco/PDF-Escolar/issues/new).
- ¿Querés comprobar el funcionamiento antes de distribuir una versión? Consultá la [lista de pruebas manuales](docs/PRUEBAS-MANUALES.md).
- ¿Buscás el código fuente? [Explorá el repositorio](https://github.com/JavierGrecco/PDF-Escolar).

## Para desarrolladores

PDF Escolar está escrito en Python y usa Qt para la interfaz. Las instrucciones del entorno de desarrollo y de publicación están en la carpeta [docs](docs/).

El proyecto se distribuye bajo la [licencia MIT](LICENSE). El código fuente es público y las contribuciones que mejoren de forma concreta la utilidad, seguridad, compatibilidad o facilidad de uso son bienvenidas.
