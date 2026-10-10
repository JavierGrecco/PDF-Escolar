# Instalación en macOS

Se generan dos imágenes de disco: Intel (`…-macOS-Intel.dmg`) y Apple Silicon (`…-macOS-Apple-Silicon.dmg`). Descargá la correspondiente al procesador de la computadora.

1. Abrí el archivo `.dmg`.
2. Arrastrá **PDF Escolar** a **Applications / Aplicaciones**.
3. Expulsá la imagen de disco y abrí PDF Escolar desde Aplicaciones.

No es necesario instalar Python ni abrir Terminal.

## Compatibilidad

El build para Intel fija PySide6/Qt 6.4.3 para apuntar a macOS Catalina 10.15. El build Apple Silicon se compila en un runner ARM nativo. La compatibilidad final depende también de las bibliotecas empaquetadas y debe comprobarse en computadoras limpias; Catalina debe incluirse en la prueba de aceptación.

## Firma y notarización

Los artefactos generados por CI no están firmados ni notarizados por Apple. macOS puede mostrar una advertencia de seguridad en el primer inicio. Para una distribución pública fluida se deben configurar una identidad Apple Developer ID, firma de código y notarización. No se deben presentar estos artefactos sin firma como una versión final de producción.
