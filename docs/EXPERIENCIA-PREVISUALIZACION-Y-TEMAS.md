# Hoja de ruta: previsualización, orden de páginas y temas visuales

**Estado:** hoja de ruta documentada el 10 de octubre de 2026; la primera implementación de previsualización está integrada en la rama de trabajo.  
**Alcance:** mejorar la experiencia de selección, orden y revisión del PDF final; corregir el estado vacío de la interfaz; establecer una base visual coherente y accesible.

## Resumen ejecutivo

La primera prueba real reportada en Windows confirma que el flujo básico actual funciona: cargar varios PDF, elegir páginas, ordenarlas y generar un documento nuevo. La próxima mejora no debe reemplazar ese flujo que ya resulta útil, sino hacer más fiable y cómoda la identificación de cada página antes de exportar.

La prioridad de producto es pasar de «ordenar miniaturas pequeñas y confiar en que son las páginas correctas» a **«identificar, previsualizar, ordenar y comprobar visualmente el documento que voy a crear»**. La previsualización tiene que ser interactiva: la persona debe poder corregir el orden desde allí sin volver atrás y reconstruir la selección.

También se atiende la impresión visual del estado vacío y se define una estrategia de apariencia para Windows y macOS. La primera implementación de revisión/miniaturas y la corrección del fondo vacío están hechas; el selector de temas y el editor avanzado siguen pendientes.

## Estado real y límites actuales

- La aplicación ya permite incorporar varios PDF, elegir páginas, reordenar la selección y generar un nuevo PDF; el usuario ha probado este flujo en Windows con varios archivos.
- La primera implementación incorpora miniaturas pequeñas/medianas/grandes, una vista detallada de la página seleccionada, identificación de archivo/página de origen y una vista ampliada. La revisión final se abre antes de elegir el destino cuando la secuencia aún no se había revisado.
- El área de documentos vacía ahora recibe un fondo explícito alineado con la superficie principal. El estado vacío con mensaje/acción dedicada y el sistema completo de temas quedan como refinamientos futuros.
- Las herramientas PDF actuales rotan páginas completas por número/rango, recortan márgenes uniformes y separan páginas. No equivalen a recortar visualmente una zona arbitraria, quitar una parte y recomponer el resto.
- El modelo inicial de composición ya existe, pero la interfaz de composición y el exportador de páginas compuestas todavía no están conectados.
- Los temas seleccionables y el sistema de tokens de color descritos aquí son una propuesta, no una función existente.

## Decisiones de producto

### D1. Mantener sencillo el camino habitual

La acción principal debe seguir siendo clara: agregar archivos, elegir páginas, ordenar, revisar y crear el PDF. Las capacidades de edición avanzada no deben llenar la ventana inicial de botones ni obligar a aprender conceptos de edición profesional.

### D2. Las miniaturas deben ayudar a identificar, no solo ahorrar espacio

La vista de ordenamiento ofrecerá tamaños de miniatura predecibles (por ejemplo, pequeño, mediano y grande), zoom o ampliación de la página seleccionada y una vista detallada accesible con un clic. El tamaño elegido no debe cambiar el orden ni perder la selección.

Cada miniatura debe comunicar, cuando haya espacio, información que ayude a reconocerla: número dentro del documento final, archivo de origen y número de página original. Estos datos deben seguir disponibles en la vista detallada aunque la miniatura sea pequeña. Los rótulos no deben tapar una parte importante del contenido de la página.

### D3. La previsualización previa a exportar debe permitir corregir el documento

Añadir una etapa de **Revisar documento** antes de crear el PDF final. No será una imagen estática ni una confirmación decorativa. La persona podrá:

- ver una página a un tamaño cómodo, con controles de acercar, alejar y ajustar a página;
- recorrer la secuencia final y comprender de qué archivo/página procede cada hoja;
- mover una página a otra posición desde la propia revisión, mediante arrastre y alternativas explícitas como «Mover antes/después»;
- quitar una página de la secuencia sin volver al selector inicial;
- volver a la selección o cancelar sin perder el trabajo;
- confirmar el total y el orden de las páginas antes de exportar.

La misma fuente de estado de la aplicación debe alimentar las miniaturas, la secuencia final y la exportación. Esto reduce el riesgo de que la vista previa muestre un orden distinto del que se escribe en el archivo. La acción «Crear PDF» se habilitará después de que la secuencia esté lista y validada.

### D4. Integrar edición en la revisión por capas

No todas las herramientas deben implementarse en una sola entrega. La vista previa será el lugar natural para las modificaciones relacionadas con la página, pero con un alcance escalonado:

**Primera capa — organización:** ampliar/inspeccionar, mover, quitar y revisar páginas.  
**Segunda capa — ajustes de página:** rotación con vista previa y recorte visual con controles claros, manteniendo el recorte actual de márgenes como herramienta conocida.  
**Tercera capa — composición visual:** seleccionar varias regiones, conservar fragmentos, excluir una zona dejando el espacio o separando las partes restantes y reordenar los fragmentos.  
**Cuarta capa — texto y maquetación:** insertar páginas de consignas, editar texto enriquecido y, posteriormente, colocar texto y fragmentos en un mismo lienzo.

La capa avanzada se presentará como **Crear documento** o equivalente. No se deben simular acciones que solo cambian la previsualización: todo control de edición debe producir el mismo resultado al exportar.

**Seguridad:** recortar u ocultar una zona no garantiza que los datos subyacentes hayan sido eliminados del PDF. La censura/redacción segura es una función diferente y queda fuera de esta primera etapa; requerirá una implementación verificable y advertencias explícitas.

### D5. Diseñar el estado vacío como parte de la experiencia

Antes de cargar archivos, la zona de trabajo debe conservar la misma identidad visual que el resto de la aplicación. Sustituir el negro reportado por una superficie neutra consistente con el tema vigente y un estado vacío deliberado, con un mensaje como «Todavía no hay documentos», una acción primaria «Agregar PDF» y, si la implementación existente lo permite de forma fiable, una indicación discreta de arrastrar y soltar archivos.

Evitar ilustraciones pesadas, grandes paneles decorativos y textos largos. Tras agregar archivos, la transición debe ser natural y no producir un salto brusco de colores. El estado vacío, el estado ocupado, la carga de miniaturas y el error necesitan tratamientos visuales diferentes.

### D6. Usar un sistema de apariencia limitado y coherente

Se propone el siguiente selector inicial:

- **Sistema (predeterminado):** seguir el modo de apariencia del sistema operativo cuando Qt y la plataforma permitan detectar y actualizarlo correctamente.
- **Claro:** alternativa explícita para quien prefiera mantenerlo.
- **Oscuro:** alternativa explícita, con fondos escalonados y texto legible, no una inversión automática de todos los colores.
- **Color de acento:** en una etapa posterior, ofrecer pocas paletas curadas compatibles con ambos modos, empezando por el azul de marca y evaluando dos o tres alternativas después de probar contraste y consistencia.

La preferencia del sistema debe ser el punto de partida. La posibilidad de forzar Claro u Oscuro es una excepción elegida por el usuario, no una sustitución silenciosa de la preferencia del sistema. No se propone una galería inicial con decenas de temas: su mantenimiento fragmentaría el diseño y la matriz de pruebas.

Los colores deben proceder de tokens semánticos compartidos (fondo de ventana, superficie, texto principal/secundario, borde, acento, selección, foco, éxito, advertencia y error) y no de valores arbitrarios repetidos en cada widget. Los diálogos, menús, campos, botones, estados vacíos, mensajes y paneles deben usar el mismo sistema.

**El papel debe seguir pareciendo papel.** En modo oscuro, el área exterior de trabajo puede ser oscura; una página PDF blanca o de color debe conservar su apariencia real en la previsualización. El tema de la interfaz nunca debe alterar el documento que se exporta.

No hay aquí una encuesta propia que permita afirmar qué color es «el más pedido». La recomendación se basa en patrones de plataforma y principios de diseño publicados, no en una estadística de preferencias de los usuarios de PDF Escolar.

### D7. Accesibilidad y contraste son requisitos de salida

Como mínimo, el diseño tomará como referencia WCAG AA: contraste de 4,5:1 para texto normal y 3:1 para texto grande y componentes gráficos relevantes. Debe haber foco visible al navegar con teclado, etiquetas entendibles, estados no comunicados solo por color y tamaños de texto que no desaparezcan con escalado del sistema.

Los estados seleccionados no dependerán únicamente de un matiz. Deben distinguirse también con borde, fondo, icono, posición o etiqueta. Se probará especialmente el texto secundario, los botones deshabilitados, las filas seleccionadas y los indicadores sobre fondos oscuros.

### D8. Preferencias persistentes y portabilidad

La elección de tema, tamaño de miniatura y otras preferencias visuales debe persistir entre sesiones. Antes de implementar el almacenamiento se verificará cómo la aplicación portable guarda actualmente la configuración; no debe cambiarse silenciosamente de una preferencia local/portable a un archivo de configuración diferente ni escribir dentro de carpetas de instalación protegidas. La primera ejecución debe tener valores predeterminados seguros si falta o se daña la configuración.

## Referencias de diseño investigadas

- [Apple — Dark Mode, Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/dark-mode): recomienda respetar la preferencia de apariencia global, usar paletas adaptadas y probar la legibilidad en claro y oscuro.
- [Apple — Color, Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/color): recomienda uso consistente del color, variantes para diferentes apariencias y contraste suficiente.
- [Microsoft Fluent 2 — Color](https://fluent2.microsoft.design/color): propone colores semánticos compartidos, uso sobrio del acento y no comunicar significado solo mediante color.
- [Microsoft Fluent 2 — Accessibility](https://fluent2.microsoft.design/accessibility): incluye referencias de contraste y foco visible.
- [Microsoft Support — Personalizar los colores en Windows](https://support.microsoft.com/es-es/windows/experience/personalization/personalize-your-colors-in-windows): documenta claro, oscuro, personalizado y color de énfasis del sistema.
- [Adobe Acrobat — Organizar páginas](https://helpx.adobe.com/acrobat/web/edit-pdfs/organize-documents/organize-pages.html): permite reorganizar, girar, agregar o eliminar páginas a través de miniaturas.
- [Adobe Acrobat — Miniaturas de página](https://helpx.adobe.com/acrobat/using/page-thumbnails-bookmarks-pdfs.html): incluye controles para agrandar y reducir miniaturas.
- [W3C — WCAG 2.1, contraste mínimo](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html): describe los umbrales de contraste para texto.

Estas referencias sirven como principios y comparación funcional. No implican copiar la interfaz, el código ni los elementos de marca de otros productos.

## Plan de implementación por etapas

### P0 — Auditoría visual y base común

- Reproducir el fondo negro reportado y localizar qué widget/estilo lo produce.
- Definir tokens de color en un único lugar; eliminar colores duros que contradigan el tema donde sea viable.
- Diseñar el estado vacío, carga, ausencia de resultados y error.
- Comprobar el aspecto actual en Windows, macOS Intel y Apple Silicon antes de cambiar estilos compartidos.
- Confirmar cómo se almacenan las preferencias en las versiones portable e instalables.

**Salida:** interfaz de inicio coherente y lista para soportar variantes de apariencia, sin modificar el comportamiento PDF.

### P1 — Identificación y miniaturas (primera implementación)

- Añadir tamaños de miniatura configurables y ampliación de una página seleccionada.
- Mostrar procedencia y numeración de manera legible.
- Implementar zoom, ajustar a página y navegación entre páginas en la vista detallada.
- Generar miniaturas y vistas pesadas fuera del hilo de interfaz y usar caché limitada.

**Implementado inicialmente:** tres tamaños de miniatura; vista detallada de la selección con posición en el documento final y procedencia; botón para abrir una vista ampliada; renderizado fuera del hilo de interfaz.\n\n**Pendiente:** comprobar la legibilidad con documentos reales, el cambio de tamaño en distintas resoluciones y el comportamiento con archivos muy largos.

### P2 — Revisión interactiva antes de exportar (primera implementación)

- Construir la vista final con una página grande y una tira/lista de miniaturas ordenables.
- Permitir arrastrar para cambiar el orden, además de acciones accesibles para mover antes/después.
- Permitir quitar una hoja, volver a editar la selección y cancelar sin perder cambios.
- Mantener sincronizados orden, selección, previsualización y exportación.
- Añadir, cuando el modelo actual lo permita sin deuda técnica, deshacer/rehacer para movimientos y eliminaciones.

**Implementado inicialmente:** «Crear PDF final» abre la revisión antes de elegir el destino si el orden aún no se revisó; la secuencia ordenada confirmada alimenta directamente el exportador. Si el usuario acaba de aplicar el orden desde la pantalla de organización, no se repite el diálogo.\n\n**Pendiente:** permitir quitar páginas desde esa vista, añadir deshacer/rehacer y ejecutar pruebas manuales en Windows y macOS.

### P3 — Tema del sistema, Claro y Oscuro

- Añadir un selector de apariencia con Sistema como predeterminado y opciones Claro/Oscuro.
- Probar el cambio en tiempo de ejecución y decidir el comportamiento si un entorno no comunica de forma fiable la preferencia del sistema.
- Auditar todos los controles propios y diálogos, no solo la ventana principal.
- Persistir la preferencia y mantener las páginas PDF con su color original.
- Añadir validación automatizada o comprobaciones de contraste para las combinaciones críticas.

**Salida:** ambas apariencias son completas y legibles, no solo una hoja de estilos parcial.

### P4 — Edición sencilla dentro de la previsualización

- Rotación de página con cambio visible inmediato.
- Recorte visual con asas y medidas coherentes.
- Confirmación clara de qué área se conserva.
- Exportación que respete exactamente la geometría vista y mantenga texto/vector cuando la fuente lo permita.

**Salida:** las operaciones implementadas en pantalla coinciden con el PDF exportado y se pueden revertir antes de crear el archivo.

### P5 — Editor de regiones y texto

Continuar la hoja de ruta de [Editor visual y composición](EDITOR-VISUAL-Y-COMPOSICION.md): fragmentos rectangulares múltiples, exclusión de zonas, recomposición, páginas de texto enriquecido, proyecto editable y luego maquetación con elementos mixtos.

**Salida:** creación de material didáctico desde partes de varios PDF sin comprometer la sencillez del flujo de combinación.

### P6 — Acentos de marca y refinamiento

- Evaluar una paleta corta de acentos con variantes claras/oscuras.
- No ofrecer una paleta si los controles deshabilitados, selección, foco y mensajes no mantienen suficiente contraste.
- Validar el diseño con personas no técnicas y pruebas manuales en pantallas y escalados distintos.

**Salida:** personalización útil que mantiene la identidad de la aplicación y no multiplica innecesariamente los casos de soporte.

## Criterios de aceptación comunes

Una etapa no se considera lista solo porque compila. Tiene que cumplir lo siguiente:

1. **Coincidencia visual:** la secuencia mostrada coincide exactamente con la secuencia exportada, incluidas hojas repetidas de un mismo PDF.
2. **Trazabilidad de página:** la persona puede identificar archivo fuente y página original sin adivinar por el dibujo de la miniatura.
3. **No destructivo:** los archivos originales permanecen intactos; la app no sobrescribe por accidente el documento fuente.
4. **Integridad PDF:** el archivo temporal se puede abrir y validar antes de publicarlo en destino; las páginas y su orden coinciden con el resultado solicitado.
5. **Calidad del contenido:** cuando se hace una operación geométrica, comprobar apariencia, rotaciones, CropBox, diferentes tamaños de página y selección de texto. No rasterizar el PDF completo solo para simplificar la vista previa.
6. **Rendimiento:** abrir documentos largos no congela la interfaz; mostrar progreso/estado y cancelar cuando sea seguro.
7. **Accesibilidad:** foco visible, contraste verificado, nombres comprensibles y ninguna operación principal exclusiva de gestos o teclado.
8. **Compatibilidad:** CI y pruebas manuales en Windows, macOS Intel y Apple Silicon para la aplicación principal. El OCR opcional conserva su matriz de plataformas separada.
9. **Tema consistente:** diálogos, menús, campos y errores respetan la apariencia elegida; al iniciar, no queda una superficie negra accidental.
10. **Distribución:** no añadir dependencias grandes, restrictivas o con licencias incompatibles sin una justificación y revisión explícitas.

## Fuera del alcance inicial

- Una galería con decenas de temas o edición libre de todos los colores.
- Redacción segura de información confidencial mediante el recorte habitual.
- Maquetación libre avanzada, capas complejas o herramientas gráficas genéricas antes de resolver la revisión de páginas.
- Una promesa de accesibilidad total sin las correspondientes pruebas.
- Cambiar el PDF original; las modificaciones se aplican al documento de trabajo o al archivo de salida.

## Registro de decisiones

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-10 | Priorizar previsualización interactiva antes de exportar | Resuelve el punto débil señalado tras la prueba real del flujo |
| 2026-10-10 | Añadir tamaños de miniatura y vista ampliada | Reduce la ambigüedad al reconocer páginas |
| 2026-10-10 | Corregir el estado vacío antes de pulir detalles decorativos | Evita la impresión de fallo cuando aún no se agregaron archivos |
| 2026-10-10 | Tema Sistema predeterminado, con Claro/Oscuro opcionales | Respeta la plataforma y permite una elección voluntaria |
| 2026-10-10 | Paletas de acento limitadas y diferidas | Reduce mantenimiento y permite probar contraste |
| 2026-10-10 | Edición dentro de la vista previa por capas | Evita hacer crecer de golpe el flujo básico y permite validar cada transformación |
| 2026-10-10 | Mantener blanco/original el papel en la vista PDF oscura | El tema no debe falsear el aspecto del documento que se va a imprimir |
