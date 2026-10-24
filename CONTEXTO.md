# Contexto del proyecto — Reto "Corte de rosas" (Sabana Hack)

> Documento vivo. Sirve como punto de partida para el equipo y para cualquier asistente de IA que trabaje en el repo.
> Última actualización: 2026-10-23.

---

## 1. El reto en una página

**Pregunta del reto:** ¿Cómo puede un sistema robótico transformar la manera en que las personas aprenden, interpretan y deciden el momento adecuado (punto de corte) para cortar una rosa de exportación?

**Qué es el punto de corte:** la rosa se corta *antes* de abrir del todo, porque termina de abrir durante la poscosecha, el transporte y la llegada al cliente. La decisión se toma pensando en cómo se verá la flor días después.

**Por qué es difícil aprender:**
- La diferencia entre "lista" y "todavía no" es sutil.
- El criterio es tácito: el experto lo reconoce, pero le cuesta explicarlo.
- La decisión es hoy y el efecto se ve días después.
- Dos personas pueden leer la misma rosa de forma distinta.
- Ningún rasgo decide solo (color, apertura, forma del botón, sépalos, tallo, hojas…) y el criterio cambia según la variedad.

**A quién afecta:**
| Actor | Dolor |
|---|---|
| Trabajador nuevo | Poca confianza, aprendizaje lento, depende de tener a alguien experimentado cerca |
| Trabajador experimentado | Formar a otros le quita tiempo de su propio trabajo |
| Finca | La variación entre decisiones produce una calidad de corte menos uniforme, y esa calidad llega al cliente |

### Reglas obligatorias
- Debe incluir un **sistema robótico**: algo físico que **capte información del entorno y actúe sobre él**.
- No tiene que cortar la rosa ni reemplazar a la persona, pero su presencia debe **tener sentido frente al problema**.
- En la presentación el prototipo se **pondrá a prueba con situaciones de corte evaluadas en ese momento**, así que debe funcionar más allá de un caso preparado.
- El equipo debe conocer y explicar los **límites** del prototipo.

### Lo que hay que poder mostrar al final
1. Qué necesidad identificamos y a quién ayudamos.
2. El prototipo funcionando.
3. Cómo se usa y cómo aporta al aprendizaje o a la decisión.
4. El criterio detrás de la propuesta y **por qué la parte robótica aporta valor**.
5. Qué aprendimos.
6. Validación: supuestos iniciales y cuáles cambiaron, qué probamos y qué observamos, limitaciones frente a una finca real y qué haría falta explorar después.

### Criterios de evaluación (100 pts)
| Criterio | Pts | Qué distingue un resultado "destacado" |
|---|---|---|
| Funcionamiento y evidencia | **25** | Funciona, responde a los casos en vivo y muestra resultados y límites |
| Pertinencia de la propuesta | 15 | El robot responde directamente a la necesidad; queda claro por qué lo físico aporta |
| Creatividad e innovación | 15 | Enfoque original y bien sustentado |
| Presentación (pitch) | 15 | Estructura clara y respuestas sólidas |
| Comprensión de la necesidad | 10 | Quién, cuándo y por qué, sustentado en lo que observamos o consultamos |
| Experiencia de uso | 10 | Alguien sin conocimientos técnicos lo usa de forma segura sin explicación |
| Validación y aprendizaje | 10 | Pruebas concretas, qué cambió y qué falta |

**Restricciones:** unas 20 horas de desarrollo y 5 integrantes (no todos programan). Se espera un prototipo demostrable, no un producto.

---

## 2. Propuesta inicial del equipo (v0)

**Núcleo:** una **red neuronal convolucional (CNN)** entrenada con bases de datos de fotos de rosas. Es el "cerebro" compartido al que acceden tres componentes:

1. **Robot con visión.** Ve y toma fotos de las rosas para apoyarse en la decisión. Con el tiempo, recoge fotos etiquetadas por trabajadores experimentados para seguir entrenando la red (aprendizaje continuo).
2. **App móvil para trabajadores.** Al empezar pregunta **en cuántos días la rosa debe estar lista para la venta** (tiempo hasta el mercado). Luego el trabajador toma fotos y la app responde si la rosa está en punto de corte o no, lo que da confianza a quien está empezando.
3. **Simulación en Meta Quest (VR).** Simulación de rosas para que los trabajadores nuevos practiquen antes de ir al cultivo.

---

## 2.0 Propuesta actual (v2) — cambio de alcance (2026-10-23)

**Restricción nueva:** la empresa **no permite que los operarios usen celulares** en el cultivo. Por eso
la app móvil para la foto del momento del corte deja de existir. La solución se reorganiza en tres áreas,
cada una con su carpeta en el repo:

1. **`metaquest/` — Entrenamiento con realidad aumentada (Meta Quest).** Enseña cómo reconocer el punto de corte y cómo cortar. Usa **modelos 2D**, sin modelar rosas en 3D.
2. **`app-tablet/` — Juego en tablet para mecanizar el proceso.** La finca tiene un **proceso estándar sencillo de tres categorías**: *muy pronto*, *punto óptimo* y *muy tarde*. El juego entrena esa clasificación y también la **sanación de la planta después del corte** (el tratamiento que necesita para volver a crecer y seguir produciendo), que es donde los operarios más se demoran o se equivocan.
3. **`robot/` — Robot de detección por sectores + dashboard.** Recorre el campo, detecta con la red neuronal (RosaNet) los botones listos para cortar en cada sector y envía un reporte a un dashboard con dos vistas:
   - **Coordinadores:** entender el estado del campo y organizar al personal.
   - **Pantalla a la entrada del campo:** a qué sectores deben ir los operarios.

   Objetivo: detectar los botones a tiempo, antes de que se abran demasiado y se pierdan, y optimizar el tiempo de los operarios.

**Implicaciones para la red neuronal (por decidir):**
- La finca piensa en **3 categorías** (muy pronto / punto óptimo / muy tarde), no en 4 etapas de apertura. Lo natural es que RosaNet entregue esas 3 categorías (o que las 4 etapas se traduzcan a ellas), para que el robot, el juego y la AR hablen el mismo idioma que la finca.
- Los "tips" por etapa pasan de la app móvil al juego de la tablet y a la AR.

> La sección 2.1 (v1) se conserva como historia. Lo del robot por cuadrantes sigue vigente; la app móvil queda reemplazada por la v2.

## 2.0.1 Información recibida de la finca (General.zip, 2026-10-23)

### Contenido
| Material | Detalle |
|---|---|
| `Información técnica.pdf` | Partes de la rosa (botón floral, pétalos, sépalos, cáliz, pedúnculo, hojas, tallo), qué es invernadero y cama, y la definición del punto de corte |
| `01_Inmaduro_No_Cortar` | 37 fotos + PDF |
| `02_Punto_Optimo_Corte` | 18 fotos + PDF |
| `03_Pasado_Sobreabierto` | 2 fotos + PDF |
| `04_Casos_Dificiles_Ruido` | 8 fotos + PDF |
| `Videos de apoyo` | "Corte con carro" (10 s), "Punto de corte baja" (64 s, video de capacitación con puntos de corte 1, 2 y 3), "Video 1 vista a un lado" (28 s), "Video 2 vista al camino" (11 s) |
| `Párrafo de Loop.loop` | Componente de Microsoft Loop; no se pudo extraer contenido útil |

### Criterio de corte de la finca
- **Variedad: Freedom** (rosa roja). Todo el material es de una sola variedad.
- La finca usa una escala de **"puntos" de corte**. El **punto 3** es el punto de corte: *"el caracol está definido mostrando centro, el color de los pétalos es vivo e intenso y la flor presenta un patrón de copa"*.
- **La falla más común es cortar en punto 2 (cerrado):** la cabeza se ve más pequeña, el rojo es más oscuro y los sépalos están más pegados a los pétalos.
- Las 3 categorías del proceso estándar: **Inmaduro – no cortar** (punto ≤ 2), **Punto óptimo de corte** (punto 3) y **Pasado / sobreabierto**.
- Estos rasgos (forma de copa, caracol con centro visible, intensidad del rojo, sépalos separados y tamaño de la cabeza) son la base de los tips de la AR, del juego y de la explicación del robot.

### Cómo vienen las fotos (importante para entrenar)
- Son **fotos de escena dentro del invernadero**, no recortes: cada una tiene muchas rosas, y en el PDF un **círculo naranja marca cuál es la rosa de esa categoría**. Los JPEG sueltos no tienen el círculo.
- Por eso **una misma foto aparece en varias carpetas** (por ejemplo, la 26 está en Inmaduro, Óptimo y Difíciles): en cada PDF se marca una rosa distinta. En total hay **56 fotos únicas**.
- Los círculos son **figuras vectoriales en el PDF**, así que se pueden extraer sus coordenadas automáticamente y convertirlas en cajas YOLO para cada foto. Eso ahorra la anotación manual, aunque conviene revisar las cajas en Roboflow porque el círculo es más grande que la rosa.
- **Desbalance fuerte:** solo hay 2 ejemplos de "Pasado". Con eso la red no aprende la clase; hay que completarla con los datasets públicos (`flower`, `3_full_bloom`, `4_senescence`) o tomar más fotos.
- **Casos difíciles:** contraluz contra el plástico del invernadero, rosas lejanas y diminutas, y rosas tapadas por hojas. Son el mejor **conjunto de prueba de robustez**; no hay que usarlos para entrenar.

### Lo que muestran los videos (implicaciones para el robot)
- Los **pasillos entre camas son angostos** y los comparten los operarios con su carro o caja de corte. El robot debe ser compacto y no estorbar.
- Las rosas están en la **parte alta de plantas altas**. Las fotos de la finca y los videos de "vista a un lado" y "vista al camino" están tomados **desde abajo mirando hacia arriba**, que es justo la perspectiva de una cámara montada en un robot bajo. La cámara debe apuntar hacia arriba y tolerar el **contraluz**.
- El video de capacitación (punto de corte 1 → 3) sirve como referencia visual para la AR y el juego (es material de un tercero, "CHT"; usarlo solo como referencia).

### Implicaciones para RosaNet
- **Pasar a las 3 clases de la finca** (inmaduro / óptimo / pasado) en lugar de 4 etapas genéricas, para que la red hable el idioma del proceso estándar.
- **Datos de la finca = verdad de terreno.** Los públicos (rosas de jardín, otras variedades) solo sirven de apoyo. Mapeo aproximado: `bud`/`1_bud` → inmaduro; `mid-bud`/`2_early_bloom` → óptimo (*dudoso*: verificar con las fotos de la finca); `flower`/`3_full_bloom`/`4_senescence` → pasado.
- La red del robot necesita **detectar** (ubicar las rosas en una escena), no solo clasificar recortes. Las fotos de la finca son de escena, así que con las cajas extraídas de los PDF sirven para ambas cosas.

### Lo que falta y hay que pedir
- **La sanación después del corte no aparece en el material.** Hace falta saber los pasos, los errores típicos y fotos o video.
- Más ejemplos de "Pasado / sobreabierto".
- La definición de los puntos 1 y 4 o 5, si existen en su escala.

## 2.0.2 Robot: AgiBot X2 Ultra con rondas nocturnas

**Decisión del equipo:** el robot es un **AgiBot X2 Ultra** (humanoide) y hace las rondas **de noche o en la madrugada**, cuando no hay operarios en los pasillos.

**Especificaciones (según tiendas y distribuidores; confirmar con AgiBot):**
| | |
|---|---|
| Tamaño | ~1,31 m de alto × 46 cm de ancho × 21 cm; ~39 kg |
| Sensores | LiDAR 3D, cámara RGB-D, RGB estéreo frontal, RGB trasera, micrófonos |
| Cómputo | 2× RK3588 + NVIDIA Orin NX (157 TOPS): puede correr RosaNet a bordo |
| Batería | ~500 Wh, **~2 h a 0,5 m/s**, intercambiable; base de carga automática opcional |
| Velocidad | Normal ≤ 0,8 m/s (máx. 1,8–2 m/s) |
| SDK | AimDK_X2, compatible con ROS (movimiento, percepción y comportamiento) |
| Temperatura | −10 °C a 40 °C |

> Hay discrepancias entre fuentes: la tienda oficial lista una "nueva versión" del X2 Ultra *sin* LiDAR ni RGB-D. Hay que confirmar la configuración exacta de la unidad que vamos a usar.

**Implicaciones de operar de noche:**
- **Ventaja:** no hay operarios en los pasillos (seguridad) y el robot no estorba el trabajo. Además, no hay contraluz del plástico del invernadero, que es uno de los "casos difíciles".
- **La cámara RGB necesita luz propia.** Ninguna especificación menciona visión nocturna. El LiDAR sirve para navegar a oscuras, pero para ver el rojo de la rosa hace falta **iluminación activa** (por ejemplo, un LED frontal o una lámpara montada en el robot). Bien hecho, esto es una ventaja: **luz controlada = color consistente**, y la intensidad del rojo es justamente un criterio de la finca.
- **Diferencia de dominio:** todas las fotos de la finca son de día con luz natural. La red se entrena con fotos de día y el robot verá de noche con luz artificial. Hace falta **tomar fotos de prueba de noche con la misma luz del robot** y medir con ellas. Si no se puede, hay que decirlo como límite.
- **Autonomía:** unas 2 h por carga a 0,5 m/s, unos 3,6 km de recorrido en teoría (menos si se detiene a fotografiar). Hay que calcular cuántas camas cubre por carga y si se necesita la base de carga automática.
- **Altura:** con ~1,3 m, la cámara de la cabeza queda por debajo de las rosas, así que mira hacia arriba, como en las fotos de la finca. Es consistente con los datos de entrenamiento.
- **Ancho:** 46 cm; verificar que cabe y gira en los pasillos entre camas.

Fuentes de las especificaciones: generationrobots.com, robotshop.com, store.agibot.com y rbtx.com (fichas del AgiBot X2 Ultra, consultadas el 2026-10-23).

## 2.0.3 Entrenamiento de la red y resultados (2026-10-23)

### Arquitectura de operación
Foto de escena del robot → **detector** (YOLO11n preentrenado, ajustado para una clase, "rosa") → recorte de cada rosa → **RosaNet** (CNN propia) → inmaduro / óptimo / pasado / *incierta* → reporte por sector (JSON) para el dashboard. Código en `robot/ml/pipeline.py`.

### Datos usados
| Fuente | Uso | Recortes |
|---|---|---|
| Finca (General.zip) | Calibración y **medición** (verdad de terreno) | 69 (47 inmaduras, 20 óptimas, 2 pasadas) |
| Roboflow Rose v1 (Sanjay M) | Preentrenamiento de RosaNet + detector | 2.575 (se descartaron 212 copias en gris) |
| Roboflow floración v8 | Preentrenamiento de RosaNet + detector | ~2.100 |
| Mendeley | **Descartado** | Son escenas con rosas en varias etapas bajo una sola etiqueta |

### Hallazgo clave: los datasets públicos no usan la frontera de la finca
Las clases intermedias públicas (`mid-bud`, `2_Early_Bloom`) son rosas **más abiertas** que el punto óptimo de la finca (punto 3), y el `bud` público mezcla botones cerrados con botones en el punto de la finca. Con un mapeo directo, la red tuvo **83 % de exactitud en los datos públicos, pero solo 25 % en rosas de la finca (0 de 6 óptimas)**.

**Solución: entrenamiento en dos etapas.**
1. **Preentrenamiento** de RosaNet desde cero con los públicos en *su propia* escala (botón / abriendo / abierta / senescente): **86,5 % de exactitud** (macro-F1 0,857) en 430 fotos públicas de prueba.
2. **Calibración** con la finca a sus 3 categorías (se cambia la última capa y se ajusta toda la red). La categoría "pasado" se completa con 40 recortes públicos de rosas abiertas o senescentes.

### Resultados en rosas de la finca (validación cruzada de 5 folds por foto, 64 rosas)
| Variante | Exactitud | Óptimas reconocidas (recall) | Inmaduras marcadas como óptimas |
|---|---|---|---|
| Mapeo directo (sin calibrar) | 25 %* | 0 % | — |
| Calibrada sin preentrenamiento | 73 % | 35 % (6/17) | 4/45 |
| Preentrenada + calibrada, 2 bloques congelados | 69 % | 47 % (8/17) | 9/45 |
| **Preentrenada + calibrada, sin congelar (en uso)** | **75 %** | **59 % (10/17)** | 7/45 |

\* Medido solo con 12 rosas. Los casos difíciles (5 rosas) dan 4/5 en todas las variantes calibradas.

### Límites honestos
- **Muy pocas rosas de la finca:** 64 para la validación cruzada. Los números tienen mucha incertidumbre (±10 puntos o más).
- **"Pasado" no se aprende:** la finca dio 2 ejemplos y ninguno se reconoce. Las públicas abiertas no se parecen a una Freedom "un poco pasada".
- **Error más costoso:** marcar una inmadura como óptima repite la falla más común de la finca (cortar en punto 2). Pasa en 7 de 45 inmaduras. Para mitigarlo, el pipeline marca como *incierta* toda predicción con confianza < 60 %.
- **Todo es de día:** el robot operará de noche con luz artificial (ver 2.0.2).
- **Lo que más mejoraría el modelo:** más fotos de la finca (sobre todo óptimas y pasadas), idealmente tomadas con la cámara y la luz del robot.

### Detector (YOLO11n ajustado, una clase "rosa")
- Se entrenó con los dos datasets públicos (3.778 fotos, 4.959 rosas). Se detuvo en la **época 12 de 35**: cada época tardaba ~8 min porque la GPU llegó a 89 °C y bajó su reloj, y los 4 GB de memoria estaban llenos.
- **Fotos públicas de prueba** (320 fotos, 430 rosas): precisión 0,914, recall 0,891, mAP50 0,959, mAP50-95 0,763.
- **Fotos de la finca** (invernadero, Freedom, desde abajo), contra las 69 rosas marcadas (IoU > 0,2):

| Resolución | Umbral | Rosas marcadas encontradas | Detecciones totales (56 fotos) |
|---|---|---|---|
| 640 px | 0,25 | 28 % | 84 |
| 1024 px | 0,10 | 70 % | 263 |
| **1280 px** | **0,10** | **78 % (en uso)** | 281 |
| 1280 px | 0,05 | 84 % | 483 |

- **Lectura:** el detector aprendió con rosas de jardín fotografiadas de cerca; en el invernadero las rosas son pequeñas y lejanas. A mayor resolución y con un umbral más bajo encuentra casi 4 de cada 5, pero aparecen **falsos positivos** (postes, hojas, una mano). Se filtran las cajas gigantes (> 8 % de la foto). Los demás falsos positivos casi siempre salen como "inmaduro" o "incierta", así que inflan el conteo de inmaduras pero rara vez generan una falsa alarma de "listas para cortar".
- **Mi medición anterior (83 %) estaba inflada:** contaba como encontrada una rosa cubierta por una caja gigante. Se corrigió con IoU.

### Siguiente paso con más impacto
1. **Anotar todas las rosas** de las 56 fotos de la finca (en Roboflow, ~1 h) y ajustar el detector con ellas. Es el cambio que más reduciría los falsos positivos y las rosas perdidas en el invernadero.
2. **Más fotos de la finca** para RosaNet, sobre todo óptimas y pasadas, idealmente con la cámara y la luz del robot de noche.
3. Terminar el entrenamiento del detector (se puede continuar desde `runs/detector/weights/last.pt`) en Colab o con el portátil más ventilado.

## 2.1 Propuesta anterior (v1) — reemplazada por la v2

**Foco del MVP:** app móvil + robot. La VR la trabaja otra parte del equipo, en paralelo y con menor prioridad.

### Núcleo: CNN que clasifica la etapa de apertura
- La CNN **no responde "sí o no"**: clasifica la **etapa de apertura** de la rosa (escala por definir según los datasets, por ejemplo 1 a 5).
- Una **capa de decisión** combina *etapa + días hasta la venta* (y, más adelante, la variedad) y produce la recomendación: "cortar hoy", "esperar ~N días" o "pasada".
- La salida incluye la **confianza** del modelo. Si es baja, el sistema dice "no estoy seguro" y sugiere consultar a un experto o tomar otra foto.

### Componente 1: App móvil (decisión y aprendizaje en el momento del corte)
- Al empezar pregunta **en cuántos días debe estar lista la rosa para la venta**.
- El trabajador toma la foto con el celular y recibe: la etapa, la recomendación, la confianza y **tips**.
- **Tips para formar criterio propio**, para que con el tiempo el trabajador no dependa de la app:
  - Qué rasgos mirar en esa etapa (por ejemplo, separación de los pétalos exteriores, posición de los sépalos, forma del botón).
  - Por qué esta rosa está en esa etapa y no en la siguiente (la comparación con la etapa vecina es donde está la sutileza).
  - Idealmente, un mapa de calor (Grad-CAM) sobre la foto que muestre *dónde* miró la red.
- **Modo práctica (deseable):** el trabajador da su veredicto primero y luego la app revela el suyo y explica la diferencia. Mide su avance con el tiempo.

### Componente 2: Robot de seguimiento en campo (alcance a nivel de finca)
- **Rol:** acompañar y dar seguimiento a los trabajadores que ya están en el campo, y dar a la finca una visión agregada que hoy nadie tiene.
- Recorre las camas, fotografía las rosas, las clasifica con la misma CNN y genera **datos de toda la finca**.
- **Organización por cuadrantes:** la plantación se divide en cuadrantes y el robot reporta toda la información **por cuadrante**.
  - Cada cuadrante tiene un identificador físico que el robot lee al llegar (propuesta: un marcador ArUco o QR, que es barato, robusto y fácil de montar en la demo).
  - Por cada cuadrante reporta: rosas listas para cortar, distribución de etapas, plantas o flores en mal estado y pronóstico para los próximos N días.
  - **Acción física:** al pasar por un cuadrante, el robot señala su estado (por ejemplo, LED verde = hay rosas listas, ámbar = pronto, rojo = revisar una planta mala). Si el hardware lo permite, también apunta o marca la rosa concreta.
  - **Dashboard:** un mapa de la finca en cuadrantes coloreado según el estado, que indica a qué cuadrante enviar a los cortadores hoy. Al hacer clic en un cuadrante se ve su detalle.
  - **En la demo:** una "mini finca" de 2×2 o 3×2 cuadrantes, cada uno con su marcador y algunas rosas o fotos.
- **Dashboard o estadísticas** (ideas):
  - Distribución de etapas por cama o bloque: cuántas rosas hay en cada etapa.
  - **Pronóstico de cosecha:** cuántas rosas estarán en punto de corte en los próximos N días (sale directo de la etapa más el ritmo de apertura).
  - Promedio de cosecha, porcentaje de plantas o flores en mal estado y tendencias.
  - Consistencia del corte: comparar la etapa a la que se cortó con la recomendada, como **retroalimentación al trabajador**, no como vigilancia.
- **Aprendizaje continuo:** las fotos que el robot y los expertos etiquetan alimentan el dataset para reentrenar por lotes.

## 2.2 Datos — evaluación de los datasets (2026-10-23)

### A. Roboflow "Rose" (Sanjay M) — https://universe.roboflow.com/sanjay-m-7nbqj/rose-tk4yv
- **Las 3 URLs (v1, v2, v3) son el mismo proyecto:** 1.099 imágenes originales. Las versiones solo cambian el preprocesado y el aumento de datos (unas 2.637 imágenes con aumento). **Cuenta como un solo dataset.** Hay que descargar una sola versión para no duplicar imágenes.
  - v3: recorte estático del 12 al 88 % (puede cortar rosas en los bordes), rotaciones, saturación y volteos; split 2307/220/110.
- **Tarea:** detección de objetos (cajas). **Clases:** `bud`, `mid-bud`, `flower`.
- **Imágenes:** rosas de jardín al aire libre, de varios colores (roja, rosada, blanca, amarilla), con fondo natural y varias flores por foto. Licencia CC BY 4.0.
- **Sirve para:** **detectar y ubicar rosas** dentro de una foto con varias flores, que es justo lo que necesita el robot al fotografiar un cuadrante. También da una clasificación gruesa en 3 etapas.

### B. Mendeley "Rose Growth Stage" (Kabir & Islam, 2026) — https://data.mendeley.com/datasets/53vyvz5yyk/1
- **Tarea:** clasificación. **Clases:** Early (98), Middle (289) y Final (178), en total 565 imágenes de alta resolución.
- Jardines comerciales en Savar (Bangladesh), luz natural, en campo. Licencia CC BY 4.0.
- **Las etapas no están definidas** en la página: hay que mirar las imágenes para saber si es *apertura de la flor* o *crecimiento de la planta*. Clases desbalanceadas (solo 98 en Early). No indica variedades.

### Veredicto
- **Sirven como punto de partida**, sobre todo el de Roboflow para la detección. **No bastan para decidir el punto de corte de exportación:**
  1. **Granularidad:** 3 etapas gruesas. La decisión de exportación ocurre *dentro* de lo que ellos llaman `bud` / `mid-bud` (botón cerrado frente a pétalos exteriores empezando a soltarse). `flower` (abierta) ya está pasada para exportación.
  2. **Tipo de rosa:** son rosas de jardín. Las de exportación colombianas son híbridos de té de invernadero, con botón alargado, tallo largo y una flor por tallo. La demo seguramente usará rosas comerciales, así que habrá una diferencia de dominio.
  3. **Sin plantas malas:** ninguno trae clases de defectos o enfermedades.
- **Mapeo inicial a una escala común:** `bud` → etapa 1 (cerrada), `mid-bud` → etapa 2 (abriendo; zona de corte), `flower` → etapa 3 (abierta; pasada). El de Mendeley se mapea cuando veamos sus imágenes.

### Plan de datos propuesto
1. **Pipeline en dos pasos:** un detector (YOLO entrenado con Roboflow) ubica cada rosa, se recorta la imagen y una CNN clasificadora asigna la etapa. Sirve igual para la foto de la app (una rosa) y la del robot (varias).
2. **Dataset propio con rosas comerciales (crítico):** comprar ramos de rosas de exportación en botón y **fotografiarlas a intervalos fijos mientras abren en florero** (timelapse). Así se obtiene:
   - Fotos de cada etapa de apertura en el tipo de rosa real.
   - **Verdad de terreno de "días hasta abrir"** para cada foto, lo que alimenta directamente la regla *etapa + días hasta la venta*.
   - Evidencia concreta para el criterio de Validación del pitch.
3. **Prueba honesta:** reservar rosas propias que el modelo nunca vea y medir con ellas la exactitud y la matriz de confusión.
4. **Dataset C — Roboflow "食用玫瑰花期检测"** (detección de etapas de floración de rosa comestible): https://universe.roboflow.com/yolo-lmnpo/-zkger. 2.101 imágenes, CC BY 4.0, clases `1_Bud`, `2_Early_Bloom`, `3_Full_Bloom` y `4_Senescence`. Aporta la etapa senescente. También es rosa no comercial.
5. Pendiente: buscar un dataset de enfermedades de la hoja de rosa para "plantas malas".

---

## 3. Análisis inicial de la propuesta v0

### Fortalezas
- **Ataca el problema real** (criterio tácito y poco consistente): convierte el ojo del experto en datos etiquetados.
- **La pregunta de "días hasta la venta" es un diferenciador fuerte.** Refleja que el punto de corte depende del destino y del tiempo de transporte, no solo de cómo se ve la flor. Es el tipo de comprensión del problema que el jurado valora.
- **El aprendizaje continuo con expertos** responde directamente a "el conocimiento vive en quien enseña": el experto enseña a la máquina una vez y la máquina enseña a muchos.
- Cubre los tres ángulos del reto: aprender (VR), interpretar (CNN) y decidir (app y robot).

### Riesgos y puntos débiles
1. **Alcance demasiado grande para 20 horas.** Son tres productos más una CNN. La simulación en VR es la parte más costosa: modelar en 3D rosas realistas en varias etapas de apertura puede comerse todo el tiempo sola.
2. **El papel del robot es la pregunta más peligrosa del jurado.** Si el robot "solo ve y toma fotos", hace lo mismo que la app con un celular, y el jurado dirá que es accesorio (se pierden puntos en Pertinencia). El robot necesita una **razón física** para existir y una **acción** sobre el entorno.
3. **Los datos.** Hay pocas bases públicas de *etapas de apertura o punto de corte* de rosas (la mayoría clasifican especies, como Oxford Flowers 102). Además, el punto de corte depende de la variedad y del criterio de cada finca, así que una base genérica no va a coincidir con las rosas que nos pongan en la demo. **Hay que verificar en Roboflow, Kaggle y artículos qué existe** y planear tomar fotos propias.
4. **Una respuesta de "sí o no" no enseña criterio.** Si la app solo dice "lista / no lista", el trabajador nuevo no aprende *por qué*. El reto pide desarrollar criterio, no depender de una caja negra.
5. **Incertidumbre.** Dos expertos pueden discrepar; el modelo también debería poder decir "no estoy seguro" en lugar de dar una respuesta falsa con confianza.
6. **Aprendizaje continuo real en 20 horas.** Reentrenar de forma automática en vivo es poco realista. Se puede demostrar el *flujo* (el experto etiqueta, la foto entra al dataset, se reentrena por lotes) sin que ocurra en vivo.

### Recomendaciones de ajuste (por discutir)
- **La CNN clasifica la etapa de apertura (por ejemplo, 1 a 5), no "sí o no".** Una capa de reglas sencilla, configurable por variedad, combina *etapa + días hasta la venta* y produce la decisión. Es más explicable, se ajusta por variedad sin reentrenar y hace que la pregunta de los días tenga un efecto real.
- **Explicar la decisión:** mostrar un mapa de calor (Grad-CAM) de *dónde* miró la red y un texto corto con el porqué (por ejemplo, "pétalos exteriores separándose: etapa 3"). Eso convierte la herramienta en un tutor y no solo en un juez.
- **Darle al robot un trabajo que el celular no hace bien.** Opciones:
  - *Estación de captura estandarizada:* una cámara en un servo o brazo que rodea la rosa y toma varias vistas (arriba, lateral, 360°) con **luz controlada**. Elimina la variación de ángulo e iluminación, que es justo lo que hace que dos personas lean distinto la misma flor.
  - *Señalización física:* el robot **apunta o ilumina** (láser o LED) la rosa que está en punto de corte, o la marca. Actúa sobre el entorno y enseña en el lugar.
  - *Modo práctica:* el trabajador nuevo da su veredicto primero y luego el robot revela el suyo y explica la diferencia. Se pasa de "dime la respuesta" a "pon a prueba tu criterio".
- **Priorizar el alcance:**
  - **Imprescindible:** CNN + robot (captura y señalización) + interfaz mínima con el veredicto y el porqué.
  - **Deseable:** app móvil con la pregunta de los días y el modo práctica.
  - **Opcional o concepto:** VR. Mostrarla como maqueta, video o escena mínima (fotos reales en un visor), o dejarla como "siguiente paso".
- **Generar evidencia desde la hora 1:** separar un conjunto de prueba que el modelo nunca vea, medir la exactitud y la matriz de confusión por etapa, registrar los casos en que falla y anotar los supuestos que cambian. Eso alimenta los criterios de Funcionamiento (25) y Validación (10).

---

## 4. Preguntas abiertas
- [ ] **(v2)** ¿Cuándo y dónde se usa la tablet si no se permiten celulares? (¿sala de capacitación, solo para entrenamiento?)
- [x] **(v2)** ¿Cómo define la finca *muy pronto*, *punto óptimo* y *muy tarde*? → Punto 3 = óptimo (ver sección 2.0.1). Variedad Freedom.
- [ ] **(v2)** ¿En qué consiste la sanación de la planta después del corte? **No viene en el material de la finca; hay que pedirlo.**
- [x] **(v2)** ¿RosaNet pasa a 3 clases (las de la finca)? → Sí, ya está hecho.
- [ ] **Robot:** ¿qué configuración exacta tiene nuestro X2 Ultra (LiDAR, RGB-D)? ¿Tendremos el robot físicamente en el hackatón?
- [ ] **Robot:** ¿qué iluminación lleva para la ronda nocturna? ¿Podemos tomar fotos de prueba de noche con esa luz?
- [ ] **Datos:** la finca dio 69 rosas marcadas (47 inmaduras, 20 óptimas y 2 pasadas). Es muy poco para entrenar desde cero; hacen falta los datasets públicos y, ojalá, más fotos de la finca.
- [ ] **(v2)** Dashboard: ¿qué tecnología usamos y cómo le llegan los datos del robot?
- [ ] ¿Qué hardware tenemos o podemos conseguir? (cámara, Raspberry Pi, ESP32 o Arduino, chasis con ruedas, servos, LEDs o láser, Meta Quest)
- [ ] ¿Tendremos rosas reales para fotografiar y probar? ¿De qué variedades?
- [ ] **Revisar los 3 datasets del equipo:** etiquetas (¿etapas de apertura?), cantidad de imágenes por clase, variedades, ángulos e iluminación, licencia. ¿Se pueden unificar en una sola escala de etapas?
- [ ] ¿Cuántas etapas usamos y cómo se definen? (hace falta una definición visual por etapa, que es además la base de los tips)
- [ ] La regla *etapa + días hasta la venta → decisión*: ¿de dónde salen los valores? (literatura, consulta a una finca o supuesto explícito)
- [ ] "Plantas malas": ¿se detectan con la misma CNN (una clase extra, "defectuosa") o con otro modelo? ¿Hay datos para eso?
- [ ] Robot: ¿cómo se mueve en la demo (ruedas, riel, empujado a mano)? ¿Qué acción física ejecuta además de fotografiar? (por ejemplo, LED o láser que marque la rosa lista o una alerta sobre una planta mala)
- [ ] Para la demo: ¿cómo recorre el robot unas "camas" simuladas en el espacio de la presentación?
- [ ] ¿Quién del equipo programa y en qué lenguajes? Reparto: CNN y datos, app, robot y hardware, dashboard, VR, pitch y validación.

## 5. Registro de decisiones
| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-23 | La propuesta v0 gira en torno a una CNN con robot, app y VR | Idea inicial del equipo |
| 2026-10-23 | La CNN clasifica **etapa de apertura**, no "sí o no"; una capa de decisión combina etapa + días hasta la venta | Más explicable, ajustable por variedad, y le da efecto real a la pregunta de los días |
| 2026-10-23 | La app da **tips** para que el trabajador aprenda a identificar las etapas por sí mismo | El reto pide desarrollar criterio propio, no depender de una caja negra |
| 2026-10-23 | Las fotos del momento del corte se toman con la **app móvil** | El celular ya está en la mano del trabajador |
| 2026-10-23 | El **robot** es de **seguimiento en campo**: recorre, clasifica y genera estadísticas a nivel de finca | Le da al robot un valor que el celular no tiene: escala, cobertura y datos agregados |
| 2026-10-23 | MVP = app + robot; la VR avanza en paralelo con menor prioridad | El equipo de 5 se divide el trabajo |
| 2026-10-23 | **Red propia (RosaNet)** entrenada desde cero en PyTorch, con escala común de 4 etapas (botón cerrado, apertura inicial, abierta, senescente) | El equipo quiere diseñar y entrenar su propia red; 4 etapas porque el dataset de floración trae senescencia |
| 2026-10-23 | **Cambio de alcance (v2):** tres áreas, Meta Quest (AR 2D de entrenamiento), app tablet (juego del proceso estándar y la sanación) y robot (detección por sectores + dashboard) | La empresa no permite celulares a los operarios |
| 2026-10-23 | Repo dividido en `metaquest/`, `app-tablet/` y `robot/`; la red neuronal vive en `robot/ml/` | Una carpeta por área de trabajo del equipo |
| 2026-10-23 | **RosaNet pasa a las 3 categorías de la finca** (inmaduro / óptimo / pasado); los tips salen de la "Información técnica" de la finca | Hablar el mismo idioma que el proceso estándar; los archivos de la finca son la referencia |
| 2026-10-23 | Las cajas de la finca se extraen automáticamente de los círculos de los PDF (`robot/ml/finca_labels.py`); los casos difíciles van a test | Ahorra la anotación manual y separa una prueba de robustez |
| 2026-10-23 | Robot = **AgiBot X2 Ultra**, con rondas **nocturnas o de madrugada** | No hay operarios en los pasillos; hace falta iluminación activa para la cámara |
| 2026-10-23 | El robot trabaja **por cuadrantes**: identifica cada cuadrante, reporta su estado y lo señala físicamente | Da una unidad de gestión clara a la finca ("¿a dónde mando a cortar hoy?") y una acción visible del robot |

## 6. Bitácora de supuestos y aprendizajes (para el pitch de validación)
| Supuesto inicial | ¿Se mantuvo? | Qué observamos |
|---|---|---|
| Hay bases de datos públicas suficientes de punto de corte | **No** | Los datasets encontrados tienen solo 3 etapas gruesas, son de rosas de jardín y no traen defectos. Sirven para la detección y una base de etapas, pero hacen falta fotos propias de rosas comerciales |
| Una foto basta para decidir el punto de corte | Por verificar | |
| La finca enviaría recortes de rosas listos para entrenar | **No** | Envió fotos de escena con la rosa marcada en un PDF; hay que convertir esas marcas en cajas |
| Las 3 categorías tendrían ejemplos parecidos en cantidad | **No** | Inmaduro 37, Óptimo 18, Pasado 2 |
| El trabajador nuevo confía más si la app le da un veredicto | Por verificar | |
