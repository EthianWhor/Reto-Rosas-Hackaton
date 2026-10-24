# Corte y sanación de la rosa — investigación para RoseApp y la VR

> Versión 1, 2026-10-24. Base para el módulo **Sanación** de la app y para la simulación en Meta Quest.
> **Importante:** esto sale de manuales y literatura general sobre rosa de corte (Colombia, Ecuador,
> México, España, EE. UU. y Australia). **El protocolo de la finca manda:** cada finca define su altura
> de corte, su desinfectante y su forma de "sanar". Lo marcado con 🏠 hay que confirmarlo con la finca
> antes de ponerlo en la app (lista de preguntas al final).
>
> **Decisión del equipo (2026-10-24):** mientras no se pueda preguntar a la finca, usamos esta versión
> como el proceso de trabajo. Lo que nos contaron se parece, aunque no será exacto. Ya está en la app
> (`app-tablet/src/data/sanacion.ts`); cuando la finca responda, se ajusta ahí.

## 1. El proceso completo, en orden

| # | Paso | Qué se hace | Por qué |
|---|---|---|---|
| 1 | Alistarse | Guantes, tijera afilada y **desinfectada** | Una tijera sucia lleva hongos (*Botrytis*) y bacterias (*Agrobacterium*) de planta en planta |
| 2 | Elegir la rosa | Solo la que está en **punto 3** (caracol con centro visible, rojo vivo, forma de copa) | Cortar en punto 2 es la falla más común de la finca |
| 3 | Elegir dónde cortar | Sobre una **hoja de cinco foliolos**, normalmente la **segunda** contando desde abajo del tallo floral | Ahí está la yema que dará el próximo tallo |
| 4 | Elegir la yema | La más **hinchada**, con la hoja más perpendicular al tallo, **mirando hacia afuera** | Da un tallo largo y fuerte; hacia afuera deja el centro de la planta aireado |
| 5 | Cortar | En **bisel** (~45°), **pegado a la yema** (unos 5 mm arriba), con la parte alta del bisel del lado de la yema | El agua escurre y no se pudre la yema; sin tocón largo que se seque |
| 6 | Sacar el tallo | Retirarlo **por arriba**, sin rozar otras flores; **nunca ponerlo en el suelo** | Las espinas dañan otros botones; el suelo contamina |
| 7 | Hidratar | Al balde de inmediato, o a la sala de poscosecha **antes de 20 minutos** | Pasado ese tiempo los vasos del tallo se taponan; si pasa, hay que recortar la base |
| 8 | Sanar la planta | Revisar el corte, quitar residuos, hojas secas y tallos débiles; seguir el protocolo de la finca para la herida 🏠 | La herida es la puerta de entrada de *Botrytis* |
| 9 | Desinfectar otra vez | Al cambiar de cama o bloque, y **siempre** después de tocar una planta enferma | Cortar la cadena de contagio |

## 2. Detalle de cada parte

### 2.1 Desinfección de la tijera
- **Productos usados en cultivos:** alcohol al 70 %, amonio cuaternario o hipoclorito (lejía) al 10 %. El
  hipoclorito corroe el metal si se deja mucho tiempo; el amonio cuaternario no corroe.
- **Cuándo:** al entrar a cada cama o bloque, y siempre después de cortar una planta enferma.
- **Buena práctica:** trabajar con **dos tijeras** y alternarlas: mientras una está en el desinfectante,
  se usa la otra.
- En rosa se probaron desinfectantes comerciales contra *Botrytis*: reducen mucho el hongo en las primeras
  horas, pero la protección baja con los días. La desinfección es continua, no de una sola vez.
- 🏠 **Cuál usa la finca, en qué dosis y cada cuánto.**

### 2.2 Dónde cortar
- **Siempre sobre una hoja de cinco foliolos** (pentafoliada). Las hojas de abajo (de uno o tres foliolos)
  tienen yemas puntiagudas que dan tallos cortos.
- **Lo usual:** justo encima de la **segunda** hoja de cinco foliolos. Si el tallo es largo y fuerte, se
  puede cortar sobre la tercera, y así quedan más cortes antes de tener que bajar la planta.
- **Dejar en el tallo que queda 2 o 3 yemas con hojas completas**, para que la planta siga alimentándose.
- **Nivel de corte (lo decide el jefe de cultivo antes de cortar):**
  - *De mantenimiento:* a la altura de siempre.
  - *Subiendo:* dejando más yemas, para que la planta recupere follaje.
  - *Bajando:* más cerca de la base, para buscar tallos más largos; puede provocar más brotes basales.
  - Cortar en el "nudillo" (*knuckle*) o por debajo sirve para controlar la altura, pero en muchas
    variedades baja la calidad.
- 🏠 **A qué altura corta la finca la Freedom y si cambia según la época** (por ejemplo, antes de un pico
  como San Valentín).

### 2.3 Hacia qué lado (orientación de la yema)
- La regla general es dejar la **yema mirando hacia afuera de la planta**, no hacia el centro: así el
  nuevo tallo crece hacia afuera, el centro queda aireado (menos hongos) y no se cruzan tallos.
- **El equilibrio importa:** las plantas crecen más del lado con más luz, y si un lado se carga, la
  planta se desbalancea. Por eso se busca una estructura abierta y pareja, con los tallos repartidos.
- Lo que nos contaron de la finca encaja con esto: **si siempre se corta hacia el mismo lado, la planta
  se carga y puede caerse.** En la práctica significa ir **repartiendo los cortes** entre los lados de la
  planta. 🏠 *No encontramos esta regla escrita en los manuales: hay que pedirle a la finca cómo la
  enseñan (por ejemplo, alternar de un corte al siguiente, o mirar qué lado está más cargado).*

### 2.4 Cómo es el corte
- **En bisel**, de unos 45°.
- **Pegado a la yema**, unos 5 mm por encima. Si se deja un **tocón** largo, ese pedazo se seca, muere y
  se vuelve entrada de hongos.
- **La parte alta del bisel va del lado de la yema**, para que el agua escurra hacia el otro lado y no
  se quede sobre ella.
- Un solo movimiento, con tijera afilada: **sin desgarrar ni aplastar** el tallo.

### 2.5 Después de cortar: el tallo
- **Nunca** dejar la flor en el suelo.
- **Hidratar de inmediato** o antes de 20 minutos. Si pasa más, recortar la base antes de meterla al agua.
- **Solución de hidratación:** agua limpia con un germicida (por ejemplo, unos 50 ppm de cloro) y un
  **pH cercano a 5**, que es donde la rosa absorbe mejor. Baldes con 20 a 30 cm de agua. Los productos
  comerciales de hidratación vienen con pH de 4,5 a 5.
- No dejar los tallos al sol mientras se termina la cama.
- En poscosecha la flor pasa a **cuarto frío, a unos 2-4 °C**.
- El transporte del campo a poscosecha es donde más se maltratan hojas y botones: cuidado con los carros.

### 2.6 Después de cortar: la planta ("sanación")
No encontramos una definición estándar de "sanación" en los manuales: es la palabra de la finca. Por lo
que encontramos, lo que se hace sobre la planta después del corte para que rebrote sana incluye:
- **Revisar el corte:** limpio, en bisel, sin tocón largo y sin desgarro. Si quedó mal, rehacerlo.
- **Retirar residuos:** hojas y flores secas, pedazos de tallo y restos de poda. La FAO recomienda
  sacarlos siempre, porque ahí crecen *Oidium* y *Botrytis*.
- **Quitar tallos débiles, ciegos o enfermos** (poda fitosanitaria).
- **Proteger la herida:** hay pastas **cicatrizantes** y **sellantes** con fungicida (en Colombia se
  venden para frutales y ornamentales), pero **no encontramos evidencia de su uso estándar en rosa de
  corte**. 🏠 *Si la finca aplica un producto en el corte ("gel" o pasta), hay que conocer cuál, cómo y
  cuándo; debe estar registrado ante el ICA.*
- **Plantas con agallas** (*Agrobacterium*, que entra por las heridas): no se cortan con la misma tijera
  sin desinfectarla, y se reportan.

### 2.7 Otras labores que el operario va a oír
| Labor | Qué es |
|---|---|
| **Pinch (despunte)** | Cortar la punta de un tallo joven (por ejemplo, un basal a 40-60 cm) para que no florezca y la planta forme tallos laterales |
| **Desbotone** | Quitar los botones laterales y dejar solo el central (más o menos una vez por semana) |
| **Desyeme / desbrote** | Quitar yemas o brotes que no se quieren |
| **Agobio** | Doblar hacia abajo un tallo (descabezado) sin quebrarlo, para que las hojas sigan alimentando la planta |
| **Basal** | Tallo fuerte que nace de la base de la planta; es el futuro de la producción |

## 3. Errores típicos (base para el juego "¿qué está mal?")
1. Cortar una rosa en **punto 2** (cerrada).
2. Cortar **sobre una hoja de tres foliolos** o muy abajo, sin dejar yemas con hoja completa.
3. Dejar la **yema mirando hacia adentro** de la planta.
4. Cortar **siempre hacia el mismo lado** y cargar la planta. 🏠
5. Dejar un **tocón** largo sobre la yema.
6. Corte **recto o desgarrado**, o el bisel al revés (el agua escurre hacia la yema).
7. **No desinfectar** la tijera entre camas o después de una planta enferma.
8. Poner la flor **en el suelo**.
9. Tardar más de **20 minutos** en hidratarla.
10. No retirar **residuos y hojas secas** de la cama.

## 4. Cómo lo llevamos a RoseApp y a la VR (propuesta)

**Módulo Sanación de la app (para aprendices):**
- **Ordena los pasos:** arrastrar las 9 tarjetas del proceso en orden (sección 1).
- **¿Dónde cortarías?:** foto o dibujo de un tallo con sus hojas; el operario toca el punto de corte
  correcto (encima de la segunda hoja de cinco foliolos). Se puede dibujar en 2D, sin fotos.
- **¿Qué está mal?:** una imagen con un error (tocón largo, yema hacia adentro, flor en el suelo…) y
  cuatro opciones.
- **Verdadero o falso** rápido con los datos clave (20 minutos, pH 5, dos tijeras…).
- Con el mismo estilo del juego actual: pétalos al acertar, racha y puntos.

**VR (Meta Quest, para inducción):**
- Simular el corte en una planta 2D o 3D sencilla: elegir hoja, yema y lado, y cortar con el gesto.
- El instructor ve si el operario desinfectó la tijera, si dejó tocón y si llevó la flor al balde a tiempo.

## 5. Preguntas para la finca (cuando estén disponibles)
- [ ] ¿Qué es exactamente "sanación" para ustedes? ¿Qué pasos tiene y en qué orden?
- [ ] ¿Aplican algún producto en el corte ("gel", pasta cicatrizante)? ¿Cuál, cómo y cuándo?
- [ ] ¿Con qué desinfectan la tijera, en qué dosis y cada cuánto? ¿Usan dos tijeras?
- [ ] ¿Sobre qué hoja cortan la Freedom (segunda, tercera pentafoliada)? ¿Cambia por época?
- [ ] ¿Cómo enseñan a no cortar siempre hacia el mismo lado? ¿Hay una regla?
- [ ] ¿Cuánto tiempo máximo puede estar el tallo fuera del agua? ¿Hidratan en el campo o en poscosecha?
- [ ] ¿Usan malla o capuchón para proteger el botón al transportarlo?
- [ ] ¿Cuáles son los errores que más ven en los nuevos?
- [ ] ¿Tienen fotos o video de un corte bien hecho y de uno mal hecho?

## Fuentes
- [Cultivo de Rosas para Exportación (Calvache, ResearchGate)](https://www.researchgate.net/publication/320387356_Cultivo_de_Rosas_para_Exportacion): tipos de corte, desinfección de la tijera, orientación de la yema.
- [El secreto de las rosas: labores de cultivo (blog técnico)](https://manejodelasrosas.blogspot.com/2011/06/labores-de-cultivo.html): hoja pentafoliada, yema perpendicular, bisel, hidratación antes de 20 minutos, corte subiendo y bajando.
- [Infoagro: el cultivo de las rosas para corte](https://infoagro.com/flores/flores/rosas2.htm): 2-3 yemas, heridas y *Botrytis*, desinfección de herramientas, *Agrobacterium*, cuarto frío.
- [Técnicas de formación y manejo del rosal (Redalyc)](https://www.redalyc.org/pdf/1932/193225911005.pdf) y [labores culturales (U. Técnica del Norte)](https://repositorio.utn.edu.ec/bitstream/123456789/8142/1/03%20AGP%20231%20TRABAJO%20DE%20GRADO.pdf): pinch, desbotone, agobio.
- [Greenhouse roses for cutflower production (DPIRD, Australia)](https://library.dpird.wa.gov.au/cgi/viewcontent.cgi?article=1168&context=bulletins): corte sobre la segunda o tercera hoja de cinco foliolos, nudillo.
- [NC State: poda de rosa en invernadero](https://hortscans.ces.ncsu.edu/file/../uploads/i/n/investig_5592dec20f88d.pdf) y [Illinois Extension: poda](https://extension.illinois.edu/roses/pruning): yema hacia afuera, 45°.
- [Evaluación de desinfectantes contra Botrytis en rosa (ResearchGate)](https://www.researchgate.net/publication/334576912_Evaluacion_de_tres_desinfectantes_contra_el_moho_gris_causado_por_Botrytis_cinerea_en_el_cultivo_de_rosa) y [INYM: desinfección de herramientas](https://inym.org.ar/noticias/produccion-sustentable/79436-desinfeccion-el-primer-paso-antes-de-la-cosecha.html).
- [UC Davis: rosas, poscosecha](https://postharvest.ucdavis.edu/es/produce-facts-sheets/rosas), [Estado del arte de la poscosecha en Colombia](https://www.researchgate.net/publication/269995957_Estado_del_arte_de_la_poscosecha_de_flores_de_corte_en_Colombia) y [ficha Chrysal](https://www.chrysal.com/sites/default/files/ps_chrysal_solucion_inicial.pdf): pH 5, 50 ppm de cloro, 4 °C.
- [FAO: manejo integrado de enfermedades](https://www.fao.org/4/a1374s/a1374s05.pdf): retirar hojas y flores secas.
- [Cikatreezan (cicatrizante en Colombia)](https://agroactivocol.com/producto/sanidad-vegetal-alimentos-saludables/coadyuvantes-y-reguladores-fisiologicos/cicatrizante-hormonal/): ejemplo de producto, no específico de rosa.
- [Cámara de Comercio de Bogotá: Manual Flores y Follajes 2015](https://bibliotecadigital.ccb.org.co/server/api/core/bitstreams/5d1965e0-a6cf-49e3-be57-76ba2408b640/content): cosecha con tijera afilada, nunca en el suelo.
