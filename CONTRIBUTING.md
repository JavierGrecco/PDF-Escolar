# Contribuir a PDF Escolar

Gracias por ayudar a mejorar PDF Escolar. El objetivo del proyecto es que cualquier persona pueda combinar páginas de libros PDF de forma sencilla, local y confiable.

## Preparar el entorno

Usar Python 3.12 recomendado (se admiten Python 3.11 a 3.13).

    python -m venv .venv

En macOS:

    source .venv/bin/activate

En Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

Instalar el proyecto y herramientas de desarrollo:

    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

## Comprobaciones antes de enviar cambios

    python -m ruff check .
    python -m pytest -q

Los cambios que afecten al motor de PDF deben incluir pruebas con documentos generados durante los tests. No subir libros, documentos personales ni PDF de terceros al repositorio.

## Principios del proyecto

- Mantener el procesamiento en local; no introducir servicios remotos ni telemetría sin una decisión explícita del proyecto.
- No modificar nunca los PDF de origen.
- Evitar cargar todas las páginas como imágenes en memoria. Las miniaturas deben renderizarse bajo demanda y en lotes pequeños.
- Mantener la interfaz en español claro, con mensajes de error accionables.
- Ejecutar operaciones pesadas fuera del hilo principal de Qt.
- Verificar el PDF de salida antes de reemplazar o publicar un archivo final.
- Mantener el soporte de Windows y macOS y revisar los artefactos generados en ambos sistemas.

## Licencias

El código propio está bajo MIT. No copiar código de terceros sin comprobar su licencia y las obligaciones de distribución aplicables.
