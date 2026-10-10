# Preparación del entorno de desarrollo

**Esta guía es solo para mantenimiento del código fuente. No es necesaria para instalar ni usar PDF Escolar.** Para personas usuarias, consultá el [README principal](../README.md).

## Requisitos

- Python 3.11, 3.12 o 3.13.
- Git para obtener el código fuente.
- Windows o macOS para ejecutar la interfaz de escritorio; las pruebas también se ejecutan en Linux.

## Preparar el entorno

En una terminal, dentro de la carpeta del proyecto, creá un entorno virtual.

macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Para iniciar la aplicación desde el código fuente:

```bash
python -m pdf_escolar
```

## Comprobaciones antes de integrar cambios

```bash
python -m ruff check .
python -m pytest -q
```

Las pruebas deben crear sus propios PDF temporales. No subas libros, documentos personales ni PDF de terceros al repositorio.

## Principios del proyecto

- Mantener todo el procesamiento de PDF en local; no agregar servicios remotos ni telemetría sin una decisión explícita.
- No modificar los PDF de origen.
- Evitar cargar un libro entero como imágenes en memoria; las miniaturas deben renderizarse por lotes.
- Mantener la interfaz en español claro, con mensajes de error accionables.
- Ejecutar operaciones pesadas fuera del hilo principal de Qt.
- Verificar el PDF final antes de reemplazar o publicar el archivo generado.
- Ejecutar las pruebas en los sistemas compatibles y revisar las compilaciones descargables.

## Licencias

El código propio está bajo MIT. Antes de distribuir un ejecutable, revisá las licencias y avisos de las dependencias incluidas.


## Componente OCR opcional

El OCR no forma parte de las dependencias instaladas en el entorno principal. `ocrmypdf`, Tesseract y los modelos de idioma se construyen como un complemento separado para evitar acoplar el conjunto de dependencias de la app a un motor nativo más pesado.

- Las dependencias de construcción específicas están fijadas en [`packaging/ocr/requirements.txt`](../packaging/ocr/requirements.txt).
- El flujo [Build OCR companion](../.github/workflows/build-ocr.yml) construye y prueba el ejecutable para Windows x64 y macOS Apple Silicon. Es preferible usar ese flujo reproducible para crear paquetes distribuidos, en vez de copiar una instalación local de Tesseract.
- La prueba de extremo a extremo [`packaging/ocr/smoke_test.py`](../packaging/ocr/smoke_test.py) requiere el ejecutable ya empaquetado; crea un escaneo sintético, ejecuta el OCR y verifica que se pueda extraer el texto esperado.
- No hace falta descargar el complemento OCR para desarrollar o probar las demás herramientas PDF. Las pruebas de `ocr_companion` usan instalaciones simuladas y no descargan versiones reales.
- La matriz OCR no incluye Mac Intel. La aplicación principal conserva su conjunto de dependencias específico para esos equipos y debe seguir superando las pruebas de CI correspondientes.
