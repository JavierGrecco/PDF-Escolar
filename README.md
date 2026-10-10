# PDF Escolar

**Elegí páginas de tus libros PDF y guardalas en un único documento.** Aplicación de escritorio en español, para usar sin conocimientos técnicos.

## Descargar y abrir

**No descargues el código fuente ni necesitás descargar todo el repositorio.** Para usar PDF Escolar, descargá el paquete de tu sistema operativo siguiendo las instrucciones de abajo.

### Descarga estable

Las versiones permanentes se publican en **[Versiones y descargas (Releases)](https://github.com/JavierGrecco/PDF-Escolar/releases)**. Los archivos adjuntos a una versión no caducan automáticamente como los artefactos de prueba de GitHub Actions.

**Todavía no hay una versión estable publicada en Releases.** Hasta que se publique la primera, podés usar una compilación de prueba. Los artefactos públicos de GitHub Actions tienen un límite de conservación de 90 días; no son el lugar adecuado para distribuir una versión permanente.

### Compilación de prueba (temporal)

1. Abrí [Compilaciones de PDF Escolar](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml).
2. Entrá en la ejecución más reciente que haya terminado correctamente (ícono verde).
3. Bajá hasta **Artifacts** al final de esa página.
4. Descargá el paquete que corresponda a tu sistema. GitHub te entregará un archivo ZIP; primero tenés que descomprimir ese ZIP.

Los ejecutables **no aparecen como archivos en la carpeta principal del repositorio**: el sistema de compilación los genera automáticamente y los adjunta a cada ejecución. Esto es normal. No hace falta descargar el ZIP del código fuente desde el botón verde **Code**.

#### Windows

En la carpeta que aparece después de descomprimir el artefacto `pdf-escolar-windows`, vas a encontrar:

- **`PDF-Escolar.exe` — recomendado si querés abrirlo sin instalar:** hacé doble clic. No necesitás Python ni instalar nada.
- **`PDF-Escolar-Instalador-…-Windows.exe` — instalación clásica:** hacé doble clic y seguí el asistente en español. Agrega una entrada al menú Inicio y permite crear un acceso directo en el escritorio.

El ejecutable portable contiene el programa y sus dependencias. La primera apertura puede demorar un poco mientras prepara los componentes temporales.

#### macOS

En **Artifacts**, descargá el paquete `pdf-escolar-macos-Intel` si tu Mac tiene procesador Intel, o `pdf-escolar-macos-Apple-Silicon` si tiene un chip M1, M2, M3, M4 o posterior. Descomprimí el ZIP descargado y abrí el archivo `.dmg` que contiene.

1. Abrí el archivo `.dmg`.
2. Arrastrá **PDF Escolar** a **Aplicaciones**.
3. Abrí PDF Escolar desde la carpeta **Aplicaciones**.

No necesitás instalar Python ni usar Terminal. La compilación para Intel usa dependencias orientadas a macOS Catalina 10.15, pero esa compatibilidad todavía debe probarse en una Mac real con Catalina antes de prometer soporte de producción.

### Aviso de seguridad de estas compilaciones

Las compilaciones de prueba actuales no están firmadas digitalmente. Windows puede mostrar una advertencia de SmartScreen y macOS puede advertir que la aplicación no está firmada ni notarizada. La compilación automática y las pruebas de CI no sustituyen una prueba manual en equipos limpios; para una publicación de producción, también corresponde configurar la firma y, en macOS, la notarización de Apple.

## Cómo usar PDF Escolar

1. **Agregá los PDF.** Elegí uno o varios archivos con el botón correspondiente o arrastralos a la ventana.
2. **Seleccioná las páginas.** Pulsá **Elegir visualmente** para ver miniaturas y marcar las páginas que necesitás. En libros largos, podés usar **Desmarcar todas** y marcar solo las elegidas. También podés escribir rangos, por ejemplo `1-8, 12, 20-25`.
3. **Ordená los documentos.** Usá las flechas para indicar qué libro aparece primero en el documento final.
4. **Creá el resultado.** Pulsá **Crear PDF final**, elegí dónde guardarlo y abrí la carpeta de destino al terminar.

## Privacidad e integridad

Los documentos se procesan en tu computadora y no se suben a Internet. PDF Escolar no modifica los archivos originales: crea un documento nuevo y comprueba el resultado antes de guardarlo.

## Para desarrolladores (opcional)

Esta sección es solo para mantener o modificar el código fuente. No hace falta seguirla para instalar ni utilizar la aplicación.

Consultá la [guía de preparación del entorno de desarrollo](docs/ENTORNO-DE-DESARROLLO.md).

## Proyecto

- [Código fuente](https://github.com/JavierGrecco/PDF-Escolar)
- [Compilaciones y pruebas automatizadas](https://github.com/JavierGrecco/PDF-Escolar/actions)
- [Versiones publicadas y descargas estables](https://github.com/JavierGrecco/PDF-Escolar/releases)
- [Licencia MIT](LICENSE)
