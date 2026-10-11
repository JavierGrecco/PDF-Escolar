# Prueba de uso de PDF Escolar desde la rama principal

Esta guía sirve para probar las mejoras recientes de la interfaz antes de que se incorporen a una beta pública. Los paquetes generados desde \`main\` son **compilaciones de prueba**, no una publicación estable ni la versión oficial \`0.1.0-beta.1\`.

## Opción recomendada: descargar la aplicación ya compilada

No necesitás instalar Python ni herramientas de desarrollo.

1. Abrí el flujo [Build installers](https://github.com/JavierGrecco/PDF-Escolar/actions/workflows/build.yml).
2. Buscá la ejecución más reciente de la rama **main** cuyo estado sea **Success**. Confirmá que sea una ejecución de \`push\` a \`main\`, no un intento de una rama o pull request.
3. En la parte inferior de esa ejecución, abrí **Artifacts** y descargá el paquete correspondiente a tu computadora:
   - **Windows:** \`pdf-escolar-windows\`.
   - **Mac con procesador Intel:** \`pdf-escolar-macos-Intel\`.
   - **Mac con chip Apple Silicon (M1, M2, M3, M4 o posterior):** \`pdf-escolar-macos-Apple-Silicon\`.
4. Descomprimí el ZIP del artefacto descargado.
   - En Windows, probá primero \`PDF-Escolar.exe\` (portable), o ejecutá el instalador cuyo nombre termina en \`Windows.exe\`.
   - En macOS, abrí el archivo \`.dmg\` y arrastrá PDF Escolar a **Aplicaciones**.
5. Conservá el nombre o enlace de la ejecución utilizada: así podremos identificar el commit y la compilación que probaste.

Los artefactos de Actions son temporales y vencen después de 90 días. Si no aparece uno de los tres paquetes, o la ejecución más reciente no terminó correctamente, no uses un paquete parcial: probá una ejecución completa y exitosa de \`main\`.

**Aviso de seguridad para macOS:** los paquetes actuales no están firmados ni notarizados por Apple y el sistema puede mostrar advertencias. No desactives las protecciones del equipo. Si no te sentís cómoda con esa advertencia, no abras el paquete y avisá para buscar otra forma de prueba.

Los paquetes creados desde \`main\` no cambian por sí mismos la Release pública ni los archivos de descarga históricos.

## Qué probar

Preferí PDF de ejemplo o copias de documentos sin información personal, nombres de alumnos, calificaciones, firmas u otros datos confidenciales. El procesamiento de PDF se hace en la computadora, pero las capturas y los informes que compartas podrían revelar información.

### 1. Seleccionar y ordenar páginas de varios archivos

- Abrí entre 3 y 6 PDF de prueba y elegí varias páginas de cada uno.
- Entrá en **Ordenar páginas…** y comprobá que se vean miniaturas.
- Cambiá el tamaño a **Pequeñas**, **Medianas** y **Grandes**.
- Seleccioná una hoja y comprobá que la vista ampliada permita leer e identificar su contenido.
- Compará la posición en el resultado, el nombre del PDF de origen y el número de página original que muestran la miniatura y el panel de vista previa.
- Si dos PDF tienen el mismo nombre pero están en carpetas distintas, verificá que se puedan distinguir.
- Cambiá el orden arrastrando miniaturas y usando **Subir** / **Bajar**. Probá también **Restablecer orden inicial**.

### 2. Guardar y comprobar el documento final

- Aplicá el orden y guardá el resultado en un archivo nuevo.
- Abrí el PDF resultante y comprobá que las páginas estén en el orden elegido.
- Confirmá que no se sobrescriban ni modifiquen los PDF originales.
- Repetí la prueba con otra combinación de archivos y páginas.

### 3. Revisar el comportamiento general

- Redimensioná la ventana y revisá si se puede acceder a los botones y al contenido.
- Probá **Herramientas PDF** y, si la necesitás, la vista previa de una página.
- Verificá que cancelar una operación no cree un archivo final inesperado.
- Si una miniatura no se puede mostrar, observá si la aplicación comunica el problema sin impedir el resto del trabajo.

No hace falta probar todo para reportar un problema. Una falla clara, junto con los pasos que la reproducen, ya es útil.

## Cómo informar el resultado

Compartí el sistema operativo y su versión, la arquitectura (Windows, Mac Intel o Apple Silicon), el enlace o número de la ejecución de Actions y la versión que aparece en la aplicación. Indicá:

- **Resultado:** correcto / problema.
- **Pasos:** qué hiciste, en orden.
- **Esperado:** qué tendría que haber ocurrido.
- **Obtenido:** qué ocurrió realmente.
- **Frecuencia:** siempre / algunas veces / una vez.

No adjuntes PDF de estudiantes ni documentos privados. Si sirve una captura, usá una con datos ficticios o difuminá la información confidencial.

## Alternativa: descargar el código fuente

Esta opción sí requiere Python y una terminal. Descargá el ZIP de la rama principal desde [Descargar el código fuente de main](https://github.com/JavierGrecco/PDF-Escolar/archive/refs/heads/main.zip), extraelo en una carpeta y abrí una terminal dentro de esa carpeta.

Requisitos: Python 3.11, 3.12 o 3.13 y conexión a Internet para instalar las dependencias.

**Windows PowerShell:**

    py -3.12 -m venv .venv
    .\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
    .\\.venv\\Scripts\\python.exe -m pip install -e .
    .\\.venv\\Scripts\\python.exe -m pdf_escolar

**macOS:**

    python3.12 -m venv .venv
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -e .
    .venv/bin/python -m pdf_escolar

Si un comando falla, copiá el mensaje de error sin incluir datos privados. Para una prueba de uso sencilla, se recomienda la opción de la aplicación ya compilada.
