# Publicar una versión descargable

**Esta guía es solo para quien mantiene el repositorio.** Quien utiliza PDF Escolar no debe seguir estos pasos: descarga la versión publicada desde [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases).

## Actualizar los archivos de descarga sin publicar una versión

1. Abrí el flujo [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml).
2. Pulsá **Run workflow** y elegí la rama `main`.
3. Dejá vacío el campo **Versión para publicar**.
4. Por defecto, dejá desmarcada la opción **Actualizar también los binarios de descargas/**. Activala solo si querés reemplazar los archivos directos del repositorio.
5. Pulsá **Run workflow**.

El flujo compila los paquetes de Windows, macOS Intel y macOS Apple Silicon. Las pruebas comprueban la instalación, apertura y desinstalación en Windows, y la integridad y el contenido del DMG en macOS. Si no activás la opción de sincronización, los paquetes quedan como artefactos temporales de la ejecución y **no se modifica `descargas/` ni se crea una publicación en Releases**. Esto evita guardar repetidamente binarios grandes en el historial de Git.

## Publicar una versión descargable

1. Abrí el flujo [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml).
2. Pulsá **Run workflow** y elegí la rama `main`.
3. En **Versión para publicar**, escribí la versión sin la letra `v`. Por ejemplo, `0.1.0-beta.1`.
4. Pulsá **Run workflow**.

El flujo compila y verifica los paquetes, los adjunta a una publicación `v...` en **Releases** y actualiza los archivos directos de la carpeta `descargas/`. Esta actualización de los binarios queda vinculada a una publicación intencional, no a cada cambio de código. No hace falta abrir una terminal ni escribir comandos.

**Importante:** los paquetes generados al probar cambios en una rama o en un pull request no actualizan `descargas/` ni se publican en Releases. Hasta ejecutar manualmente uno de los dos pasos anteriores, los enlaces directos siguen apuntando a los últimos archivos guardados en esa carpeta.

Para refrescar los enlaces directos sin publicar una versión, ejecutá el flujo manualmente y activá **Actualizar también los binarios de descargas/**. Es una acción deliberada: los binarios nuevos se guardan en Git y aumentan el historial, por lo que conviene reservarla para una compilación que realmente quieras distribuir. Los cambios de código y las compilaciones automáticas no reemplazan por sí solos esos archivos.

## Publicación inicial coordinada de la beta OCR

La primera integración de OCR publica dos artefactos relacionados: la aplicación beta `v0.1.0-beta.1` (que contiene el botón OCR) y el complemento `ocr-engine-v0.1.0-beta.1` (el motor opcional). El flujo de OCR no sustituye la publicación de la aplicación: si solo se publica el motor, la versión de PDF Escolar ya instalada no obtiene la interfaz nueva.

La primera publicación se activa de forma deliberada al integrar el PR de OCR con los marcadores `[publish-app-beta]` y `[publish-ocr-beta]` en el título del commit de integración. El workflow construye y comprueba todos los paquetes antes de publicarlos como versiones beta y sincroniza los enlaces directos de `descargas/`. Si el build o el smoke test falla, no se publica una versión estable ni debe anunciarse la beta como disponible.

Para versiones posteriores, publicá la aplicación con **Build installers** (`release_version`) y el complemento con **Build OCR companion** (`release_version`) por separado. No uses una etiqueta de la aplicación como si fuera la etiqueta del motor OCR.

## ¿Qué versión conviene publicar?

- **Vista previa de prueba:** usá una versión con guion, por ejemplo `0.1.0-beta.1`. GitHub la marcará como *pre-release*. Es lo recomendado mientras la aplicación no tenga firma digital y pruebas manuales en equipos limpios.
- **Versión estable:** usá una versión como `0.1.0` solo después de hacer pruebas manuales en los sistemas que se anuncian como compatibles y resolver la firma/notarización si se distribuirá públicamente.

## ¿Cuánto duran los archivos?

Los paquetes bajo **Artifacts** son compilaciones temporales y, en este repositorio público, se configuran para conservarse 90 días como máximo. Los instaladores adjuntos a una publicación en **Releases** no tienen esa caducidad automática; siguen disponibles mientras no se eliminen la publicación o sus archivos y el repositorio siga disponible.

**Sobre el tamaño del historial:** los binarios que ya se guardaron en commits anteriores siguen formando parte del historial de Git. Esta política evita volver a guardarlos por cada cambio de código, pero no borra lo acumulado. Eliminar blobs antiguos requiere reescribir el historial y coordinar una actualización forzada de las ramas; es una tarea de mantenimiento separada y no se hace automáticamente.

## Descargas de la publicación

- `PDF-Escolar.exe`: aplicación portable para Windows, sin instalación.
- `PDF-Escolar-Instalador-…-Windows.exe`: instalador tradicional para Windows.
- `PDF-Escolar-Instalador-…-macOS-Intel.dmg`: Mac con procesador Intel.
- `PDF-Escolar-Instalador-…-macOS-Apple-Silicon.dmg`: Mac con Apple Silicon (M1, M2, M3, M4 o posterior).
