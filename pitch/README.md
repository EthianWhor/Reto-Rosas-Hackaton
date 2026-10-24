# Pitch — borrador v2 (para corregir)

> **Versión 2, 2026-10-24:** evidencia con los números finales del robot y del modelo, solo datos
> comprobables, y el negocio recalculado con la velocidad medida del robot.
>
> Versión 1, 2026-10-23 (noche). Recoge las correcciones del equipo sobre la v0: un solo robot,
> recorrido línea por línea, iluminación LED en el campo, la app en pantallas comunes tipo turnero y
> los drones de la finca, que no guardan datos.
> Las cifras están en [inversion-y-retorno.md](inversion-y-retorno.md), la investigación y las fuentes en
> [investigacion.md](investigacion.md) y la visión 360 en [vision-360.md](vision-360.md).
> **Todavía no tenemos los datos de la finca:** los números marcados con ❓ se actualizan cuando las
> dueñas respondan (lista al final de este archivo).

## Datos del evento que condicionan el pitch

- **10 minutos**, formato *elevator pitch*, ante jurados que envían las empresas.
- **Ficha técnica** (título, descripción y beneficios) antes del **sábado 24 de octubre a las 3:00 p. m.**, junto con el demo del prototipo funcional.
- La presentación debe incluir el **objetivo inicial, el nivel de consecución, las ventajas y desventajas y las tecnologías usadas**.
- Quedan **unas 10 horas** de trabajo: el alcance del demo tiene que caber ahí (los drones quedan fuera).
- Hay **dos rúbricas** y hay que cubrir ambas:

| Rúbrica general (términos del evento) | % | Rúbrica del reto (CONTEXTO.md) | Pts |
|---|---|---|---|
| Integración tecnológica en el prototipo | 30 | Funcionamiento y evidencia | 25 |
| Relevancia, impacto y ética | 20 | Pertinencia (por qué el robot) | 15 |
| Viabilidad y escalabilidad técnica | 20 | Creatividad e innovación | 15 |
| Innovación y diferenciación | 10 | Presentación (pitch) | 15 |
| Uso estratégico y justificación de la IA | 10 | Comprensión de la necesidad | 10 |
| Modelo de negocio y pitch | 10 | Experiencia de uso | 10 |
| | | Validación y aprendizaje | 10 |

**Lectura:** el demo y la integración pesan más que cualquier diapositiva. El negocio y la ética
suman, pero el jurado premia ver las piezas funcionando y conectadas.

## La idea en una frase

> **"Punto 3"**: un sistema que convierte el ojo del cortador experto en un estándar que se aprende,
> se practica y se mide. Un robot recorre el campo de noche, línea por línea, y en la mañana le dice
> a cada trabajador a dónde ir. La app y la realidad virtual entrenan a las personas para reconocer
> el punto de corte por sí mismas.

(La app ya se llama **RoseApp**: rosa, rojo y blanco, con práctica tipo Duolingo. "Punto 3" sigue
como propuesta para el sistema completo; si prefieren, todo puede llamarse RoseApp.
"Punto 3" es el punto de corte de la finca y el nombre lo entiende
cualquier operario.)

## El ecosistema: un cerebro y tres piezas

```
                    ┌──────────────────────────────────────────┐
                    │  CEREBRO: RosaNet + base de conocimiento │
                    │  (fotos etiquetadas, criterio de la finca,│
                    │   proceso de corte y sanación)            │
                    └──────────────────────────────────────────┘
          ▲ datos nuevos      │ mismo criterio     │ mismo criterio
          │                   ▼                    ▼
 ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
 │ ROBOT X2 Ultra  │  │ ROSEAPP          │  │ META QUEST (VR)  │
 │ Ronda nocturna  │→ │ Pantallas tipo   │  │ Inducción y      │
 │ línea por línea │  │ turnero + juego  │  │ evaluación con   │
 │ y por cuadrante │  │ de práctica      │  │ instructor       │
 └─────────────────┘  └──────────────────┘  └──────────────────┘
   DECIDIR (finca)       ORIENTAR Y PRACTICAR   APRENDER (operario nuevo)
```

1. **Aprender: realidad virtual (Meta Quest).** Inducción del operario nuevo. Simula la cama, el
   recorrido, la lectura del botón, el corte y la sanación. El instructor ve y evalúa lo que hace
   el operario. Un error en VR no cuesta una rosa.
2. **Orientar y practicar: RoseApp en pantallas comunes.** No es un celular en la mano del
   operario mientras corta. Es una **tablet común o una pantalla tipo turnero de banco**, fija a la
   entrada del invernadero o en el lugar de trabajo:
   - **Turnero del día:** el trabajador se identifica (nombre o código) y ve a qué cuadrante y a qué
     líneas ir según el reporte del robot. La pantalla de la entrada muestra el mapa del campo.
   - **Reporte para todos:** el reporte del robot llega a **todos los trabajadores registrados** en
     la app y a los coordinadores.
   - **Juego de práctica:** rondas cortas con fotos reales de la finca y explicación inmediata, en las
     pausas o en la sala de formación, para **mecanizar** el criterio hasta que salga solo.
3. **Decidir: robot AgiBot X2 Ultra.** Recorre el campo de noche **línea por línea**: avanza por la
   línea sin girar dentro de ella, da la vuelta en la cabecera (donde hay más espacio) y entra a la
   siguiente. El campo tiene **iluminación LED blanca**, así que la cámara ve el color real de la
   rosa. Por cada cuadrante cuenta los botones en punto 3, detecta los pasados y las plantas con
   problemas, mide el ambiente y entrega el reporte en la mañana: *"Cuadrante 4: 30 rosas listas hoy"*.
4. **Cerebro común:** RosaNet (3 categorías de la finca) + una base de conocimiento a la que se le
   puede **preguntar** (el robot responde por voz con LinkSoul; la app, por texto). Cada ronda del
   robot y cada corrección de un experto **alimentan** la base: el sistema mejora con el uso.

**Por qué es un sistema y no tres productos:** las tres piezas hablan el mismo idioma (inmaduro /
punto 3 / pasado), usan las mismas fotos y el mismo criterio, y los datos del robot se vuelven
material de entrenamiento para las personas. **El experto enseña una vez y el sistema enseña a
cientos.**

## Evidencia: lo que ya funciona (todo medido, nada de ejemplo)

> Actualizado 2026-10-24 con el cierre del robot (`robot/DEMO.md`, `robot/PLAN_robot_rosas_X2.md` 4.5 y
> 7.13) y del modelo (CONTEXTO.md, "Detector de noche", "Concordancia entre personas" y "Forma y color").
> **Regla del equipo: en la presentación solo van datos comprobables.** La app ya muestra el reporte real
> que el robot subió a Supabase (`INV1_2026-10-24_090237`), con las fotos reales de sus 29 rosas dudosas.

**Cómo ve el robot:** foto de la escena → **detector** (YOLO11n ajustado, una clase "rosa", versión de
noche) → recorte de cada rosa → **RosaNet** (CNN propia) + **forma y color** (10 rasgos que traducen el
criterio de la finca) → inmaduro / óptimo / pasado / *dudosa* → reporte por cuadrante → Supabase → RoseApp.

**El problema, medido por nosotros:** una integrante del equipo que asistió a la explicación de la finca
clasificó 69 rosas que la finca ya había clasificado. **Coincidieron en 24 de 69 (35 %)**, y ella llamó
"óptimas" a la mitad de las inmaduras. Una explicación no basta para transmitir el criterio: eso es
exactamente lo que dice el reto, y es la razón de la app, la VR y un modelo que aplique siempre el mismo criterio.

| Pieza | Resultado medido | Lectura para el pitch |
|---|---|---|
| RosaNet con datos públicos directos | 83 % en fotos públicas, **25 % en rosas de la finca** | El criterio es de la finca, no genérico |
| RosaNet en dos etapas (públicos + finca) | **75 %** en rosas de la finca (validación cruzada, 64 rosas) | De 25 % a 75 % con solo 64 rosas de la finca |
| RosaNet "noche" | Con fondo de noche, la versión de día caía a **52 %**; la de noche, **75,5 %** | Vimos que fallaría de noche, encontramos la causa y lo corregimos |
| **Forma + RosaNet (en uso)** | **77 % de día y 77 % de noche**; óptimas reconocidas de día de 43 % a **61 %** sin subir el error más caro | 10 números medibles (copa, alto/ancho, rojo) casi igualan a la red y son **explicables**: "copa abierta, rojo vivo → óptima" |
| Detector de noche | De noche encuentra el **55 %** de las rosas (el de día, 22 %) | La noche es simulada: falta medir con la luz del robot |
| **Ronda completa en la simulación** (20 camas de 30 m, 6.031 rosas) | **95 %** de las rosas vistas, **0 %** contadas dos veces, **0,4 %** falsas; ubica cada rosa con **0,5 cm** de error en altura y **0,9 cm** en el metro de la cama | El robot cuenta y ubica el invernadero entero, rosa por rosa |
| Con fotos reales de la finca y el modelo del equipo | Encuentra **71–73 %**; clase correcta **74–80 %**; **0 inmaduras** mandadas a "cortar hoy" | El error más caro (cortar en punto 2) no aparece; lo dudoso va a revisión |
| Tamaño de la cabeza como segunda opinión | Si la red dice "óptima" pero la cabeza es muy chica o muy grande, va a dudosa: pasadas en "cortar hoy" de **6–7 a 0–3** por ronda, sin perder óptimas | Dos opiniones independientes antes de mandar a cortar. Umbrales de la simulación: falta calibrarlos con rosas reales |
| Duración y batería | Ronda completa: **2 h**, con 1 vuelta a la base al 25 % de batería, y sigue donde quedó | Medido con el robot simulado, no supuesto |
| Acción física | Apunta la cabeza e ilumina cada óptima de los **10 cuadrantes que se cosechan primero**: 211 rosas, ronda de **2 h 18 min**. Señalarlas todas toma 4 h 46 min (~5,3 s por rosa) | Decidimos con la medición, no a ojo |
| Obstáculos | Frena, espera 30 s, sigue si lo quitan o abandona el camino y lo anota | |
| Reporte en vivo | El robot subió su ronda a Supabase con las fotos de 29 dudosas; la app reparte el turno con ese reporte y el experto revisa esas fotos | Los tres sistemas conectados de verdad |
| Ajustes de la red | Ningún ajuste mejora más que el ruido entre semillas (±4 puntos) | **El límite son los datos**: por eso un robot que toma fotos cada noche |

**Límites que decimos nosotros (antes de que pregunten):**
- **Todo el robot es simulación.** Del SDK del X2 Ultra salen riesgos concretos: cámara de 1280 × 720 (la
  cobertura baja de 90 % a 68 %), la cabeza del modelo original no se inclina y no trae foco.
- **La noche es simulada:** oscurecimos fotos de día; faltan fotos reales de noche con la luz del robot.
- **Pasadas:** la finca dio solo 2 fotos; con la segunda opinión del tamaño, en la simulación todavía 0–3 pasadas por ronda salen como óptimas.
- **Las rosas de la simulación son fotos con las que se entrenó el modelo:** los números del robot con fotos
  reales son optimistas. Los de validación cruzada (75–77 %) son los honestos.
- **RosaNet (77 %) está por debajo del ojo del operario (88 %):** su papel es contar y priorizar, no decidir el corte.

## Guion v2 (10 min) — el orden acordado

**Orden:** problema → cómo lo abordamos → prototipo conectado → beneficios en números → costos → fácil
implementación → cierre. **Foco:** lo que más vende es el **software**: RoseApp y la red (RosaNet + forma y
color) que conecta todo. El robot es la prueba de que la red funciona en el campo, no el producto principal.
**Regla:** cada número se dice como **medido** (lo mostramos) o como **proyectado** (supuesto explícito).

| Min | Bloque | Qué decimos | Números |
|---|---|---|---|
| 0:00 | **1. Problema** | "¿Cuál de estas dos rosas cortarían?" (punto 2 y punto 3; dejar que el jurado falle). El punto de corte es un criterio que vive en la cabeza del experto: se aprende en 15–18 días al lado de alguien, y ni así se transmite bien. La finca no tiene datos de su campo. | 🏠 12 de cada 100 rosas se cortan fuera de punto · 🏠 inducción de 15–18 días, solo 2–3 de teoría · **medido: tras la explicación de la finca, una integrante del equipo coincidió en 24 de 69 rosas (35 %)** |
| 1:30 | **2. Cómo lo abordamos** | Convertir el ojo del experto en un **criterio digital** (la red) y usarlo en dos frentes: **formar** a las personas (RoseApp + VR) y **orientarlas** cada mañana (el robot cuenta el campo de noche). Un solo cerebro, el mismo idioma: inmaduro, punto 3, pasado. | Diagrama del ecosistema |
| 2:30 | **3. Prototipo conectado (demo, ~3,5 min)** | En vivo y conectado de verdad: **(a)** RoseApp: coordinación ve el turno repartido con el reporte real del robot; un aprendiz practica y ve su progreso; módulo de Sanación. **(b)** La red: el jurado pone una rosa frente a la webcam y la red la clasifica o dice "dudosa". **(c)** El experto clasifica en la app la **foto real** que tomó el robot de una rosa dudosa: esa respuesta reentrena la red. **(d)** 30 s del robot simulado haciendo la ronda. | Red: de 25 % a **77 %** en rosas de la finca, de día y de noche · 0 inmaduras mandadas a cortar · robot: 95 % de las rosas, 0 repetidas |
| 6:00 | **4. Beneficios en números** | Lo que la finca gana y **cómo lo va a ver medido en la propia app**. | Ver "Cifras para la finca" abajo |
| 7:15 | **5. Costos** | Dos paquetes. **Formación** (RoseApp + VR + red) en toda la finca. **Robot piloto** en un bloque. | Formación: ~USD 6.600 + 8.000/año → **payback ~3 meses** (base) · Robot: ~USD 63.400, piloto |
| 8:15 | **6. Fácil implementación** | Tablets comunes en la entrada (sin celulares en el cultivo), la nube ya funciona, el alta de un trabajador toma un minuto con un código, y cada trabajador crea su PIN. Para una variedad nueva solo se etiquetan fotos de esa variedad. | Piloto de 8 semanas en un campo |
| 9:15 | **Cierre** | "El experto enseña una vez; RoseApp enseña a cientos y le dice a cada trabajador dónde cortar hoy." Qué pedimos: el piloto. | |

### Cifras para la finca: medido vs. proyectado

| Medido hoy (lo podemos mostrar) | Proyectado (supuesto, lo mide el piloto) |
|---|---|
| Línea base de la finca: 88 % de acierto 🏠 | Bajar el error de 12 % a 9 % (base) |
| Acuerdo tras una explicación: 35 % (24 de 69) | Inducción de ~16 a ~11 días |
| Red: 25 % → 77 % en rosas de la finca; 0 inmaduras a "cortar hoy" | Formación: payback ~3 meses (base), ~11 meses (conservador) |
| Robot simulado: 95 % de las rosas, ubicadas al centímetro, en 2 h por invernadero | Sistema completo: ~14 meses si el robot fotografía en movimiento |
| La app ya guarda cada respuesta del juego por persona en Supabase y cada etiqueta del experto | La finca ve, por trabajador y por categoría, si su acierto sube del 88 % |

**Cómo lo demostramos en el piloto:** la app ya registra cada ronda de práctica por persona (aciertos por
categoría y con qué se confunde). Antes y después del piloto se compara: acierto de cada operario, días de
inducción y error en el corte medido por la finca. Así el beneficio deja de ser un supuesto.

## Guion v1 (referencia)

| Min | Bloque | Qué decimos o mostramos | Criterio que ataca |
|---|---|---|---|
| 0:00 | **Gancho** | Foto de dos rosas casi iguales: punto 2 y punto 3. "¿Cuál cortarían?" (dejar que el jurado falle). "En la finca, **12 de cada 100 rosas** se cortan fuera de punto, y la falla más común es esta." | Comprensión de la necesidad |
| 0:45 | **Problema** | El criterio es tácito y se aprende en el cultivo: la inducción dura **15 a 18 días** y la teoría es solo **2 o 3**; el resto es práctica al lado de un experto. **Lo medimos:** una integrante del equipo escuchó la explicación de la finca y después coincidió con la finca en solo **24 de 69 rosas (35 %)**. **Hoy la finca no tiene datos del campo:** sus drones solo se usan para pruebas y no guardan nada. | Necesidad, validación |
| 1:45 | **Persona** | "Marta, 3 semanas en la finca" y "Don Luis, 15 años cortando, que pierde tiempo enseñando". | Necesidad, ética |
| 2:15 | **Solución** | El diagrama de arriba: aprender → practicar → decidir, con un solo cerebro. | Integración |
| 3:00 | **DEMO EN VIVO** (3–4 min, guion en `robot/DEMO.md`) | 1) **Ronda del X2 en la simulación** (`--ventana`): camina en serpiente, frena ante la caja, apunta e ilumina las óptimas, vuelve a la base y sube el reporte. 2) **RoseApp:** el reporte real llega, coordinación ve el reparto del turno, cada trabajador ve sus cuadrantes y el experto clasifica **la foto real** de una rosa dudosa. 3) **Modo foto:** el jurado pone una rosa o foto frente a la webcam; si duda, dice "dudosa" y no adivina. 4) Juego de práctica y Sanación en la app; VR, aunque sea en video. | Funcionamiento (25 + 30 %) |
| 6:30 | **Por qué un robot** | Ve el botón de lado y desde abajo; trabaja de noche sin estorbar; recorre el invernadero entero (95 % de las rosas, 0 repetidas) y ubica cada rosa al centímetro; deja la foto como evidencia; **actúa**: apunta e ilumina las óptimas de los cuadrantes que se cosechan primero. | Pertinencia |
| 7:15 | **Negocio** | Dos paquetes: la **formación** (app + VR) se paga sola en meses en toda la finca; el **robot** entra como piloto en un bloque y escala cuando capture en movimiento. Números en `inversion-y-retorno.md`. | Negocio, viabilidad |
| 8:15 | **Visión 360** | Personas primero (no reemplaza: forma y orienta), mantenimiento, datos y ética. | Impacto y ética |
| 8:45 | **Validación y límites** | Qué supusimos y qué cambió: los datasets públicos servían (no: 25 % en la finca → dos etapas → 75 %); la red funcionaría igual de noche (no: 52 % → aumento de fondo → 75,5 %; con forma y color, 77 % de día y de noche); explicar el criterio bastaba (no: 35 % de acuerdo); el robot podría señalar todas las óptimas (no: 4 h 46 min → solo los 10 primeros cuadrantes); el robot iría a 0,6 m/s (no: con paradas para fotos va a ~0,09 m/s → el negocio se separó en dos paquetes); celulares (no se permiten → pantallas comunes). | Validación |
| 9:30 | **Cierre** | "El experto enseña una vez. Punto 3 enseña a cientos y le dice a cada trabajador dónde cortar hoy." + qué pedimos (piloto de 8 semanas en un campo). | Pitch |

## Preguntas difíciles que el jurado probablemente hará

| Pregunta | Respuesta corta que proponemos |
|---|---|
| ¿Por qué un humanoide de USD 43.000 y no cámaras fijas o drones? | La finca ya tiene drones y **no le sirven para esto**: no guardan datos ni se usan para muestreo. Un dron ve desde arriba; el robot ve el botón de lado y desde abajo (sépalos, copa, caracol), que es lo que define el punto 3. Las cámaras fijas no escalan a miles de camas. Y el robot habla con las personas y señala físicamente. A futuro los drones pueden sumarse a la misma base de datos. |
| ¿Cómo se mueve el robot entre las camas? | Recorre cada línea de punta a punta sin girar dentro de ella; da la vuelta en la cabecera, donde hay espacio, y entra a la siguiente. Como ve las dos camas a cada lado, puede ir por un pasillo sí y otro no. |
| ¿Funciona de noche? | Sí: el campo tendrá **iluminación LED blanca**, que además da un color constante (la intensidad del rojo es criterio de corte). Hay que validar RosaNet con fotos tomadas con esa luz, porque las fotos actuales son de día. |
| ¿Un robot alcanza? | Para empezar, sí: un robot por finca en el piloto y **un robot por campo** cuando el piloto demuestre el valor. La cuenta está en `inversion-y-retorno.md`. |
| ¿Los operarios van a usar celular? | No. La finca no lo permite y no hace falta: la app vive en pantallas comunes tipo turnero a la entrada del invernadero y en la sala de formación. |
| ¿No reemplaza trabajadores? | No corta rosas. Les quita el trabajo de adivinar a dónde ir, acelera la curva de aprendizaje y libera al experto para enseñar lo difícil. |
| ¿Con 69 fotos entrenaron una red? | No desde cero: se preentrenó con ~4.700 rosas públicas y se calibró con las de la finca (25 % → 75 %), y se combinó con 10 rasgos de forma y color (77 % de día y de noche). Lo dudoso sale como "dudosa". El robot existe justamente para conseguir miles de fotos etiquetadas. |
| Si los operarios aciertan el 88 % y RosaNet el 77 %, ¿para qué la red? | La red no reemplaza el ojo del cortador: **cuenta y prioriza** el campo entero cada noche (a dónde ir), algo que hoy nadie hace. El que decide qué cortar sigue siendo la persona, y la app y la VR existen para subir ese 88 %. La meta es superar el 88 %, y lo decimos como meta, no como logro. |
| ¿Qué pasa cuando el modelo se equivoca? | Lo dudoso va a la lista de "Rosas dudosas" de la app con la foto que tomó el robot; un experto la clasifica y esa respuesta queda guardada para reentrenar el modelo. Ya funciona con el reporte real. |
| ¿Por qué no señala todas las rosas? | Lo medimos: señalar cuesta ~5,3 s por rosa y llevaría la ronda a 4 h 46 min. Señala solo en los 10 cuadrantes que se cosechan primero (2 h 18 min). |
| ¿Cuánto cuesta y cuándo se paga? | Dos respuestas honestas: la formación (app + VR, ~USD 6.600) se paga en meses en toda la finca. El robot (~USD 63.000) hoy, con la velocidad medida, cubre ~0,55 ha por noche: entra como piloto y se paga cuando capture fotos en movimiento (a 0,3–0,6 m/s, entre ~14 meses y ~2,4 años). |
| ¿Qué tan lento es el robot? | En la simulación para cada 1,25 m a tomar 4 fotos: ~0,09 m/s en promedio, 2 h por invernadero de 20 camas de 30 m. Caminar es solo ~4 s de cada ~14 s por parada; el resto son las fotos. Ahí está la mejora. |

## Qué necesitamos decidir como equipo

- [ ] ¿Nos gusta el nombre "Punto 3"? ¿Otro?
- [ ] ¿Qué mostramos del robot en vivo: el X2 físico, el simulador (MuJoCo) o una mini finca con cámara? (define el bloque de 3–4 min y tiene que caber en ~10 h)
- [ ] ¿Cómo se identifica el trabajador en la pantalla turnero: nombre, código o carné?
- [x] **Acción física:** apuntar la cabeza e iluminar las óptimas de los 10 primeros cuadrantes (medido: 2 h 18 min, 211 rosas).
- [x] **Velocidad real de la ronda:** medida en la simulación, ~0,09 m/s (2 h por invernadero). Cambia el negocio: ver `inversion-y-retorno.md` sección 2.
- [x] **Negocio en dos paquetes** (formación en toda la finca + robot piloto): aceptado por el equipo (2026-10-24).
- [ ] Las gafas (Meta Quest) todavía no están en el repo: cuando lleguen, tienen que verse y hablar igual que la app (mismas categorías, fotos y estilo).
- [x] La rama `A` (simulación y envío del reporte) ya está en `main`.
- [ ] ¿Quién presenta cada bloque?

## Datos pendientes de la finca (preguntar cuando las dueñas estén disponibles)

Con estas respuestas se cambian los ❓ por datos reales en `inversion-y-retorno.md`:

- [ ] Hectáreas en rosa, número de campos e invernaderos, y largo y número de líneas por campo. (**Todavía no hay medidas.**)
- [ ] Ancho de los pasillos y de las cabeceras (donde gira el robot).
- [ ] Número de operarios de cultivo y de cortadores; rotación anual y temporales por temporada.
- [x] Acierto en el punto de corte: **~88 % de las flores; ~12 % de error** (dato de la finca, 2026-10-23).
- [ ] Qué pasa con una flor cortada fuera de punto: ¿baja de grado, va a nacional o se descarta? ¿Cuánto vale menos? (hoy suponemos ~1/3 del valor)
- [x] Duración de la inducción: **15 a 18 días**, de los cuales la teoría son **2 o 3** (dato de la finca, 2026-10-23).
- [ ] Cuánto tarda un cortador, después de la inducción, en llegar a su meta de tallos por hora.
- [ ] Cómo hacen hoy el conteo o la proyección de cosecha (quién, cada cuánto, cuántas horas).
- [ ] El proceso de **sanación** de la planta después del corte. Mientras tanto usamos la versión investigada (`contenido/corte-y-sanacion.md`), que ya está en la app.
- [ ] ¿El video de capacitación de "CHT" es de GHT? ¿Qué relación tiene la finca con GHT?
