# Lista de pruebas manuales — PDF Escolar

Esta lista complementa las pruebas automáticas. Usá copias de archivos de prueba, no documentos importantes. Anotá el sistema operativo, la versión de la aplicación y cualquier mensaje inesperado.

## Antes de empezar

Prepará dos PDF fáciles de reconocer:

- **Libro A:** 3 páginas, con una palabra distinta en cada página: «A-UNO», «A-DOS» y «A-TRES».
- **Libro B:** 2 páginas, con «B-UNO» y «B-DOS».

Confirmá que los originales sigan iguales después de las pruebas.

## Pruebas funcionales

- [ ] La aplicación abre sin cerrarse y muestra el nombre y la versión.
- [ ] Se pueden agregar los dos PDF desde el selector de archivos.
- [ ] También se pueden agregar arrastrándolos a la ventana.
- [ ] Después de agregar un PDF, el área de carga se compacta y el botón pasa a decir «Agregar más PDF».
- [ ] Incluso en estado compacto, se pueden arrastrar otros PDF al área de carga.
- [ ] Al quitar todos los documentos, el área de carga vuelve a mostrar las instrucciones iniciales.
- [ ] Agregar varios PDF dañados o protegidos muestra un único resumen, sin una sucesión de ventanas emergentes.
- [ ] Los errores muestran una explicación y un próximo paso en español; nunca incluyen trazas técnicas, nombres de excepciones ni detalles internos de las bibliotecas.
- [ ] Probar un PDF protegido, uno dañado, uno inexistente y una carpeta de destino sin permisos produce mensajes entendibles y no bloquea la aplicación.
- [ ] Si algunos archivos fallan, los PDF que sí se pudieron abrir siguen cargados.
- [ ] Los detalles del error se pueden consultar sin obligar al usuario a leerlos para entender qué pasó.
- [ ] Cada tarjeta muestra el nombre completo y legible del PDF en una fila propia, además de la cantidad de páginas y el tamaño.
- [ ] Probar nombres largos y cambiar el escalado de pantalla (por ejemplo, 125 % o 150 % en Windows); el nombre sigue visible.
- [ ] La selección inicial incluye todas las páginas.
- [ ] Escribir `3, 1` en el Libro A muestra dos páginas seleccionadas y conserva ese orden al exportar.
- [ ] «Elegir visualmente» abre las miniaturas; al confirmar la selección, los rangos se actualizan.
- [ ] Abrir y cancelar rápidamente el selector de miniaturas no cierra la aplicación ni deja la ventana bloqueada.
- [ ] Cambiar entre grupos de miniaturas varias veces; la barra de carga corresponde al grupo actual y no desaparece antes de tiempo.
- [ ] Las flechas cambian el orden de los documentos y deshabilitan el movimiento cuando ya están al principio o al final.
- [ ] Arrastrar el control ↕ con mouse funciona para reordenar los documentos; soltar antes y después de una tarjeta produce el orden esperado.
- [ ] Repetir el arrastre usando el panel táctil, sin mouse externo.
- [ ] «Ordenar páginas…» muestra miniaturas de ambos PDF, con el nombre del archivo y número de página.
- [ ] En el organizador, mover páginas con arrastre, Subir, Bajar y Restablecer orden inicial actualiza el orden esperado.
- [ ] Desplazarse rápidamente por las miniaturas y cerrar el organizador no bloquea la aplicación ni produce cierres inesperados.
- [ ] Crear una secuencia mezclada, por ejemplo B-DOS, A-TRES, B-UNO, A-UNO; exportarla y verificar visualmente que ese sea el orden final.
- [ ] Cancelar el organizador no cambia el orden previamente aplicado; cancelar Guardar no crea un archivo.
- [ ] Cambiar un rango o quitar/agregar un PDF después de ordenar páginas no deja una secuencia vieja; volver a ordenar si hace falta.
- [ ] Cuando un cambio invalida el orden manual, la aplicación lo explica y dice cómo volver a «Ordenar páginas…».
- [ ] Cerrar y reabrir la aplicación; «Seleccionar archivos PDF» comienza en la última carpeta utilizada.
- [ ] El resumen actualiza la cantidad de páginas seleccionadas cuando cambia un rango.
- [ ] Intentar usar un rango inválido, por ejemplo `1-99` en un PDF de 3 páginas, muestra un aviso y no genera un PDF incompleto.
- [ ] Un PDF protegido con contraseña o dañado no se agrega como si fuera válido; se muestra un aviso entendible.
- [ ] Al exportar, el PDF final se puede abrir y contiene las páginas seleccionadas, en el orden esperado.
- [ ] Cancelar el diálogo de guardado no crea un archivo.
- [ ] Los originales no se modifican.
- [ ] La aplicación sigue respondiendo mientras revisa archivos y durante la exportación.
- [ ] Quitar un documento actualiza el resumen y el botón de exportación.

## Pruebas de distribución

### Windows

- [ ] El ejecutable portable abre en una computadora que no tenga Python instalado.
- [ ] El instalador completa el proceso y permite abrir la aplicación desde el menú Inicio.
- [ ] Cerrar y volver a abrir la aplicación no muestra errores inesperados.
- [ ] Anotar cualquier advertencia de SmartScreen o del antivirus; no ignorar un aviso sin verificar el origen del archivo.

### macOS Intel y Apple Silicon

- [ ] Probar el arrastre con el panel táctil en un MacBook y con mouse si está disponible.
- [ ] Confirmar que la aplicación principal abre, importa y exporta PDF en Mac Intel y Apple Silicon.
- [ ] Confirmar que el nombre de los PDF sigue legible con el escalado y tamaño de ventana habituales.

- [ ] Usar el paquete correspondiente a la arquitectura del equipo.
- [ ] Abrir el DMG y arrastrar PDF Escolar a Aplicaciones.
- [ ] Abrir la aplicación desde Aplicaciones y probar la importación y exportación.
- [ ] Anotar las advertencias de Gatekeeper; las compilaciones sin firma ni notarización pueden mostrarlas.

## Resultado

- **Sistema y versión:**  
- **Versión de PDF Escolar:**  
- **Pruebas realizadas:**  
- **Resultado:** aprobada / fallida  
- **Errores o pasos para reproducirlos:**  


## Herramientas PDF

- [ ] Abrir «Herramientas PDF» desde la ventana principal.
- [ ] Cancelar la elección del PDF no inicia ninguna operación.
- [ ] Girar una página 90° a la derecha; confirmar que solo gira la página indicada y que se conserva el contenido vectorial.
- [ ] Girar páginas 90° a la izquierda y 180°.
- [ ] Dejar vacía la selección de páginas y confirmar que la herramienta actúa sobre todas las páginas.
- [ ] Introducir rangos inválidos, repetidos o fuera de límite; se muestra un aviso comprensible y no se reemplaza ningún archivo.
- [ ] Recortar márgenes de una copia usando distintos valores en milímetros; comprobar visualmente que el contenido no se rasteriza.
- [ ] Introducir márgenes que eliminen toda el área visible de una página; se cancela la operación y cualquier PDF de salida previo permanece intacto.
- [ ] Separar un PDF de varias páginas en archivos individuales, incluida una selección en un orden específico.
- [ ] Intentar separar páginas en una carpeta con nombres de salida existentes; no se reemplaza ningún archivo previo.
- [ ] Confirmar que el PDF de origen permanece intacto en todas las operaciones.
- [ ] Cerrar la ventana mientras una operación está en curso; la ventana espera al final de la operación en vez de terminar el trabajo de forma insegura.


## Reconocimiento de texto (OCR)

Estas pruebas requieren una versión de prueba que incluya una publicación del complemento OCR. En la primera ejecución se necesita conexión a Internet para instalarlo; después, desactivá la conexión para comprobar que el reconocimiento sigue siendo local.

- [ ] En un equipo compatible, elegir «Crear PDF buscable (OCR)» y confirmar que la aplicación explica qué componente se descargará y que los PDF no se suben.
- [ ] Instalar el complemento y comprobar que se guarda en el perfil del usuario sin pedir permisos de administrador.
- [ ] Probar un escaneo en español, guardar el resultado como un PDF nuevo y verificar que los originales no cambian.
- [ ] Abrir el PDF generado en un lector y buscar una palabra visible en el escaneo; confirmar que se puede seleccionar y copiar texto reconocido.
- [ ] Comparar visualmente el original y el resultado; la capa de texto no debe reemplazar la imagen de la página.
- [ ] Repetir con «Español e inglés» en un documento bilingüe.
- [ ] Probar un PDF que ya contiene texto digital: el reconocimiento debe omitir ese texto cuando corresponda y no deteriorar su apariencia.
- [ ] Seleccionar rangos concretos, por ejemplo 2-3; comprobar que el resultado conserva todas las páginas y aplica OCR solo a las seleccionadas.
- [ ] Probar un PDF con páginas giradas o ligeramente inclinadas y revisar el resultado.
- [ ] Probar un PDF protegido con contraseña o dañado; se debe mostrar un aviso entendible y no reemplazar ningún archivo de salida previo.
- [ ] Cerrar la aplicación durante una operación larga solo después de confirmar que el flujo espera a que el proceso termine y no deja un archivo parcial.
- [ ] Desconectar Internet y volver a ejecutar OCR; la función debe trabajar con el complemento ya instalado.
- [ ] En Mac con Apple Silicon y macOS 14 o posterior, comprobar la instalación y ejecución de OCR.
- [ ] En Mac Intel y en Mac Apple Silicon con macOS anterior a 14, confirmar que se indica que OCR no está disponible sin afectar las demás herramientas PDF.
- [ ] Registrar sistema operativo, versión del complemento, idioma, tamaño aproximado del escaneo y resultado de la prueba.
