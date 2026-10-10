# Visión de producto: editor visual de documentos por páginas y fragmentos

## Objetivo

Evolucionar PDF Escolar de una herramienta para seleccionar y combinar páginas a un **taller visual para crear documentos educativos y documentos de uso general**. La persona debe poder tomar partes de diferentes PDF, decidir qué conservar y qué excluir, montar las piezas en el orden y la posición que quiera, insertar consignas escritas y exportar un PDF final.

El producto debe seguir siendo local, intuitivo, no destructivo y compatible con el flujo de distribución de escritorio. La complejidad técnica tiene que quedar escondida detrás de acciones visibles y reversibles.

## Decisión de producto

No convertir la ventana inicial en un editor profesional recargado. Mantener dos niveles:

1. **Modo sencillo:** agregar PDFs, elegir páginas, ordenarlas, combinar y exportar; las funciones actuales siguen siendo rápidas y fáciles de encontrar.
2. **Modo Crear documento:** un espacio visual para extraer fragmentos, montar páginas, insertar texto y ajustar el resultado. Solo aparecen las herramientas avanzadas cuando la persona entra en este modo.

La promesa no debe ser «un editor PDF con todos los botones posibles», sino «preparar el documento que necesitás, a tu manera, sin pelearte con el programa».

## Experiencia de trabajo propuesta

### Distribución de pantalla

- **Panel Fuentes** (izquierda): documentos agregados, miniaturas de páginas y buscador de archivos.
- **Lienzo central**: vista fiel de la página final, con selección, recorte, asas para redimensionar y guías de alineación.
- **Guion del documento** (abajo): miniaturas de páginas finales, fragmentos y páginas de texto. Arrastrar una pieza cambia el orden; duplicar crea una copia independiente.
- **Inspector contextual** (derecha): las pocas propiedades relevantes del elemento elegido (giro, tamaño, posición, ajuste, tipografía y color). Se oculta cuando no hay nada seleccionado.
- **Barra principal**: Deshacer, Rehacer, Agregar página, Insertar fragmento, Texto, Rotar, Recortar y Exportar.

Evitar tener todos los controles abiertos todo el tiempo. La barra muestra acciones principales y el inspector cambia según la selección. Todas las acciones importantes deben funcionar con botones, clic y arrastre del mouse o touchpad; los atajos de teclado son una vía adicional, nunca la única.

## Modelo conceptual: no editar los PDF fuente, editar piezas

El documento de trabajo tendrá páginas de composición. Cada página de composición puede contener uno o más elementos ordenables:

- **Fragmento PDF**: referencia a un PDF fuente, índice de página y rectángulo de la página que se desea conservar.
- **Bloque de texto**: texto enriquecido y formato (tipografía, tamaño, color, negrita, cursiva, subrayado, alineación y listas).
- **Página completa**: una página fuente completa también se representa como un fragmento que ocupa todo el lienzo.
- **Elementos futuros**: imágenes importadas, formas, líneas, encabezados y pies podrán añadirse sin cambiar el modelo fundamental.

La secuencia final se modela como páginas de composición con elementos posicionados. Por separado se guarda el orden de páginas. Esto permite que una pieza pueda vivir en su propia página o combinarse con otros fragmentos y texto en una misma hoja. En el primer corte de entrega se puede comenzar con fragmentos como páginas independientes, pero el modelo no debe impedir el montaje de varios elementos en un lienzo.

Cada fragmento debe referenciar la fuente y guardar el rectángulo en coordenadas normalizadas (0 a 1, relativas al área visible de la página), el giro y los ajustes de presentación. La interfaz usa coordenadas de pantalla; la conversión a coordenadas PDF debe ser responsabilidad de una única capa del motor y tener pruebas para páginas rotadas, CropBox y distintos tamaños.

## Recortar, seleccionar y excluir: tres acciones diferentes

La selección de regiones es una de las capacidades centrales y no debe quedarse en «recortar márgenes».

### Conservar una región

1. Abrir la página fuente.
2. Arrastrar con el mouse o touchpad para dibujar un rectángulo; mover los bordes para afinarlo.
3. Pulsar **Usar esta parte** o duplicar la región.
4. La región aparece como fragmento en el guion. Se puede renombrar, duplicar, rotar, ordenar y colocar en una página final.
5. Repetir sobre otras páginas o PDFs; el usuario construye el documento con las partes que necesita.

Debe ser posible tomar varias regiones distintas de una sola página. La vista previa tiene que mostrar claramente qué contenido entra en el fragmento y qué queda fuera.

### Excluir una región

La interfaz debe ofrecer una acción explícita para quitar una zona seleccionada, sin exigir seleccionar manualmente todo lo demás. Según el contexto, ofrecer dos resultados entendibles:

- **Quitar esta zona y dejar el espacio:** conserva la distribución visual de la página y deja un área vacía en el lugar eliminado.
- **Quitar esta zona y juntar las partes restantes:** divide la página en regiones rectangulares restantes para que el usuario las pueda ordenar como piezas independientes y reacomodarlas en el lienzo.

Para exclusiones rectangulares, la diferencia geométrica se puede expresar como regiones rectangulares no superpuestas. Varias exclusiones posteriores deben recalcular la composición sin dejar duplicados ni solapamientos accidentales. Si una operación deja piezas demasiado pequeñas o ambiguas, pedir una acción explícita en vez de adivinar.

### Advertencia importante sobre contenido oculto

Un recorte PDF normal limita el área visible, pero puede conservar datos fuera de esa área dentro del archivo. Es suficiente para reorganizar apuntes, consignas y fragmentos; **no es redacción segura de datos confidenciales**. Si más adelante se agrega una función de censura, deberá ser una herramienta separada, con una advertencia propia y una implementación de eliminación o aplanado verificable.

## Rotación

- La rotación de 90°, 180° y 270° debe estar disponible para una página o fragmento individual, con vista previa inmediata.
- La rotación se aplica a la pieza seleccionada, no a todas las páginas fuente por accidente. Una opción explícita permite aplicar el mismo giro a un grupo de piezas.
- La rotación libre con arrastre de un control angular es deseable para enderezar imágenes y montar recortes. Antes de publicarla, hay que verificar que la exportación mantenga el texto seleccionable, la nitidez vectorial, el tamaño final y los límites correctos; no aceptar una solución que convierta documentos enteros en imágenes para simular el giro.
- Mientras la rotación libre no supere las pruebas de integridad, mantener 90°/180°/270° como operaciones confiables y anunciar el enderezado fino como una capacidad posterior, no como un control que solo funciona en pantalla.

## Texto y consignas entre páginas o fragmentos

Agregar **Nueva página de texto** debe ser una acción de primer nivel. Una persona docente debe poder insertar una consigna antes de un ejercicio, una explicación entre dos fragmentos o una carátula al principio del trabajo.

El primer editor enriquecido debe incluir:

- tipografía y tamaño;
- negrita, cursiva, subrayado;
- color de texto;
- alineación;
- listas numeradas y con viñetas;
- títulos y subtítulos;
- deshacer y rehacer;
- vista previa en tamaño A4/carta y orientación vertical/horizontal.

La página de texto se inserta en el guion como otra página, se puede mover entre fragmentos, duplicar y volver a editar. El texto debe exportarse como texto/vector PDF siempre que sea posible, no como una captura de pantalla. Conviene reutilizar `QTextDocument`, `QTextEdit` y las capacidades de rich text ya disponibles en Qt/PySide6 antes de añadir una dependencia de editor externa. Qt admite un subconjunto documentado de HTML enriquecido; por tanto, la aplicación debe limitar la barra a funciones que se puedan representar fielmente al exportar.

En una segunda etapa, permitir bloques de texto posicionados dentro de una página que contenga también recortes. La primera versión debe priorizar una experiencia predecible, con saltos de página y estilos estables entre Windows y macOS, antes de ofrecer maquetación libre avanzada.

## Usabilidad inspirada en productos simples y elegantes

- **Vista previa antes que opciones técnicas:** seleccionar una pieza y ver inmediatamente lo que se conservará.
- **Deshacer y rehacer globales:** ninguna operación destructiva sin una acción inversa razonable.
- **Lenguaje cotidiano:** «Usar esta parte», «Quitar esta zona», «Agregar consigna», «Mover antes»; no exponer CropBox, matrices ni otros términos internos.
- **Edición no destructiva:** las fuentes no se sobrescriben. El usuario edita referencias y piezas hasta exportar.
- **Operaciones visibles:** al guardar/exportar, informar nombre, destino y cantidad de páginas resultantes.
- **Manejo cómodo:** zoom, ajustar a página, desplazamiento por touchpad, arrastre, selección y controles accesibles con teclado. No depender de gestos difíciles de descubrir.
- **Complejidad progresiva:** controles avanzados agrupados en paneles contextuales, sin convertir la ventana inicial en una consola.
- **Recuperación:** conservar el borrador de trabajo y ofrecer recuperación si la app se cierra inesperadamente.

## Guardar proyecto y exportar PDF son cosas diferentes

Incorporar un formato de proyecto editable de PDF Escolar (por ejemplo `.pdfescolar`) separado del PDF final. El proyecto guardará la secuencia, geometría, formatos de texto, referencias a fuentes y versión del esquema. Debe señalar si faltan fuentes movidas y ofrecer volver a localizarlas, en vez de fallar silenciosamente.

El PDF final exportado será un archivo independiente. La exportación debe validar que se puede volver a abrir, que el número de páginas coincide con la composición, y que no se ha sobrescrito accidentalmente ningún PDF fuente. Guardar/recuperar un proyecto debe funcionar sin conexión.

## Arquitectura técnica propuesta

- **UI:** Qt/PySide6, usando un lienzo basado en `QGraphicsView/QGraphicsScene` para selección, elementos movibles, asas, zoom y arrastre. Esta clase de vista ya admite interacción con mouse, transformaciones y selección por banda elástica; la lógica de aplicación define las herramientas y sus atajos.
- **Editor de texto:** `QTextEdit/QTextDocument`, con una barra limitada a las propiedades soportadas y un camino de exportación PDF basado en Qt.
- **Modelo de documento:** clases propias independientes de la UI: proyecto, página de composición, fragmento fuente, bloque de texto, posición, tamaño, giro y orden.
- **Motor PDF:** mantener `pikepdf` para operaciones no destructivas, orden de páginas y exportación de piezas rectangulares. Evitar adoptar PyMuPDF únicamente por comodidad sin decidir conscientemente la licencia AGPL/comercial y el efecto en la distribución MIT.
- **Previsualización:** rasterización solo para mostrar el lienzo; exportar los fragmentos desde PDF vectorial, no a partir de la imagen de previsualización.
- **Exportación:** construir primero un resultado temporal, comprobar estructura e integridad, y publicarlo al destino solo después de validar el archivo.
- **Rendimiento:** miniaturas y vistas previas en segundo plano con caché limitada; las tareas pesadas no bloquean la UI.

## Plan incremental

### Etapa 1 — piezas fiables

- Mejorar las herramientas de página para operar por selección visual, no solo por rangos escritos.
- Selección rectangular, conservar región y crear fragmento.
- Exclusión rectangular con opción de dejar espacio o crear piezas restantes.
- Girar página/fragmento individual en incrementos de 90°.
- Guion visual con arrastrar/soltar, duplicar, borrar y reordenar fragmentos.
- Pruebas geométricas con páginas rotadas, CropBox, mezclas de tamaños y fuentes de múltiples PDFs.

### Etapa 2 — consignas y documentos híbridos

- Insertar y editar páginas de texto enriquecido entre las demás.
- Exportar texto como texto/vector PDF y verificar búsquedas, fuentes y saltos de página.
- Añadir deshacer/rehacer y guardado/recuperación del proyecto.
- Incluir las pruebas manuales y las compilaciones de Windows y Apple Silicon.

### Etapa 3 — composición libre

- Página con varios fragmentos y bloques de texto posicionados.
- Alineación, márgenes, distribución, tamaño de página y orientación.
- Rotación libre probada con transformación vectorial.
- Herramientas agrupadas, guías de alineación y atajos, manteniendo el modo sencillo intacto.

### Etapa 4 — refinamiento

- Accesibilidad y pruebas con usuarios no técnicos.
- Medición de memoria y respuesta con PDF extensos.
- Importación de imágenes, plantillas de consignas y estilos reutilizables solo si surgen necesidades reales.
- Censura segura únicamente con pruebas especializadas y lenguaje inequívoco.

## Criterios para considerar una etapa lista

- La persona completa una tarea típica sin leer documentación técnica.
- Mouse y touchpad permiten realizar todas las acciones principales.
- El resultado visual coincide con la vista previa; la geometría se prueba con fixtures de referencia.
- Los originales permanecen intactos y los resultados se verifican antes de publicarse.
- Los PDF con texto siguen permitiendo seleccionar/copiar cuando corresponde.
- No hay regresiones en Windows ni Apple Silicon; las funciones actuales de la app siguen operativas en Mac Intel.
- No se amplía la distribución con nuevas dependencias pesadas o licencias restrictivas sin justificarlo por una necesidad concreta.
