# Publicar una versión descargable

**Esta guía es solo para quien mantiene el repositorio.** Quien utiliza PDF Escolar no debe seguir estos pasos: descarga la versión publicada desde [Releases](https://github.com/JavierGrecco/PDF-Escolar/releases).

## Compilar paquetes de prueba sin publicar

1. Abrí el flujo [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml).
2. Pulsá **Run workflow** y elegí la rama `main`.
3. Dejá vacío el campo **Versión para publicar** y dejá desmarcada **Actualizar también los binarios de descargas/**.
4. Pulsá **Run workflow**.

El flujo compila los paquetes de Windows, macOS Intel y macOS Apple Silicon y comprueba su integridad. Los paquetes quedan como artefactos temporales de la ejecución; **no crea una Release ni modifica `descargas/`**. Esta es la opción correcta para validar cambios sin publicar.

## Publicar una nueva versión descargable

1. Abrí [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml), pulsá **Run workflow** y elegí `main`.
2. En **Versión para publicar**, escribí una versión nueva sin la letra `v`, por ejemplo `0.1.0-beta.2`.
3. Dejá desmarcada **Actualizar también los binarios de descargas/**, salvo que también necesites reemplazar los enlaces directos antiguos.
4. Pulsá **Run workflow** y revisá los resultados.

Antes de publicar, el flujo exige los cuatro paquetes de la versión elegida (portable Windows, instalador Windows, DMG Intel y DMG Apple Silicon), rechaza archivos ausentes, vacíos o de versiones mezcladas, y genera `SHA256SUMS.txt` con los hashes SHA-256, la versión, el commit de origen y el enlace a la compilación. Ese manifiesto se adjunta a la nueva Release.

El flujo **no sobrescribe una Release existente**. Si el tag ya está publicado, elegí una versión nueva en lugar de intentar reemplazar sus assets. Si el tag existe sin Release, solo se acepta cuando apunta al mismo commit que se está compilando.

Antes de anunciar la versión, revisá los assets y los hashes, y actualizá los cuatro enlaces del README si deben apuntar a la nueva Release. Los enlaces públicos del README están fijados a `v0.1.0-beta.1` para no cambiar de archivo por accidente; una Release nueva no los actualiza por sí sola.

## Evidencia independiente para revisar licencias

Cada compilación de prueba y cada publicación generada por **Build installers** adjunta tres artefactos de auditoría independientes en la misma ejecución de GitHub Actions:

- **license-audit-windows:** avisos de terceros y metadatos del paquete Windows x64.
- **license-audit-macos-Intel:** avisos y metadatos de la compilación Intel.
- **license-audit-macos-Apple-Silicon:** avisos y metadatos de la compilación Apple Silicon.

El archivo LICENSE-AUDIT-METADATA.txt identifica la versión, plataforma, arquitectura, commit y ejecución; además registra el tamaño y SHA-256 del archivo THIRD-PARTY-NOTICES.txt y de cada paquete generado por esa plataforma. Los hashes pueden comprobarse con herramientas estándar y permiten detectar si un archivo se mezcló con uno de otra compilación.

Los artefactos de Actions se conservan durante 90 días. Para una revisión posterior, descargalos y guardalos junto con la versión exacta antes de que venzan. Se suben con nombres separados de los paquetes pdf-escolar-* para que no interfieran con la verificación de instaladores ni con el manifiesto SHA256SUMS.txt.

**Importante:** el inventario automático y estos hashes son evidencia técnica, no una conclusión legal. Antes de declarar una versión estable, todavía hay que comparar las licencias y avisos con los componentes nativos realmente redistribuidos (incluidos Qt y PDFium), revisar las obligaciones aplicables y documentar el resultado de esa revisión.

## Actualizar los enlaces directos antiguos

La opción de sincronización existe únicamente para conservar la compatibilidad con enlaces raw que terceros pudieran tener guardados. Para actualizar esos binarios, ejecutá el flujo manualmente con una versión nueva en **Versión para publicar** y marcá explícitamente **Actualizar también los binarios de descargas/**. La sincronización espera a que la nueva Release se haya publicado correctamente; si la validación o publicación falla, no reemplaza `descargas/`.

Esta acción guarda varios binarios grandes en el historial de Git, así que usala solo si hace falta. Los enlaces principales del README apuntan a assets versionados de Releases, por lo que el uso normal no requiere sincronizar `descargas/`.

## Verificar los hashes descargados

En una nueva Release, descargá `SHA256SUMS.txt` y los instaladores a la misma carpeta. En Linux o macOS, ejecutá:

```bash
sha256sum --check SHA256SUMS.txt
```

Cada archivo debería mostrar `OK`. En Windows, compará la salida de `Get-FileHash .\PDF-Escolar.exe -Algorithm SHA256` (y el comando equivalente para el instalador) con la línea del nombre correspondiente en `SHA256SUMS.txt`.

La versión `v0.1.0-beta.1` no contiene ese asset nuevo. Sus cuatro hashes están en `descargas/INFORMACION-DE-DESCARGA.txt` y se verificaron contra los cuatro assets de esa Release.

## Primera beta coordinada: publicada el 10 de octubre de 2026

La beta inicial está publicada en dos releases y los enlaces directos se sincronizaron:

- [Aplicación PDF Escolar v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/v0.1.0-beta.1): portable Windows, instalador Windows, DMG Mac Intel y DMG Apple Silicon.
- [Complemento OCR v0.1.0-beta.1](https://github.com/JavierGrecco/PDF-Escolar/releases/tag/ocr-engine-v0.1.0-beta.1): ZIP Windows x64 y ZIP Mac Apple Silicon.

La primera publicación se activó históricamente con los marcadores `[publish-app-beta]` y `[publish-ocr-beta]` en los títulos de los commits. **Ese atajo se retiró** porque fijaba la versión antigua `0.1.0-beta.1`; no debe usarse para futuras publicaciones. La build de la aplicación [#38087055313](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38087055313) y la build del complemento [#38087055391](https://github.com/JavierGrecco/PDF-Escolar/actions/runs/38087055391) terminaron correctamente. El manifiesto `descargas/INFORMACION-DE-DESCARGA.txt` apunta a `0.1.0-beta.1` y contiene SHA-256 coincidentes con los activos de esa Release.

Para futuras versiones, publicá la aplicación desde **Build installers** usando **Run workflow** y una versión nueva en `release_version`. Publicá el complemento con **Build OCR companion** (`release_version`) por separado. Usá el mismo número de versión para una pareja coordinada, pero no confundas los tags: `vX.Y.Z` es la aplicación y `ocr-engine-vX.Y.Z` es el motor. No reutilices los tags de la beta inicial: las Releases existentes no se pueden sobrescribir.

## ¿Qué versión conviene publicar?

- **Vista previa de prueba:** usá una versión con guion que todavía no exista, por ejemplo `0.1.0-beta.2`. GitHub la marcará como *pre-release*. No vuelvas a usar `0.1.0-beta.1`, porque esa Release ya está publicada. Es lo recomendado mientras la aplicación no tenga firma digital y pruebas manuales en equipos limpios.
- **Versión estable:** usá una versión como `0.1.0` solo después de hacer pruebas manuales en los sistemas que se anuncian como compatibles y resolver la firma/notarización si se distribuirá públicamente.

## ¿Cuánto duran los archivos?

Los paquetes bajo **Artifacts** son compilaciones temporales y, en este repositorio público, se configuran para conservarse 90 días como máximo. Los instaladores adjuntos a una publicación en **Releases** no tienen esa caducidad automática; siguen disponibles mientras no se eliminen la publicación o sus archivos y el repositorio siga disponible.

**Sobre el tamaño del historial:** los binarios que ya se guardaron en commits anteriores siguen formando parte del historial de Git. Esta política evita volver a guardarlos por cada cambio de código, pero no borra lo acumulado. Eliminar blobs antiguos requiere reescribir el historial y coordinar una actualización forzada de las ramas; es una tarea de mantenimiento separada y no se hace automáticamente.

## Descargas de la publicación

- `PDF-Escolar.exe`: aplicación portable para Windows, sin instalación.
- `PDF-Escolar-Instalador-…-Windows.exe`: instalador tradicional para Windows.
- `PDF-Escolar-Instalador-…-macOS-Intel.dmg`: Mac con procesador Intel.
- `PDF-Escolar-Instalador-…-macOS-Apple-Silicon.dmg`: Mac con Apple Silicon (M1, M2, M3, M4 o posterior).
