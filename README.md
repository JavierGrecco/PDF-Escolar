# PDF Escolar

Aplicación de escritorio local para elegir páginas de uno o varios PDF y reunirlas en un solo documento. Está pensada para personas que prefieren una interfaz clara y guiada, en español.

## Funciones del prototipo

- Seleccionar varios PDF mediante el explorador o arrastrarlos a la ventana.
- Consultar la cantidad de páginas y el tamaño de cada archivo.
- Elegir páginas por rangos, por ejemplo: 1-8, 12, 20-25.
- Mantener el orden de los archivos y el orden de los rangos ingresados.
- Crear un PDF nuevo y elegir su nombre y ubicación.
- Procesar archivos en segundo plano para mantener la interfaz receptiva.
- No modificar los originales ni subir documentos a Internet.

La selección visual por miniaturas y el reordenamiento manual quedan para una siguiente versión.

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

## Ejecutables de prueba

GitHub Actions puede construir un ejecutable para Windows y una aplicación .app para macOS. Los artefactos no están firmados ni notarizados y no deben considerarse instaladores definitivos. Cada paquete se construye en el sistema operativo de destino.

## Selección de páginas

Los números empiezan en 1:
- 1-8: páginas 1 a 8.
- 3, 7, 12: páginas individuales.
- 1-5, 10-15: varios rangos.
- 20-: desde la página 20 hasta el final.
- -6: desde el inicio hasta la página 6.

## Privacidad y PDF grandes

Los documentos se procesan localmente. El motor abre los archivos de origen de a uno, escribe la salida a un archivo temporal y valida el PDF antes de moverlo a su ubicación final. El espacio disponible en disco y los recursos de la computadora siguen siendo límites prácticos.

## Licencias

El código propio utiliza MIT (ver LICENSE). Las dependencias conservan sus propias licencias y avisos; deben revisarse antes de distribuir aplicaciones empaquetadas.

## Próximos pasos

1. Probar con libros grandes, PDF protegidos y documentos dañados.
2. Añadir miniaturas para elegir páginas visualmente.
3. Añadir reordenamiento de páginas y vista previa final.
4. Probar instaladores en equipos limpios.
5. Configurar firma de código y notarización para distribución pública.
