# PDF Escolar

**Elegí páginas de tus libros PDF y guardalas en un solo documento.** Todo funciona localmente en tu computadora.

PDF Escolar está pensado para personas que quieren resolver esta tarea sin aprender herramientas técnicas.

## Para usar PDF Escolar (sin comandos ni Python)

**No hace falta abrir Terminal, usar PowerShell, escribir comandos ni instalar Python.** Cuando descargues una versión empaquetada, la aplicación incluye Python y sus dependencias.

### Windows

1. Descargá el archivo `PDF-Escolar-Instalador-…-Windows.exe` desde [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases).
2. Hacé doble clic en el instalador y seguí los pasos. Podés elegir crear un acceso directo en el escritorio.
3. Abrí **PDF Escolar** desde el menú Inicio o desde el acceso directo.

Las compilaciones de prueba no están firmadas digitalmente y Windows puede mostrar una advertencia de seguridad. La distribución pública requiere firma de código.

### macOS

1. Descargá `PDF-Escolar-Instalador-…-macOS.dmg` desde [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases).
2. Abrí el archivo descargado y arrastrá **PDF Escolar** a **Aplicaciones**.
3. Abrí PDF Escolar desde Aplicaciones.

Las compilaciones de prueba no están firmadas ni notarizadas por Apple, por lo que macOS puede mostrar una advertencia. Para una distribución pública fluida se necesita una cuenta Apple Developer y configurar la firma y notarización.

> Si todavía no hay una versión publicada en Releases, se puede consultar [GitHub Actions](https://github.com/JavierGrecco/PDF-Escolar/actions) para ver las compilaciones de prueba. Esos artefactos son para validar el programa, no instaladores finales firmados.

## Cómo se usa

1. **Agregá tus PDF.** Seleccioná uno o varios archivos con el botón o arrastralos a la ventana.
2. **Elegí las páginas.** En cada documento, pulsá **Elegir visualmente** para ver miniaturas y marcar páginas. Si solo necesitás unas pocas de un libro largo, usá **Desmarcar todas** y después marcá las páginas deseadas. También se pueden escribir rangos, por ejemplo `1-8, 12, 20-25`.
3. **Ordená los archivos.** Usá las flechas para cambiar qué libro aparece primero en el documento final.
4. **Creá el PDF.** Pulsá **Crear PDF final** y elegí dónde guardarlo. Al terminar, podés abrir la carpeta del resultado.

Los documentos se procesan en la computadora: no se suben a Internet. Los PDF originales permanecen intactos.

## Sobre archivos grandes

La aplicación procesa archivos locales y crea las miniaturas en grupos pequeños para evitar convertir un libro entero en imágenes de una sola vez. El tiempo de proceso depende del tamaño del libro, la cantidad de páginas seleccionadas y la computadora disponible. También necesitás espacio libre para guardar el documento final.

## Para desarrolladores (solo para colaborar con el proyecto)

Esta sección es únicamente para quienes quieran ejecutar o modificar el código fuente. **No es necesaria para instalar ni usar la aplicación empaquetada.**

Requiere Python 3.11, 3.12 o 3.13.

### Preparar el entorno

macOS:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    python -m pdf_escolar

Windows PowerShell:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    python -m pdf_escolar

### Comprobaciones

    python -m ruff check .
    python -m pytest -q

Las compilaciones de escritorio se generan en GitHub Actions para cada sistema operativo. Para publicar una versión descargable, el workflow se ejecuta con una etiqueta Git cuyo nombre empiece con `v`, por ejemplo `v0.1.0`.

## Calidad y distribución

- Interfaz de escritorio en español con selección visual por miniaturas.
- Motor PDF separado de la interfaz gráfica.
- Pruebas automáticas en Linux, Windows y macOS.
- Compilaciones separadas por sistema operativo; cada descarga incluye su runtime y dependencias.
- Las versiones de producción deben probarse con libros reales y en computadoras limpias.
- La distribución pública debe incluir firma de Windows y firma/notarización de macOS.
- El código propio está bajo licencia MIT. Las dependencias mantienen sus propias licencias y avisos.
