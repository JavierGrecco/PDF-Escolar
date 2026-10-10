# PDF Escolar

Aplicación de escritorio local para seleccionar páginas de uno o varios PDF y reunirlas en un único documento. Interfaz en español pensada para usuarios no técnicos.

## Funciones disponibles en esta rama

- Carga de varios archivos PDF mediante selector o arrastrar y soltar.
- Muestra páginas totales y tamaño de cada archivo.
- Selección por rangos (por ejemplo, `1-8, 12, 20-25`).
- **Selección visual por miniaturas**, en grupos de hasta 30 páginas, sin renderizar todos los libros a la vez.
- Navegación por grupos, marcado/desmarcado del grupo y contador de páginas elegidas.
- Guardado del resultado con nombre y ubicación elegidos por el usuario.
- Verificación del PDF resultante antes de moverlo al destino final.
- Procesamiento en segundo plano, para mantener la ventana interactiva.
- Trabajo local: los PDF no se suben a ningún servicio.

La selección y combinación respetan el orden de los archivos en la lista, y dentro de cada archivo el orden de las páginas elegidas. El reordenamiento manual de páginas entre archivos queda para una siguiente iteración.

## Ejecutar en modo desarrollo

Requiere Python 3.11, 3.12 o 3.13.

### macOS

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    python -m pdf_escolar

### Windows PowerShell

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"
    python -m pdf_escolar

## Pruebas

    python -m pytest -q

GitHub Actions ejecuta las pruebas en Linux, Windows y macOS. El workflow de empaquetado genera artefactos de prueba por sistema operativo. Esos artefactos no están firmados ni notarizados y todavía no son instaladores de producción.

## Selección de páginas

Los números empiezan en 1:
- `1-8`: páginas 1 a 8.
- `3, 7, 12`: páginas individuales.
- `1-5, 10-15`: varios rangos.
- `20-`: desde la página 20 hasta el final.
- `-6`: desde el inicio hasta la página 6.

La vista por miniaturas carga solo el grupo actual. Esto controla el uso de memoria con documentos grandes; los recursos de la computadora y el espacio libre en disco siguen siendo límites prácticos.

## Privacidad y seguridad de archivos

Los PDF se leen y procesan localmente. La salida se crea en un archivo temporal de la carpeta de destino, se abre de nuevo para verificar su cantidad de páginas y solo entonces se mueve al nombre final. El programa impide que el destino sea el mismo archivo que cualquiera de los originales.

## Licencias

El código propio está bajo MIT (ver `LICENSE`). Las dependencias conservan sus propias licencias y avisos; deben revisarse antes de distribuir ejecutables.

## Próximos pasos

1. Revisar los resultados de CI y probar los artefactos en equipos limpios.
2. Añadir reordenamiento explícito de archivos y páginas.
3. Añadir vista previa del documento final.
4. Preparar instaladores firmados de Windows y macOS.
