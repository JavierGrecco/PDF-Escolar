# Instalación en macOS

El artefacto distribuido es una imagen de disco `.dmg` que contiene una aplicación `.app` autocontenida.

1. Abrí `PDF-Escolar-Instalador-…-macOS.dmg`.
2. Arrastrá **PDF Escolar** a **Applications / Aplicaciones**.
3. Expulsá la imagen de disco y abrí PDF Escolar desde Aplicaciones.

No es necesario instalar Python ni abrir Terminal.

## Firma y notarización

Los artefactos de CI de desarrollo no están firmados ni notarizados por Apple. macOS puede mostrar una advertencia de seguridad en el primer inicio. Para una distribución pública fluida, se deben configurar una identidad Apple Developer ID, firma de código y notarización; no se deben presentar estos artefactos sin firma como una versión final de producción.
