# PDF Escolar

Elegí páginas de uno o varios PDF y guardalas en un solo documento. La aplicación está en español y está pensada para usarse sin conocimientos técnicos.

## Descargar

Los instaladores están en la carpeta **[descargas](descargas/)** de este mismo repositorio. No hace falta descargar el código fuente ni instalar Python.

### Windows

- **[Descargar PDF-Escolar.exe](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar.exe)** — recomendado. Descargalo y hacé doble clic. No necesita instalación.
- **[Descargar el instalador de Windows](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-Instalador-Windows.exe)** — seguí los pasos del instalador para dejarlo en tu computadora.

### Mac

- **[Mac con procesador Intel](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-macOS-Intel.dmg)**
- **[Mac con chip Apple Silicon (M1, M2, M3, M4 o posterior)](https://github.com/JavierGrecco/PDF-Escolar/raw/refs/heads/main/descargas/PDF-Escolar-macOS-Apple-Silicon.dmg)**

En Mac, abrí el archivo descargado y arrastrá **PDF Escolar** a la carpeta **Aplicaciones**.

## Cómo usarlo

1. Abrí PDF Escolar y agregá los PDF que quieras usar.
2. Entrá en **Elegir visualmente** para marcar las páginas. También podés escribir números o rangos, por ejemplo: `1-8, 12, 20-25`.
3. Ordená los documentos con las flechas o arrastrá el control ↕ con el mouse o el touchpad.
4. Pulsá **Ordenar páginas…** para ver las miniaturas de las páginas elegidas de todos los PDF y mezclarlas en el orden que necesites. Podés arrastrarlas o usar **Subir** y **Bajar**.
5. Pulsá **Crear PDF final** y elegí dónde guardar el archivo nuevo. El resultado respeta el orden visual que confirmaste.

La última carpeta desde la que agregaste PDF se recuerda para la próxima vez que uses el selector de archivos.

Tus documentos se procesan en tu computadora. Los PDF originales no se modifican.

## Un aviso

Estas versiones todavía no están firmadas digitalmente. Windows o Mac pueden mostrar una advertencia de seguridad al abrirlas. Además, aunque los paquetes se compilan automáticamente, todavía falta validarlos manualmente en computadoras de uso habitual antes de considerarlos una versión de producción.

## Código fuente

Si querés revisar o modificar el proyecto, podés [ver los archivos del repositorio](https://github.com/JavierGrecco/PDF-Escolar). Para usar la aplicación, seguí solamente los pasos de descarga de arriba.

## Validar una versión

Antes de considerar una versión lista para distribuir, conviene completar la [lista de pruebas manuales](docs/PRUEBAS-MANUALES.md). Las pruebas automáticas ayudan a detectar errores, pero no reemplazan probar los instaladores en computadoras reales.
