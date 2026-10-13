# Auditoría del tamaño del historial Git

La herramienta [tools/analyze_git_history_size.py](../tools/analyze_git_history_size.py) genera un inventario **de solo lectura** para preparar una posible reducción del historial. No borra archivos, no mueve referencias y no reescribe commits.

## Qué mide

- Los objetos únicos alcanzables desde las referencias locales (opción `--all`) y el tamaño lógico total de los blobs. El contenido idéntico comparte el mismo SHA de Git y se cuenta una sola vez, aunque haya aparecido en varias rutas o commits.
- Los blobs que superan el umbral elegido, con SHA, tamaño y una ruta representativa. La ruta no es una lista completa de todas las apariciones históricas.
- Los archivos actualmente presentes en `descargas/` en `HEAD`, por separado, para distinguir el peso actual de los archivos conservados en el historial.
- La información de almacenamiento local devuelta por `git count-objects -vH`, que ayuda a comparar tamaño lógico con almacenamiento comprimido.

El tamaño lógico de los blobs **no equivale** al tamaño del directorio `.git` ni al campo `size` de la API de GitHub. El tamaño local de los packs depende de compresión, deltas y de qué objetos se hayan descargado. El inventario también puede ser incompleto si faltan referencias en el clon o si este es superficial.

## Ejecutar un inventario completo

El repositorio incluye el flujo manual **Audit Git history**, que hace un checkout completo y guarda el informe legible y el JSON como artefactos de GitHub Actions. Después de integrar esta herramienta, podés ejecutarlo desde la pestaña **Actions → Audit Git history → Run workflow**. El flujo es de solo lectura y no modifica referencias ni archivos versionados.

También podés ejecutarlo localmente en un clon espejo nuevo, que obtenga las ramas y etiquetas anunciadas por el remoto. Así no mezclamos el resultado con un clon de desarrollo que quizá solo tenga `main`.

### macOS o Linux

    git clone --mirror https://github.com/JavierGrecco/PDF-Escolar.git PDF-Escolar-auditoria.git
    git --git-dir=PDF-Escolar-auditoria.git show refs/heads/main:tools/analyze_git_history_size.py > analyze_git_history_size.py
    python3 analyze_git_history_size.py --repo PDF-Escolar-auditoria.git --min-size-mib 10 --top 50 --json informe-historial.json

### Windows PowerShell

    git clone --mirror https://github.com/JavierGrecco/PDF-Escolar.git PDF-Escolar-auditoria.git
    git --git-dir=PDF-Escolar-auditoria.git show refs/heads/main:tools/analyze_git_history_size.py > analyze_git_history_size.py
    py -3 .\analyze_git_history_size.py --repo .\PDF-Escolar-auditoria.git --min-size-mib 10 --top 50 --json .\informe-historial.json

La herramienta solo requiere Git y la biblioteca estándar de Python. El informe JSON se guarda en la ruta indicada, fuera del repositorio espejo en los ejemplos anteriores. Se puede ajustar el umbral y la cantidad de líneas visibles; el JSON conserva todos los blobs que superen el umbral elegido.

## Cómo interpretar el resultado

1. Revisar los blobs mayores y comprobar si son distintas versiones históricas de binarios, paquetes de prueba, artefactos temporales o archivos que deban conservarse.
2. Comparar `large_blob_bytes` con `current_descargas_total_bytes` sin sumarlos como si fueran magnitudes equivalentes: la primera cifra cuenta versiones de contenido únicas alcanzables en toda la historia; la segunda solo el árbol actual bajo `descargas/`.
3. Usar `git_count_objects` como una medida complementaria del almacenamiento local del clon.
4. Antes de limpiar, guardar una copia espejo verificable, ensayar `git filter-repo --analyze` y cualquier reescritura en una copia aislada, comparar ramas y etiquetas, y revisar cómo conservar las URLs raw de `main/descargas/`.

Este informe es diagnóstico, no una autorización para reescribir la historia. No se debe hacer un push forzado ni pedir a otras personas que reclonen hasta acordar el impacto y el plan de recuperación.
