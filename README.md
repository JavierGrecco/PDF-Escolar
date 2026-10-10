# PDF Escolar

Aplicación de escritorio local para seleccionar páginas de uno o varios PDF y reunirlas en un único documento. Interfaz en español pensada para personas que no quieren lidiar con herramientas técnicas.

## Funciones disponibles en esta rama

- Carga de varios archivos PDF con el explorador o arrastrándolos a la ventana.
- Cantidad de páginas y tamaño de cada archivo.
- Selección de páginas por rangos, por ejemplo `1-8, 12, 20-25`.
- Selección visual por miniaturas; se renderizan solo 30 páginas por grupo para controlar memoria y tiempo de carga.
- Contador de páginas seleccionadas y controles para marcar/desmarcar el grupo visible.
- Reordenamiento de los PDF de origen mediante flechas; el orden se refleja en el documento final.
- Guardado del PDF final con nombre y ubicación elegidos por la persona usuaria.
- Proceso de exportación en segundo plano y verificación de la salida antes de publicarla.
- Procesamiento local: los PDF no se suben a Internet.

Dentro de cada archivo, las páginas seleccionadas visualmente se exportan por número ascendente. En modo de rangos, se conserva el orden en que se ingresan los rangos. El reordenamiento manual página por página entre diferentes libros se puede ampliar en una versión posterior.

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

## Pruebas y compilación

    python -m pytest -q

GitHub Actions ejecuta pruebas en Linux, Windows y macOS y crea artefactos de prueba independientes. Los artefactos no están firmados ni notarizados y todavía no son instaladores de producción.

## Rangos de páginas

Los números empiezan en 1:
- `1-8`: páginas 1 a 8.
- `3, 7, 12`: páginas individuales.
- `1-5, 10-15`: varios rangos.
- `20-`: desde la página 20 hasta el final.
- `-6`: desde el inicio hasta la página 6.

## Privacidad e integridad

Los documentos se procesan en la computadora. El archivo de salida se crea primero en un temporal de la carpeta de destino, se vuelve a abrir para comprobar la cantidad de páginas y solo entonces se mueve al nombre definitivo. La app impide seleccionar un archivo original como destino para evitar reemplazarlo por accidente.

El procesamiento local no elimina las limitaciones de memoria, CPU o espacio disponible en disco, pero la generación de miniaturas está paginada y no convierte el libro completo en imágenes.

## Licencias

El código propio está bajo MIT (ver `LICENSE`). Las dependencias mantienen sus licencias y avisos respectivos; deben revisarse antes de distribuir ejecutables.

## Próximos pasos

1. Revisar todos los resultados de CI y probar los artefactos en equipos limpios.
2. Añadir una vista de revisión del documento final.
3. Añadir reordenamiento página por página.
4. Preparar instaladores de Windows y macOS con firma y notarización para distribución externa.
