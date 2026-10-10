# PDF Escolar

**Elegí páginas de tus libros PDF y guardalas en un único documento.** Una aplicación de escritorio en español, diseñada para usarse sin conocimientos técnicos.

## Descargar y abrir

**No necesitás instalar Python, abrir una terminal ni escribir comandos.** Los paquetes incluyen el programa y sus dependencias.

Todavía no hay una versión estable publicada en *Releases*. Mientras tanto, podés descargar los paquetes de prueba generados automáticamente en [esta compilación de PDF Escolar](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38022280751). En la sección **Artifacts** al pie de la ejecución, elegí el paquete que corresponda a tu equipo. Estos paquetes de prueba caducan el **9 de noviembre de 2026**.

### Windows

Hay dos opciones:

**Opción recomendada para abrirlo directamente: PDF-Escolar.exe**

1. Descargá el artefacto `pdf-escolar-windows` y descomprimí el ZIP.
2. Hacé doble clic en `PDF-Escolar.exe`.
3. La aplicación se abre; no tenés que instalar nada.

El ejecutable portable es un único archivo que incluye Python y las bibliotecas necesarias. Al abrirlo, prepara automáticamente sus componentes temporales y arranca la interfaz.

**Opción alternativa: instalador de Windows**

Ejecutá `PDF-Escolar-Instalador-…-Windows.exe` y seguí el asistente en español. Esta opción crea una entrada en el menú Inicio y permite generar un acceso directo en el escritorio.

### macOS

Elegí el paquete según el procesador de tu Mac:

- **Mac Intel:** `PDF-Escolar-Instalador-…-macOS-Intel.dmg`.
- **Mac Apple Silicon (M1, M2, M3 o M4):** `PDF-Escolar-Instalador-…-macOS-Apple-Silicon.dmg`.

Abrí el archivo `.dmg`, arrastrá **PDF Escolar** a **Aplicaciones** y luego abrí la aplicación desde esa carpeta. No necesitás instalar Python ni abrir Terminal.

El paquete Intel se compila con dependencias orientadas a macOS Catalina 10.15, pero la compatibilidad final debe validarse en una Mac con Catalina real antes de declarar una versión de producción.

### Aviso de seguridad

Los paquetes de prueba actuales no están firmados digitalmente. Windows puede mostrar una advertencia de SmartScreen, y macOS puede advertir que la aplicación no está firmada ni notarizada. No se debe confundir la compilación correcta con una distribución pública firmada: para una publicación de producción se deben configurar los certificados de firma y, en macOS, la notarización de Apple.

## Cómo usar la aplicación

1. **Agregá los PDF.** Elegí uno o varios archivos con el botón o arrastralos a la ventana.
2. **Seleccioná las páginas.** Pulsá **Elegir visualmente** para ver las miniaturas y marcar las páginas que necesitás. En libros largos, podés usar **Desmarcar todas** y luego marcar solo las páginas elegidas. También podés escribir rangos como `1-8, 12, 20-25`.
3. **Ordená los documentos.** Usá las flechas para definir qué libro aparece primero en el PDF final.
4. **Creá el archivo final.** Pulsá **Crear PDF final**, elegí dónde guardarlo y abrí la carpeta de destino al terminar.

## Privacidad e integridad

Los documentos se procesan en tu computadora y no se suben a Internet. PDF Escolar no modifica los archivos originales: crea un documento nuevo y comprueba el resultado antes de guardarlo.

## Entorno de desarrollo (opcional)

Esta sección es para quien quiera mantener o modificar el código fuente. No hace falta leerla para instalar ni usar PDF Escolar.

Consultá la guía de [preparación del entorno de desarrollo](docs/ENTORNO-DE-DESARROLLO.md).

## Proyecto

- [Código fuente y versiones](https://github.com/JavierGrecco/PDF-Escolar)
- [Compilaciones y pruebas automatizadas](https://github.com/JavierGrecco/PDF-Escolar/actions)
- [Versiones publicadas](https://github.com/JavierGrecco/PDF-Escolar/releases)
- [Licencia MIT](LICENSE)
