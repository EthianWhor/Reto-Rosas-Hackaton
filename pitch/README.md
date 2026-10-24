# Pitch — borrador v1 (para corregir)

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

## Evidencia: lo que ya funciona

Sale del trabajo del equipo en `robot/` (en `main`: CONTEXTO.md 2.0.3; en la rama `A`:
`robot/PLAN_robot_rosas_X2.md`, la simulación y el envío del reporte). Es el material de los bloques
de demo y de validación.

**Cómo ve el robot:** foto de la escena → **detector** (YOLO11n ajustado, una clase "rosa") → recorte
de cada rosa → **RosaNet** (CNN propia) → inmaduro / óptimo / pasado / *incierta* → reporte por cuadrante.

| Pieza | Resultado | Lectura para el pitch |
|---|---|---|
| RosaNet con mapeo directo de datos públicos | 83 % en fotos públicas, **25 % en rosas de la finca** (0 de 6 óptimas) | **Aprendizaje clave:** el "botón" y el "abriendo" de los datasets públicos no coinciden con el punto 3 de la finca. El criterio es de la finca, no genérico |
| RosaNet en dos etapas (preentrenada con públicos + calibrada con la finca) | **75 % de exactitud** en rosas de la finca (validación cruzada, 64 rosas); reconoce **10 de 17 óptimas**; 4 de 5 casos difíciles | Pasó de 25 % a 75 % con solo 64 rosas de la finca. Más fotos de la finca = mejor modelo, y el robot es justamente el que las consigue |
| Seguridad del modelo | Marca como **"incierta"** toda predicción con confianza < 60 % | No inventa: lo dudoso va a revisión de un experto |
| Detector de rosas | mAP50 0,959 en fotos públicas; encuentra **78 %** de las rosas marcadas en las fotos del invernadero (1280 px) | Funciona, pero las rosas del invernadero son pequeñas y lejanas: hay que ajustarlo con fotos de la finca |
| RosaNet "noche" (aumento de fondo oscuro, en `main`) | Con fondo oscuro como de noche, la versión de día bajaba a **52 %** y marcaba como óptimas **~25 de 45** inmaduras. La versión noche sube a **75,5 %** y baja ese error a **~7 de 45**; de día pierde ~3,5 puntos | **Validación que convence:** detectamos que el robot se equivocaría de noche, encontramos la causa (el fondo, no la luz sobre la rosa) y lo corregimos con datos. Falta medir con fotos reales de noche |
| Ajustes de la red (3 semillas por ajuste) | Ningún ajuste mejora más que la variación entre semillas (±4 puntos); completar "pasado" con fotos públicas sí suma +28 | **El límite ya son los datos, no el modelo.** Por eso el robot que toma fotos cada noche es la pieza clave |
| Simulación del X2 Ultra en MuJoCo (rama `A`) | Ronda nocturna completa por un invernadero (20 camas de 30 m, caminos de 0,8 m), con el modelo real del equipo sobre fotos de la finca, reporte Excel + JSON por cuadrante y envío al dashboard cuando vuelve el WiFi. Cobertura de rosas vistas: **de 73 % a ~95 %** | El sistema completo corre de punta a punta sin el robot físico |
| Estado nuevo **"lista mañana"** (rama `A`) | Punto 2 avanzado que llegará al punto 3 en ~1 día | Pronóstico: la finca planea el corte de mañana, no solo el de hoy |
| Prioridad por cuadrante (rama `A`) | `puntaje = óptimas + 0,5 × lista mañana`; prioridad alta con 3 o más óptimas; orden 1, 2, 3… | Es exactamente lo que muestra la pantalla turnero: "ve primero al cuadrante INV1-C07-T3" |

**Límites que decimos nosotros:** "pasado" no se aprende (solo 2 ejemplos); 7 de 45 inmaduras se
marcan como óptimas, que es la falla más costosa (cortar en punto 2); la noche está simulada
oscureciendo el fondo de fotos de día y falta medir con fotos reales de noche; los números tienen
±10 puntos de incertidumbre por las pocas fotos.

## Guion propuesto (10 min)

| Min | Bloque | Qué decimos o mostramos | Criterio que ataca |
|---|---|---|---|
| 0:00 | **Gancho** | Foto de dos rosas casi iguales: punto 2 y punto 3. "¿Cuál cortarían?" (dejar que el jurado falle). "En la finca, **12 de cada 100 rosas** se cortan fuera de punto, y la falla más común es esta." | Comprensión de la necesidad |
| 0:45 | **Problema** | El criterio es tácito y se aprende en el cultivo: la inducción dura **15 a 18 días** y la teoría es solo **2 o 3**; el resto es práctica al lado de un experto. La decisión de hoy se ve en días y dos personas leen distinto la misma rosa. **Hoy la finca no tiene datos del campo:** sus drones solo se usan para pruebas y no guardan nada. | Necesidad |
| 1:45 | **Persona** | "Marta, 3 semanas en la finca" y "Don Luis, 15 años cortando, que pierde tiempo enseñando". | Necesidad, ética |
| 2:15 | **Solución** | El diagrama de arriba: aprender → practicar → decidir, con un solo cerebro. | Integración |
| 3:00 | **DEMO EN VIVO** (3–4 min) | 1) **Modo foto:** el jurado elige una rosa o una foto y el pipeline (detector + RosaNet) la clasifica con su porqué, o dice "incierta". 2) **Ronda del X2 en la simulación** → el reporte JSON llega al dashboard y aparece en la pantalla turnero ("ve primero al cuadrante INV1-C07-T3; mañana, al C04"). 3) Juego de práctica en la app. 4) VR, aunque sea en video. | Funcionamiento (25 + 30 %) |
| 6:30 | **Por qué un robot** | Ve desde abajo, como la cámara se entrenó; trabaja de noche sin estorbar; con la luz LED del campo el color es constante; cubre el campo entero cada noche con el mismo criterio y deja fotos como evidencia; actúa (informa por voz, pantalla y LED, señala con el brazo). | Pertinencia |
| 7:15 | **Negocio** | Un robot para empezar; un robot por campo después. Inversión, retorno y payback en una diapositiva con 3 números. | Negocio, viabilidad |
| 8:15 | **Visión 360** | Personas primero (no reemplaza: forma y orienta), mantenimiento, datos y ética. | Impacto y ética |
| 8:45 | **Validación y límites** | Qué supusimos y qué cambió: los datasets públicos servían (no: 25 % en la finca → entrenamiento en dos etapas → 75 %); la red funcionaría igual de noche (no: 52 % con fondo oscuro → aumento de fondo → 75,5 %); celulares (no se permiten → pantallas comunes); drones (no guardan datos). Qué medimos y qué falta (ver "Evidencia"). | Validación |
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
| ¿Con 69 fotos entrenaron una red? | No desde cero: se preentrenó con ~4.700 rosas públicas y se calibró con las de la finca. Pasó de 25 % a 75 % de exactitud en la finca. Lo dudoso sale como "incierta". El robot existe justamente para conseguir miles de fotos etiquetadas. |
| Si los operarios aciertan el 88 % y RosaNet el 75 %, ¿para qué la red? | La red no reemplaza el ojo del cortador: **cuenta y prioriza** el campo entero cada noche (a dónde ir), algo que hoy nadie hace. El que decide qué cortar sigue siendo la persona, y la app y la VR existen para subir ese 88 %. La red mejora con cada ronda y cada corrección del experto; la meta es superar el 88 %, y lo decimos como meta, no como logro. |
| ¿Qué pasa cuando el modelo se equivoca? | Lo que tiene confianza baja va a una lista de "dudosas" que revisa un experto en la app; su respuesta reentrena el modelo. La decisión final de cortar siempre es de la persona. |
| ¿Cuánto cuesta y cuándo se paga? | Ver la diapositiva de negocio: si el error baja de 12 % a 9 %, el primer robot se paga en ~14 meses (con supuestos explícitos y condicionado a la velocidad de la ronda). |

## Qué necesitamos decidir como equipo

- [ ] ¿Nos gusta el nombre "Punto 3"? ¿Otro?
- [ ] ¿Qué mostramos del robot en vivo: el X2 físico, el simulador (MuJoCo) o una mini finca con cámara? (define el bloque de 3–4 min y tiene que caber en ~10 h)
- [ ] ¿Cómo se identifica el trabajador en la pantalla turnero: nombre, código o carné?
- [ ] **¿Qué acción física hace el robot?** (pregunta de "Pertinencia", 15 pts). La rama `A` recomienda: en la demo, girar la cabeza e iluminar cada rosa en punto 3; como siguiente paso, esperar en la entrada de los cuadrantes de prioridad alta y señalarlos con el brazo cuando llegan los operarios.
- [ ] **Velocidad real de la ronda** (decide el negocio, ver `inversion-y-retorno.md` sección 2): la simulación para cada 1,25 m y avanza ~0,1 m/s en promedio; las cuentas del negocio suponen ~0,6 m/s fotografiando en movimiento.
- [ ] Las gafas (Meta Quest) todavía no están en el repo: cuando lleguen, tienen que verse y hablar igual que la app (mismas categorías, fotos y estilo).
- [ ] ¿Cuándo se une la rama `A` (simulación y envío del reporte) a `main`?
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
- [ ] El proceso de **sanación** de la planta después del corte.
- [ ] ¿El video de capacitación de "CHT" es de GHT? ¿Qué relación tiene la finca con GHT?
