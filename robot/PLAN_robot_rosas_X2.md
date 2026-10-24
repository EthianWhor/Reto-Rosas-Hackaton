# Plan: AgiBot X2 Ultra detectando rosas listas para corte

Robot que camina de noche por un invernadero de rosas rojas (variedad Freedom), analiza las rosas, dice cuáles están listas para cortar, dónde están y a qué altura. Al final arma un reporte por cuadrante (Excel + JSON) y lo envía al **dashboard** del proyecto cuando encuentra WiFi.

> Estado: **plan, todavía no implementado.**
> Primero se hace en **simulación (MuJoCo)**. El código queda separado para cambiar a **robot real** con un solo ajuste en la configuración.
> **Alcance de este plan:** solo la parte del robot. La red neuronal (RosaNet, `robot/ml/`) la hace otra persona del equipo; aquí solo se **conecta** y no se modifica.

---

## Índice

0. [Respuestas y supuestos](#0-respuestas-y-supuestos)
1. [Qué hace el sistema (resumen)](#1-qué-hace-el-sistema-resumen)
2. [Estados de la rosa: inmaduro, óptimo, pasado y lista mañana](#2-estados-de-la-rosa)
3. [Cómo ve rosas de 2 m sin hardware extra](#3-cómo-ve-rosas-de-2-m-sin-hardware-extra)
4. [Invernadero, cuadrantes y ruta](#4-invernadero-cuadrantes-y-ruta)
5. [Caminar por un camino estrecho y difícil](#5-caminar-por-un-camino-estrecho-y-difícil)
6. [Noche y luz](#6-noche-y-luz)
7. [Conexión con RosaNet (el modelo del equipo)](#7-conexión-con-rosanet-el-modelo-del-equipo)
8. [Eficiencia: varias rosas por foto](#8-eficiencia-varias-rosas-por-foto)
9. [Ubicación, altura y no contar dos veces la misma rosa](#9-ubicación-altura-y-no-contar-dos-veces)
10. [Reporte Excel y JSON para el dashboard](#10-reporte-excel-y-json-para-el-dashboard)
11. [Envío al cuartel general sin WiFi constante](#11-envío-al-cuartel-general-sin-wifi-constante)
12. [Estructura del repo y cómo armarlo](#12-estructura-del-repo-y-cómo-armarlo)
13. [La simulación paso a paso](#13-la-simulación-paso-a-paso)
14. [Modo robot real](#14-modo-robot-real)
15. [Fallas y recuperación](#15-fallas-y-recuperación)
16. [Pruebas y métricas](#16-pruebas-y-métricas)
17. [Cronograma de 10 horas](#17-cronograma-de-10-horas)
18. [Riesgos y decisiones pendientes](#18-riesgos-y-decisiones-pendientes)
19. [Preguntas para el equipo del modelo y para el dashboard](#19-preguntas-para-el-equipo-del-modelo-y-para-el-dashboard)

---

## 0. Respuestas y supuestos

### Lo que respondiste

| # | Tema | Respuesta |
|---|------|-----------|
| 1 | Ancho del camino | **80 cm** |
| 2 | Tamaño del invernadero | Se inventa (ver supuestos) |
| 3 | Cuadrante | **Tramo de 5 m de cama** |
| 4 | Variedades | **Solo rosas rojas** (Freedom) |
| 5 | Piso | Puede ser **difícil** (tubos, mangueras, desniveles) |
| 6 | Misión | **Solo detectar**, no corta |
| 7 | Horario | **De noche** |
| 8 | Frecuencia | **1 ronda por noche**, todo el invernadero |
| 9 | Estados | **Inmaduro, óptimo (punto 3), pasado, lista mañana** (explicados en la sección 2) |
| 10 | Reporte | Lugar y altura de las listas + conteo por cuadrante |
| 11 | Cuartel general | **Dashboard** que hace otra persona del equipo (vista de coordinadores + pantalla a la entrada del campo, CONTEXTO.md sección 2.0) |
| 12 | WiFi | No es constante: **guardar y enviar** al encontrar WiFi |
| 13 | Formato | **Excel** (para personas) + **JSON** con los mismos datos (para que el dashboard lo lea fácil) |
| 14 | Alcance | **Simulación** ahora, dejarlo listo para el robot real |
| 15 | Tiempo | **10 horas**. Tú haces el robot, otra persona el dashboard |
| 16 | Hardware | **Ninguno extra**: resolverlo con zoom o posturas |
| 17–18 | Modelo IA | RosaNet, en `robot/ml/` de este mismo repo. Lo hace otra persona. Aquí solo se **conecta** (sección 7) |

### Supuestos inventados (se cambian en `config/config.yaml`)

| Dato | Valor supuesto |
|------|----------------|
| Invernaderos | 1 |
| Camas | 20 |
| Largo de cada cama | 30 m |
| Ancho de cada cama | 1,0 m |
| Camino entre camas | 0,8 m |
| Pasillo principal (cabecera de camas) | 1,5 m |
| Altura de las rosas | 1,0 m a 2,0 m |
| Tramos por cama | 30 / 5 = **6** |
| Cuadrantes en total | 20 × 6 = **120** |
| Caminos que recorre el robot | 21 (uno a cada lado de cada cama) |

### Lo que salió del zip

- **Información técnica**: variedad Freedom. **Punto de corte = punto 3**: el caracol está definido y se ve el centro, el rojo es vivo e intenso y la flor tiene forma de copa. El error más común es cortar en **punto 2**: cabeza más pequeña, rojo más oscuro y sépalos pegados a los pétalos.
- **Fotos**: 37 de inmaduro, 18 de punto óptimo, 2 de pasado y 8 de casos difíciles. **8 fotos se repiten en varias carpetas** (8, 16, 25, 26, 28, 45, 47, 63), porque en una foto salen rosas en estados distintos. Por eso el sistema analiza **varias rosas por foto**.
- **Videos**: muestran pasillos estrechos con rosas más altas que una persona, la vista de lado, la vista al camino y la explicación de los puntos de corte (forma triangular, centro visible).
- **`Párrafo de Loop.loop`**: está vacío (es un acceso a Microsoft Loop). No se usó.
- **Medidas del robot** (sacadas del modelo de MuJoCo, `X2-Ultra.xml`):
  - Cámara de la cabeza a **~1,19 m** del piso (medido en la simulación con el robot de pie; antes se había anotado 1,24 m).
  - Hombros: **~58 cm** de ancho. Las fichas de las tiendas dicen **46 cm** (CONTEXTO.md 2.0.2). Se usa **58 cm**, que es lo más conservador, hasta medir el robot real.
  - Cabeza: inclinación de −0,40 a +0,49 rad (unos 23° hacia arriba) y giro de ±0,49 rad (28°).
  - Cintura: ±0,31 rad de inclinación (18°) y giro de −3,4 a +2,1 rad.

### Lo que ya se sabe del X2 Ultra (CONTEXTO.md 2.0.2, confirmar con AgiBot)

| Dato | Valor | Qué cambia en el plan |
|------|-------|-----------------------|
| Batería | ~500 Wh, **~2 h a 0,5 m/s**, intercambiable | La ronda de ~95 min cabe, pero con poco margen (sección 4.4) |
| Cómputo | NVIDIA Orin NX (157 TOPS) | RosaNet corre **a bordo durante la ronda**; el análisis al volver a la base queda solo como respaldo (sección 8) |
| Sensores | LiDAR 3D, RGB-D, RGB estéreo frontal | El LiDAR sirve para ir centrado en el camino y ver obstáculos, también a oscuras (sección 5) |
| SDK | AimDK_X2, compatible con ROS | Es lo que se llena en `real_backend.py` (sección 14) |
| Velocidad normal | ≤ 0,8 m/s | 0,3 m/s del plan está muy por debajo: seguro |

> **Ojo:** la tienda oficial lista una "nueva versión" del X2 Ultra **sin LiDAR ni RGB-D**. Si la unidad es esa, se usa el plan B sin profundidad (sección 9.2) y la odometría + marcas para ir centrado.

### Lo que ya existe en el repo y se reutiliza

| Qué | Dónde | Uso en este plan |
|-----|-------|------------------|
| Modelo del robot | `robot/X2-Ultra.xml` + `robot/meshes/` | Ya está copiado. No hace falta traerlo de Descargas |
| Script de 10 plantas | `robot/referencias/jardin_10_plantas.py` + `scene_jardin.xml` | Base del caminar con punto guía (mocap + `weld`), la cámara de la cabeza y la exclusión cabeza-torso |
| RosaNet | `robot/ml/` (`predict.py`: `RosePredictor`) | Se importa directo desde el adaptador (sección 7). **No se modifica** |
| Fotos de la finca recortadas | `app-tablet/assets/rosas/` (1_inmaduro, 2_optimo, 3_pasado) | Texturas de los "carteles" en la simulación (sección 7.4) |

---

## 1. Qué hace el sistema (resumen)

```
 [Base / cargador]
       │ 1. arranca de noche (hora configurable)
       ▼
 [Recorre camino por camino en serpiente]
       │ 2. para cada 1,25 m
       │ 3. toma 4 fotos (izq media, izq alta, der media, der alta)
       │ 4. encuentra TODAS las rosas candidatas de cada foto (máscara roja / oráculo)
       │ 5. recorta cada una y la clasifica con RosaNet (inmaduro / óptimo / pasado)
       │ 6. calcula cama, metro y altura de cada rosa
       │ 7. junta duplicados (la misma rosa vista en varias fotos)
       │ 8. decide "lista mañana" entre las inmaduras
       │ 9. guarda avance por tramo (si se cae, sigue donde iba)
       ▼
 [Fin de ronda]
       │ 10. arma reporte_YYYY-MM-DD.xlsx + reporte_YYYY-MM-DD.json
       │ 11. los deja en la carpeta "bandeja de salida"
       ▼
 [Cuando hay WiFi]
         12. los envía al dashboard y los marca como enviados
```

El código se divide en piezas. Cada pieza tiene una versión **sim** y una **real**:

| Pieza | Simulación | Robot real |
|-------|-----------|------------|
| Caminar | punto guía (como ya hicimos) | controlador oficial de AgiBot |
| Cámara | render de MuJoCo | cámara RGBD de la cabeza |
| Encontrar rosas (candidatas) | "oráculo" (la verdad de MuJoCo) o máscara roja | máscara roja (o el detector del equipo, si lo entrega) |
| Clasificar cada rosa | "oráculo" o RosaNet sobre carteles con fotos reales | RosaNet |
| Ir centrado en el camino | la da MuJoCo | LiDAR / profundidad |
| Posición del robot | la da MuJoCo | odometría + marcas en las camas |
| WiFi | simulado (se prende al volver a la base) | revisa la conexión real |

### 1.1 Acción física: señalar las rosas óptimas (hecho)

Para que se note por qué es un robot y no solo una cámara: después de las 4 fotos de cada parada, el robot
**apunta la cabeza a cada rosa óptima nueva y la ilumina con un foco angosto** (1,5 s). Quien pase por el
camino ve en el momento qué rosas cortar. Es la propuesta de ejemplo; **el equipo puede elegir otra** y se
cambia en un solo lugar (`Cuerpo.senalar` y `accion` en el config; `accion.tipo: ninguna` la apaga).

- **Cuáles:** las que salen "óptimo" con las mismas reglas del reporte (solo seguras; las dudosas no). Una rosa
  vista desde dos paradas se señala una sola vez (radio de 8 cm, guardado en el checkpoint, así también al
  seguir una ronda interrumpida).
- **Cómo apunta:** gira la cintura hacia la rosa y reparte la inclinación entre cabeza y cintura. Después mide
  con la pose real de la cámara dónde quedó la rosa y corrige (hasta 6 veces, solo el 60 % de la corrección
  vertical: la cintura también mueve la cámara y con una rosa cerca la corrección completa oscila). Espera 1 s
  entre correcciones: con menos, mide con la cámara todavía moviéndose y queda corrida. Queda a menos de
  ~30 px del centro de la foto (unos 2 cm a 1 m).
- **Alcance:** cabeza + cintura suben como máximo ~41°. Una rosa de 2 m justo encima del robot no se puede
  centrar: el foco queda cerca y se cuenta como "fuera de alcance" en la hoja Ronda.
- **Tiempo (simulación, 20 m de camas, 65 óptimas):** la ronda pasa de 7,2 a 12,6 min, unos 5 s por rosa.
  En un invernadero con muchas óptimas esto suma; se puede bajar `accion.segundos` o señalar solo las del
  lado del camino que se cosecha primero.
- **Arreglo que salió de aquí:** con la cintura girada, el hombro del robot quedaba delante del sensor de
  obstáculos (las piezas visuales del robot están en el mismo grupo que la escena) y salía un obstáculo
  fantasma. Ahora el sensor salta las piezas del robot y, al terminar cada parada, el robot vuelve a la
  postura neutra antes de caminar.
- **En el robot real:** falta decidir el foco (un LED blanco angosto en la cabeza) y probar los tiempos de la
  cabeza y la cintura del X2.

---

## 2. Estados de la rosa

Variedad **Freedom**, roja. RosaNet da una de las **3 categorías del proceso estándar de la finca** por cada rosa (`robot/ml/stages.py`). Son los mismos nombres que usan el juego de la tablet y el dashboard, así que el robot también los usa:

| Nombre en el código y el reporte | Clase de RosaNet | Puntos de la finca |
|----------------------------------|------------------|--------------------|
| `inmaduro` | `1_inmaduro` | punto 1 y punto 2 |
| `optimo` | `2_optimo` | punto 3 |
| `pasado` | `3_pasado` | sobreabierta |

Encima de eso, el robot aplica unas reglas para decidir **"lista mañana"** (`lista_manana`), que es un subconjunto de las inmaduras.

### 2.1 Inmaduro (punto 1–2, cerrado) – NO cortar

**Cómo se ve:**
- La cabeza es **más pequeña** y alargada, como una bala.
- El rojo es **más oscuro**, casi vino tinto.
- Los **sépalos van pegados** a los pétalos y todavía la abrazan.
- No se ve el centro desde arriba. Los pétalos están apretados.

**Qué hace el robot:** la cuenta como `inmaduro`. **No** sale en la lista de corte, salvo que pase las reglas de "lista mañana" (2.4).

**Trampa:** cortar en punto 2 es el error más común en el cultivo. Un punto 2 grande se puede confundir con punto 3. Por eso se mide el **tamaño real** de la cabeza (sección 9) y no se usa solo el color. Además, RosaNet junta el punto 1 y el punto 2 en una sola clase: el tamaño también ayuda a separar un punto 2 avanzado (candidato a "lista mañana") de un botón todavía muy cerrado.

### 2.2 Óptimo (punto 3) – CORTAR HOY

**Cómo se ve:**
- El **caracol está definido**: desde arriba se ve la espiral de pétalos y **se ve el centro**.
- El rojo es **vivo e intenso**.
- La flor tiene **forma de copa** (en el video sale como patrón triangular invertido: ancha arriba y angosta en la base).
- Los **sépalos ya se separaron** y bajaron.

**Qué hace el robot:** la pone en la hoja **Rosas_listas** con cama, metro y altura.

**Trampa:** de noche el color cambia con la luz. Hace falta luz constante y calibrar el color (sección 6).

### 2.3 Pasado – sobreabierto (se perdió el punto)

**Cómo se ve:**
- Los pétalos están **abiertos hacia afuera** y la copa ya no se ve.
- El centro queda totalmente expuesto. A veces los bordes están oscuros o quemados.
- La cabeza es más ancha que alta.

**Qué hace el robot:** la cuenta como `pasado` (pérdida). Sirve para que el cultivo vea dónde se está cortando tarde.

**Trampa:** en el zip **solo hay 2 fotos** de pasadas. El modelo puede fallar mucho en esta clase. Hay que avisarle al equipo del modelo.

### 2.4 Lista mañana – punto 2 avanzado (CORTAR MAÑANA)

No es una clase que se ve directo en una sola foto. Es una **predicción**. El robot la decide con las `probabilidades` que ya entrega RosaNet (`RosePredictor.predict`), así:

**Paso 1. Candidata:** RosaNet dice `1_inmaduro`, pero con una probabilidad de óptimo alta.

```
p(2_optimo) ≥ 0,30   y   etapa = 1_inmaduro
```

**Paso 2. Tamaño:** la cabeza ya está cerca del tamaño típico de un punto 3.

```
               diámetro de la cabeza
tamaño_rel = ─────────────────────────────────
              diámetro típico de un punto 3
```

Si `tamaño_rel ≥ 0,85` → suma puntos.

**Paso 3. Historia (desde la segunda noche):** si la misma rosa se vio ayer (sección 9.4), se mira cuánto creció.

```
             tamaño_hoy − tamaño_ayer
velocidad = ──────────────────────────
                       1 día

               tamaño_punto3 − tamaño_hoy
días_faltan = ────────────────────────────
                      velocidad
```

Si `días_faltan ≤ 1,5` → **lista mañana**.

**Ejemplo:** el diámetro típico de punto 3 es 5,0 cm. Ayer la rosa medía 4,0 cm y hoy mide 4,5 cm.

```
velocidad    = (4,5 − 4,0) / 1 = 0,5 cm/día
días_faltan  = (5,0 − 4,5) / 0,5 = 1 día      → LISTA MAÑANA
```

**Paso 4. Puntaje final** (cuando no hay historia, la primera noche):

```
puntaje = 0,6 · p(2_optimo) + 0,4 · min(tamaño_rel, 1)
```

Si `puntaje ≥ 0,6` → lista mañana. (RosaNet no entrega nada sobre los sépalos, así que no se usan. Si más adelante el modelo lo da, se agrega como un tercer término.)

**Ejemplo:** `p(2_optimo) = 0,45` y `tamaño_rel = 0,92`.

```
puntaje = 0,6 · 0,45 + 0,4 · 0,92 = 0,27 + 0,37 = 0,64      → LISTA MAÑANA
```

**Valores a calibrar con datos reales:** el diámetro típico de punto 3, los umbrales 0,30 / 0,85 / 0,6 y la velocidad normal de crecimiento de Freedom. Quedan en `config.yaml`. **No son datos confirmados del cultivo.** Hay que preguntarle a un experto o medirlos.

**Trampa:** sin historia, "lista mañana" es una estimación. Desde la segunda noche mejora mucho.

### 2.5 Tabla resumen

| Estado | Acción | Sale en el reporte |
|--------|--------|-------------------|
| `inmaduro` | esperar | solo en el conteo |
| `lista_manana` | cortar mañana | conteo + lista con ubicación |
| **`optimo`** | **cortar hoy** | **lista con ubicación y altura** |
| `pasado` | pérdida | conteo |
| `dudosa` (confianza baja) | revisión humana | hoja aparte con la foto |

> Regla de seguridad: si RosaNet dice `seguro = false` (confianza menor a **0,6**, el `DEFAULT_THRESHOLD` de `ml/predict.py`), la rosa va a **"Dudosa"** y no se adivina. El umbral se lee del modelo, no se repite en el robot, para que los dos digan lo mismo.
>
> **Excepción (agregada al construir `percepcion/madurez.py`):** si el modelo duda **solo entre inmaduro y óptimo** (`p(inmaduro) + p(óptimo) ≥ 0,85`, en config `madurez.duda_entre_vecinas_min`), la rosa no va a "Dudosa": esa duda es justo la de una rosa a punto de abrir, y se decide con las reglas de "lista mañana". Sin esta excepción, "lista mañana" casi nunca salía, porque una rosa con `p(óptimo) ≥ 0,30` casi nunca tiene confianza de inmaduro ≥ 0,6.
>
> **Primer resultado en la simulación (oráculo):** de las rosas "lista mañana" que el robot vio, solo marcó el 9 % (pero todas las que marcó eran de verdad). Con 3 clases, una rosa casi lista suele tener `p(óptimo)` de 0,30 a 0,45 y `tamaño_rel` cercano a 0,9, que da un puntaje de 0,55 a 0,62, justo en el borde de 0,6. **No se calibró con el oráculo**, porque sus probabilidades son inventadas: hay que calibrar los umbrales con las salidas reales de RosaNet sobre carteles (paso 4:00) y con un experto del cultivo.

### 2.6 El tamaño de la cabeza como segunda opinión (paso 3, hecho)

`percepcion/madurez.py`, después de la regla de "seguro":

- **"Óptimo" con la cabeza de otro tamaño → dudosa.** Si el modelo dice óptimo pero `tamaño_rel` está fuera de
  `madurez.optimo_tamano_rel_min`–`optimo_tamano_rel_max` (0,7–1,6, es decir menos de 3,5 cm o más de 8 cm
  medidos), la rosa va a "Dudosa" con el motivo ("chica: ¿punto 2?" o "grande: ¿pasada?") y la revisa el experto
  en la tablet con la foto. Sin diámetro (modo foto, sin profundidad) no se aplica.
- **Las dudosas que parecen óptimas cuentan en la prioridad.** Una dudosa por baja confianza cuya mejor clase es
  óptimo suma `reporte.peso_dudosa_optimo` (0,5) al `orden` del cuadrante, y un cuadrante sin otras rosas para
  cortar pasa de "baja" a "media": puede que haya que ir. Las que fueron a dudosa por el tamaño no suman. Las
  columnas del reporte no cambian (las lee la app).
- **Umbrales:** el robot mide la cabeza con la caja del detector, que toma algo de margen. En la simulación midió
  las óptimas de 4,4 a 8,9 cm (casi todas por debajo de 7,6) y las pasadas que el modelo llamaba óptimas de 6,7 a
  10,5 cm. **Se eligieron con la simulación, donde los carteles tienen el tamaño de su estado: en la finca va a
  rendir menos.** Hay que calibrarlos midiendo rosas reales con la cámara del robot.

**Medido** (misma escena, misma red; "cortar hoy" por estado real: óptimas / inmaduras / pasadas):

| | Sin la regla | **Con la regla** |
|---|---|---|
| Carteles, semilla 7 | 10 / 0 / 7 | **10 / 0 / 3** |
| Carteles, semilla 11 | 18 / 0 / 6 | **18 / 0 / 0** |
| Oráculo, semilla 7 | 53 para cortar hoy | **49** (salen 4 inmaduras chicas que el oráculo marcó óptimas a propósito) |

No se perdió ninguna óptima. Las rosas que salen de la lista quedan en "Dudosas", con su foto, para el experto.

---

## 3. Cómo ve rosas de 2 m sin hardware extra

### 3.1 El problema

```
                      rosa a 2,0 m  ●
                                  ╱
                                ╱   hay que mirar ~60–70° hacia arriba
                              ╱
       cámara 1,19 m  [■]───── horizontal
                       │
                     robot       ← 40 cm →│ cama
```

- La cabeza solo sube unos **23°**.
- Si la rosa está **justo al lado**, a 40–60 cm, para verla a 2 m hay que mirar 52–62° hacia arriba. **No alcanza.**

### 3.2 La solución: mirar en diagonal hacia adelante + inclinarse + zoom digital

**Idea clave:** una rosa lejos se ve **más baja** en la foto. Si el robot mira **en diagonal hacia adelante** por el camino, ve las rosas altas a 1–3 m de distancia con un ángulo pequeño. La rosa que tiene justo al lado ya la vio desde la parada anterior.

```
 VISTA DESDE ARRIBA (un camino)

 cama izq  ████████████████████████████████████
                ╲ zona que ve (izq)  ╲
 camino    ──[R]────────────────────────────►  avanza
                ╱ zona que ve (der)  ╱
 cama der  ████████████████████████████████████

  parada k        parada k+1 (1,25 m después)
  ve de 0,7 m a 3,5 m adelante → hay traslape con la siguiente
```

**Ángulo para ver una rosa:**

```
                    altura_rosa − altura_cámara
ángulo = arctan ( ───────────────────────────── )
                   distancia horizontal a la rosa
```

**Ejemplo:** una rosa a 2,0 m de altura, 2 m adelante y 0,6 m al lado.

```
distancia = √(2² + 0,6²) = 2,09 m
ángulo    = arctan( (2,0 − 1,19) / 2,09 ) = arctan(0,39) ≈ 21°
```

**Se ve con la cabeza casi recta.**

**Inclinación disponible (sin hardware):**

| Parte | Hacia arriba |
|-------|-------------|
| Cabeza (pitch) | ~23° |
| Cintura (pitch, solo quieto) | ~18° |
| **Total** | **~41°** |
| + mitad del campo de visión de la cámara (ej. 45° / 2) | **~63° el borde de la foto** |

**Posturas por parada (4 fotos):**

| Foto | Giro (cintura + cabeza) | Inclinación | Qué alturas cubre a 1–3 m |
|------|------------------------|-------------|---------------------------|
| izq_media | +65° | 0° | 0,9–1,6 m |
| izq_alta | +65° | −35° (arriba) | 1,4–2,2 m |
| der_media | −65° | 0° | 0,9–1,6 m |
| der_alta | −65° | −35° (arriba) | 1,4–2,2 m |

> **Cambio después de medir (sección 16.1):** el giro era de 35°. Con 35° las rosas del costado se veían desde lejos y quedaban de menos de 32 px. Con **65°** el robot mira casi de frente a la cama (las rosas quedan a 0,5–2 m) y, con paradas cada 1,25 m, igual hay traslape entre una parada y la siguiente. La cobertura sube de ~88 % a ~95 % con las mismas fotos y el mismo tiempo.

> **Comprobado en la simulación:** "mirar hacia arriba" es un ángulo **negativo**, en la cabeza y en la cintura. El giro lo hace la cintura y la inclinación primero la cabeza (hasta −0,40) y el resto la cintura (`cuerpo/posturas.py`). Con −0,61 pedidos, la cámara queda mirando **~38° hacia arriba** (con el giro de 35° que se probó primero): la cintura cede un poco por el peso del torso. No importa, porque cada foto guarda la pose **real** de la cámara. La inclinación de cintura se hace **solo con el robot quieto**, por equilibrio.
>
> Las fotos se toman en el orden `izq_media → izq_alta → der_alta → der_media`, así la cintura cruza de lado una sola vez por parada.

### 3.3 Zoom digital

Una rosa lejos sale pequeña en la foto. La cabeza debe medir **al menos 32 píxeles**: es el mismo mínimo con el que se armaron los recortes de entrenamiento de RosaNet (`--min-size 32` en `ml/prepare_data.py`). Más pequeña, el modelo nunca vio algo así.

```
                           ancho de la imagen (px) / 2
distancia focal (px) = ───────────────────────────────
                        tan(campo de visión horizontal / 2)

                          tamaño real (m) · focal (px)
tamaño en la foto (px) = ─────────────────────────────
                                distancia (m)
```

**Ejemplo:** una cabeza de 5 cm a 3 m, con cámara de 1920 px y campo de 70°.

```
focal  = 960 / tan(35°) = 960 / 0,70 = 1371 px
tamaño = 0,05 · 1371 / 3 = 23 px      → muy pequeño, toca zoom
```

**Qué se hace:**
1. Se toma la foto a la **máxima resolución** de la cámara.
2. Se pasa una vez completa, reducida, para encontrar candidatas.
3. Las zonas con candidatas se **recortan a resolución completa**. Eso es el zoom digital, y se le pasa ese recorte al modelo (RosaNet lo reescala a 224 × 224).
4. Si aun así salen pequeñas, se baja la **distancia máxima útil** (en config: `distancia_max_m`) y se ponen paradas más seguidas.

> **Actualizado:** según el SDK AimDK_X2, la cámara RGB-D de la cabeza da **1280 × 720** (sección 14.1); el campo de visión sale de `camera_info`. Con esa resolución la cobertura simulada baja de 90 % a 68 %.
> Hay que confirmar la **resolución y el campo de visión** de la cámara RGBD de la cabeza del X2 Ultra real. En la simulación se ponen los mismos valores. Por ahora quedan en config: `camara.ancho`, `camara.alto`, `camara.fov_h_grados`.

**Detalles de MuJoCo para la cámara:**
- MuJoCo pide el campo de visión **vertical** (`fovy`), no el horizontal. Se convierte en el código:
  ```
  fovy = 2 · arctan( tan(fov_h / 2) · alto / ancho )
  ```
  Con 70° horizontales y 1920 × 1080 da **~43°**. (El script de referencia usa `fovy=45`, casi lo mismo.)
- El render fuera de pantalla solo llega hasta el tamaño de `<visual><global offwidth offheight>`. En `scene_jardin.xml` es 1280 × 960; en `escena_base.xml` se subió a 1920 × 1080.
- **En la simulación se usa la misma resolución que la real (1920 × 1080).** Se probó 1280 × 720 para ir más rápido, pero el tamaño de la rosa en píxeles es justo lo que decide si RosaNet la puede leer (mínimo 32 px): a 1280 una cabeza de 5 cm a 2 m mide 23 px y se perdían casi todas. Con 1920 × 1080 un camino de 10 m tarda ~10 s.

### 3.4 Rosas bajas

Las rosas de 1,0–1,2 m quedan por debajo de la cámara. Se ven en la foto "media" o mirando un poco hacia abajo (+10°). No hace falta agacharse.

---

## 4. Invernadero, cuadrantes y ruta

### 4.1 Nombres

```
Cuadrante ID:  INV1-C07-T3
               │    │   └─ tramo 3 (de 10 a 15 m)
               │    └───── cama 7
               └────────── invernadero 1
```

- **Tramo** = 5 m de cama. T1 = 0–5 m, T2 = 5–10 m, …, T6 = 25–30 m.
- Cada cama se ve **por los dos lados**, desde dos caminos distintos. Las rosas de los dos lados se suman al mismo cuadrante. En la tabla queda el lado (`izq`/`der`) solo como dato.

### 4.2 Plano supuesto

```
       pasillo principal (1,5 m)
 ═══════════════════════════════════════════  ← base / cargador aquí
  ║ C1 ║ C2 ║ C3 ║ ... ║ C20 ║
  ║    ║    ║    ║     ║     ║   camas de 30 m
  ║    ║    ║    ║     ║     ║   caminos de 0,8 m entre camas
 ═══════════════════════════════════════════
       pasillo del fondo
```

### 4.3 Ruta en serpiente

```
 camino 0 ↓ (fondo) → camino 1 ↑ (cabecera) → camino 2 ↓ → ...
```

- Entra por un camino, lo recorre todo, sale por el otro extremo, se corre al siguiente camino y vuelve.
- Así **no repite** caminos y no da la vuelta dentro del camino estrecho.
- Los caminos de las orillas (0 y 20) solo ven una cama.

**Hecho en la simulación (`navegacion/ruta.py`, `ronda.py`):**
- El robot sale de la **base** (placa verde en el pasillo principal, `sim.base_xy`), entra al camino 0, lo recorre hasta el fondo, sale al pasillo del fondo, gira 90°, se corre al camino 1, gira otra vez y vuelve hacia la cabecera, y así. Al terminar vuelve a la base. Si quedó en el pasillo del fondo, regresa por el último camino sin tomar fotos.
- Siempre camina de frente: antes de cambiar de dirección gira en el lugar, y nunca gira dentro de un camino.
- Las fotos se nombran con el número de parada contado desde la cabecera, igual en los dos sentidos.
- El "lado" (`izq`/`der`) del reporte depende de hacia dónde caminaba el robot: en los caminos de vuelta, la izquierda y la derecha se invierten. Cada foto guarda el `rumbo` del robot.
- Ronda completa en la escena de prueba (3 caminos): 108 fotos, ~55 s de simulación sin ventana, cobertura ~95 % (igual que antes de la serpiente).

### 4.4 Tiempo estimado por noche

| Dato | Valor |
|------|-------|
Paradas cada **1,25 m** (decidido después de medir la cobertura en la simulación, sección 16.1; antes eran 2,5 m):

| Dato | Valor |
|------|-------|
| Paradas por camino | 30 / 1,25 + 1 = 25 |
| Fotos por parada | 4 |
| Tiempo por parada (posar + foto) | ~8 s |
| Caminar 1,25 m a 0,3 m/s | ~4 s |
| Por camino | 25 × 12 s ≈ 5 min |
| Cambio de camino | ~1 min |
| **Total (21 caminos)** | **≈ 2 h 10 min** |
| Fotos por noche | 21 × 25 × 4 ≈ **2.100** |

> **Batería:** las fichas dicen **~2 h a 0,5 m/s** (CONTEXTO.md 2.0.2). Con paradas cada 1,25 m la ronda (~2 h 10 min) **ya no cabe en una carga**: se parte en dos. A mitad de la ronda va a la base y se cambia la batería (es intercambiable) o se carga, y sigue desde el último tramo guardado (sección 15). Con 2,5 m cabía (~95 min), pero solo veía el 47 % de las rosas.

### 4.5 Invernadero completo, medido en la simulación (paso 9, 2026-10-24)

`python main.py --completo` (y `--continuar` después de cada vuelta por batería): 20 camas de 30 m, 6.031 rosas,
21 caminos en serpiente, oráculo, semilla 7, con los obstáculos por defecto (el camino 2 se abandona en el metro 4,2).

| | Con señalar (`accion.tipo: senalar`) | Sin señalar (`ninguna`) |
|---|---|---|
| Tiempo del robot | **286 min** (4 h 46 min) | **120 min** (2 h) |
| Vueltas a la base por batería (25 %) | 2 (la ronda se hace en 3 partes) | 1 (a los 98 min, con el 86 % de las fotos) |
| Fotos | 2.012 | 2.012 |
| Rosas señaladas | 1.865 (23 fuera de alcance) | — |
| Cobertura | 95,2 % | 95,3 % |
| Duplicados / falsas | 0 % / 25 (0,4 %) | 0 % / 32 (0,5 %) |
| Error de altura / metro | 0,5 cm / 0,9 cm | igual |
| Tiempo de cómputo (CPU, sin ventana) | 29 min | 20 min |
| Reporte | 120 cuadrantes, JSON 631 KB, Excel 622 KB | igual |

- **Señalar suma ~5,3 s por rosa óptima** (166 min para 1.865 rosas): más que toda la ronda sin señalar. Con una
  sola batería no cabe en una noche. Lo que pesa no es el foco (`accion.segundos: 1,5`) sino apuntar: girar,
  medir y corregir hasta 6 veces con 1 s de espera. Bajar `accion.segundos` ahorra poco.
- **Opciones:** señalar solo en los N primeros cuadrantes del `orden`; marcar el cuadrante con la tira LED del
  pecho, sin apuntar; o señalar solo en la demo.
- **Decisión (2026-10-24): señalar solo en los 10 primeros cuadrantes** (`accion.primeros_cuadrantes: 10`;
  `null` = en todos). El `orden` de esta noche recién se conoce al terminar la ronda, así que el robot usa el del
  **último reporte** de ese invernadero (`ronda.cuadrantes_a_senalar`; no cuenta los del modo foto). Sin un reporte
  anterior (la primera noche) señala en todos. La lista se decide al empezar, queda en el checkpoint (igual con
  `--continuar`) y sale en la hoja Ronda. Medido con el invernadero completo, usando el reporte de la noche anterior:

| | Señalar en todos | **Solo los 10 primeros cuadrantes** | Sin señalar |
|---|---|---|---|
| Tiempo del robot | 286 min | **138 min (2 h 18 min)** | 120 min |
| Vueltas a la base por batería | 2 | **1** | 1 |
| Rosas señaladas | 1.865 | **211** (4 fuera de alcance) | — |
| Cobertura | 95,2 % | 95,5 % | 95,3 % |
- **"Solo prioridad alta" no ahorra nada en esta escena:** los 120 cuadrantes salen `alta` (6 a 15 óptimas cada
  uno, con `optimo_prioridad_alta: 3`). El umbral de 3 hay que acordarlo con la finca y medirlo con la proporción
  real de óptimas; el `orden` igual sirve para ordenar.
- **Rosas falsas:** 0,4 %, todas con una sola vista. Son rosas reales ubicadas con la profundidad de algo que las
  tapa (entre 0,1 y 1 m de error, casi siempre más cerca de la cámara). Dos quedaron a 6 y 12 m: la profundidad
  pasó por un hueco hasta el fondo. Con una escena de prueba de ~140 rosas el mismo porcentaje da 0 o 1, así que
  no es un problema nuevo de la escala. Se puede filtrar con "vista al menos dos veces", pero perdería rosas vistas
  una sola vez; queda para medir con la cámara RGB-D real.
- **Visor (`--ventana`):** la escena completa tiene 52.486 piezas y el visor de MuJoCo 3.17 admite 100.000: se ve todo.

---

## 5. Caminar por un camino estrecho y difícil

### 5.1 Márgenes

```
 |← 80 cm de camino →|
 |   11 | 58 | 11    |   cm
 | cama | X2 | cama  |
```

- Solo hay **11 cm** de cada lado (con los 58 cm del modelo de MuJoCo; si el robot real mide 46 cm, como dicen las fichas, quedan 17 cm). Al caminar, los brazos van **pegados al cuerpo**: el hombro rueda hacia adentro y los codos doblados.
- Los tallos y las hojas se meten al camino. El robot los va a rozar. En la simulación las hojas no chocan con el robot (como en la realidad, son flexibles), pero los **tallos gruesos y los postes** sí.
- El robot camina por el **centro** del camino. Sin marcas físicas, se usa el **LiDAR 3D** (funciona a oscuras) para medir la distancia a las dos camas y corregir. Si la unidad no trae LiDAR, se usa la cámara de profundidad, y si tampoco la trae, la odometría + las marcas de la sección 9.1.

### 5.2 Piso difícil

En la simulación se agregan al azar:
- **Mangueras / tubos** cruzados (cilindros de 2–4 cm).
- **Desniveles** de 1–3 cm (con mapa de alturas, `hfield`).
- **Barro**: zonas con menos fricción.

Qué hace el robot:
- Camina **más lento** (0,2 m/s) en los tramos marcados como difíciles.
- Si el LiDAR o la profundidad detectan algo más alto que 5 cm en el camino, **para** y lo anota en el reporte como "obstáculo en INV1-C07-T3".

**Hecho en la simulación (`sim/estructura.py`, `ronda.py`, 2026-10-24):**
- **Escena:** postes cada 3 m en los bordes de las camas, con alambres guía a 1,2 y 1,8 m (tapan la vista como en las fotos reales), 1–2 mangueras cruzando cada camino y 0–2 desniveles (parches de 1–3 cm). Usa su propio azar: no cambia las rosas de una semilla. Se configura en `sim.estructura`.
- **Obstáculos altos** en `sim.obstaculos` (camino, metro, alto, y `se_quita_s` si alguien lo quita mientras el robot espera). Por defecto: una caja en el camino 1 que quitan a los 10 s y un balde en el camino 2 que se queda toda la noche.
- **Sensor** (`obstaculos_adelante`): rayos hacia adelante, como un LiDAR, en el centro del camino y a 25 cm de cada lado. Los rayos altos (8 cm a 1 m) ven lo que obliga a frenar; uno bajo (1,5 cm) ve mangueras y desniveles. No ven al propio robot. En el robot real sale del LiDAR o de la cámara de profundidad.
- **Comportamiento** (`_avanzar` en `ronda.py`): avanza de a 1 m mirando 1,5 m adelante.
  - Obstáculo bajo en el tramo: lo cruza a 0,2 m/s (`velocidad_dificil_m_s`).
  - Obstáculo alto: frena a 50 cm y espera hasta 30 s (`espera_obstaculo_s`), revisando cada 5 s. Si lo quitan, sigue.
  - Si sigue ahí: abandona el camino, sale por donde entró (es la única vez que gira dentro de un camino) y sigue con los demás caminos desde ese lado (la serpiente se vuelve a planear).
- **Reporte:** en `obstaculos` (lo que lee la app) van los cuadrantes junto a un camino bloqueado, en el tramo del obstáculo (quedaron revisados solo en parte). La hoja `Ronda` y el checkpoint guardan todos, también los que quitaron.
- **Ronda de prueba con los obstáculos por defecto:** 84 fotos en vez de 108 (el camino 2 se abandonó en el metro 4,2), cobertura 90 % (la cama 2 se vio solo desde el camino 1), obstáculos reportados: `INV1-C02-T1`.

### 5.3 Caminar en simulación vs real

| Modo | Cómo camina |
|------|-------------|
| Sim (hoy) | Punto guía que sostiene la pelvis, piernas animadas. No tiene equilibrio real. |
| Sim (después) | Controlador entrenado (RL), si el equipo lo consigue. |
| Real | **Controlador de locomoción oficial de AgiBot** (SDK AimDK_X2 / ROS). El código solo le manda "avanza X m", "para" y "gira". |

> El robot real **no** debe usar el control PD de la simulación en las piernas: se cae. En modo real solo se mandan **velocidades** al controlador oficial, y la cabeza y la cintura se mueven por su API. Hay que revisar en la documentación oficial del AimDK_X2 cómo se hace y si deja mover la cintura mientras el controlador de equilibrio está activo. No se asume ninguna API específica.

---

## 6. Noche y luz

**El punto más delicado del proyecto.** La diferencia entre punto 2 y punto 3 es en parte el **tono de rojo**. Sin luz buena y constante, el modelo se confunde.

### 6.1 Opciones

| Opción | Hardware nuevo | Notas |
|--------|----------------|-------|
| A. Prender las luces del invernadero durante la ronda | No | La más fácil si el invernadero tiene luces |
| B. Luz propia del robot (si la trae) | No | Revisar si el X2 trae alguna luz |
| C. Lámpara pequeña en la cabeza | Sí | Lo más confiable, pero rompe la regla de "sin hardware" |

En la **simulación** se usa una linterna en la cabeza, como ya hicimos. Para el real, **queda como decisión pendiente** (sección 18).

### 6.2 Calibrar el color

- Una **tarjeta blanca/gris** al inicio de cada camino (una hoja plastificada en un palo, no es hardware del robot).
- El robot le toma foto y ajusta el balance de blancos de esa noche.
- Se guarda el factor en el reporte (hoja `Ronda`).

### 6.3 Profundidad de noche

La cámara RGBD normalmente mide profundidad con luz infrarroja propia, así que **funciona a oscuras**. El color sí necesita luz. Hay que confirmarlo con la cámara del X2.

---

## 7. Conexión con RosaNet (el modelo del equipo)

Tú **no** haces el modelo. RosaNet vive en `robot/ml/`, en este mismo repo, y lo trabaja otra persona. Lo que haces es un **adaptador**: una pieza que recibe la foto, llama al modelo y devuelve siempre el mismo formato. Si el modelo cambia, solo se cambia el adaptador. **No se toca nada dentro de `ml/`.**

### 7.1 Lo que RosaNet hace (y lo que no)

RosaNet **clasifica una sola rosa ya recortada**. **No** encuentra las rosas en una foto con muchas (no es un detector).

```python
from ml.predict import RosePredictor

pred = RosePredictor(ckpt="runs/rosanet/best.pt")
pred.predict(recorte_PIL)
# {
#   "etapa": "2_optimo",                    # 1_inmaduro | 2_optimo | 3_pasado
#   "nombre": "Punto óptimo de corte",
#   "confianza": 0.87,
#   "seguro": True,                         # confianza >= 0,6
#   "probabilidades": {"1_inmaduro": 0.10, "2_optimo": 0.87, "3_pasado": 0.03},
#   "tips": {...}
# }
```

Por eso el robot se arma en **dos pasos**:

```
foto completa ──► [1. candidatas] ──► cajas ──► [2. recorte + RosaNet] ──► clase por rosa
                   (lo hace el robot)             (adaptador)
```

### 7.2 Paso 1: encontrar las candidatas (`percepcion/candidatas.py`)

| Modo | Cómo |
|------|------|
| `oraculo` (sim) | El simulador sabe dónde está cada cabeza: proyecta su posición 3D a la foto y da la caja |
| `color` (sim con carteles, modo foto y real) | Máscara de **rojo en HSV** + limpieza (abrir/cerrar) + componentes conectados → una caja por mancha roja. Se descartan las de menos de 32 px y las muy alargadas |
| `detector_equipo` (si llega) | Si el equipo del modelo entrega un detector (por ejemplo, YOLO), se enchufa aquí |

**Trampas de la máscara roja:** dos rosas pegadas salen como una sola mancha, y una rosa tapada por una hoja sale partida en dos. Se usa la profundidad para separar manchas que están a distancias distintas y la deduplicación 3D (sección 9.4) para juntar las partidas. Es un límite conocido y hay que decirlo en el pitch.

### 7.3 Paso 2: recortar y clasificar (`percepcion/clasificador.py`)

1. Se toma cada caja y se le agrega **10% de margen**, igual que en el entrenamiento (`--pad 0.10` en `ml/prepare_data.py`). Si el recorte es distinto al del entrenamiento, el modelo se confunde.
2. Se recorta de la foto a **resolución completa** (zoom digital, sección 3.3).
3. Se llama a `RosePredictor.predict` (o a un lote de recortes, si el equipo agrega esa función).
4. Se traduce al contrato del robot:

```python
{
  "bbox": [x1, y1, x2, y2],          # caja en píxeles (de la foto completa)
  "clase": "optimo",                 # inmaduro | optimo | pasado (sin el número)
  "confianza": 0.87,
  "seguro": True,                    # tal cual lo da RosaNet
  "probs": {"inmaduro": 0.10, "optimo": 0.87, "pasado": 0.03},
}
```

Esqueleto:

```python
class ClasificadorRosaNet:
    def __init__(self, cfg):
        # importa ml.predict.RosePredictor y carga cfg["modelo"]["ckpt"]
        ...
    def clasificar(self, img, cajas):
        # recorta con margen, llama al modelo y traduce al contrato de arriba
        ...

class ClasificadorOraculo:
    # solo para simulación: usa la verdad de MuJoCo + ruido
    ...
```

Para que funcione el `import ml...`, el programa se corre **desde la carpeta `robot/`**, igual que los comandos de `ml/` en el README.

### 7.4 Oráculo y carteles para la simulación

RosaNet está entrenada con **fotos reales**. Las rosas de MuJoCo son figuras simples y el modelo **no las va a reconocer**. Hay dos caminos, y **los dos son necesarios**:

1. **Oráculo** (primero): el simulador sabe dónde está cada rosa y su estado. Da la caja y la clase con errores a propósito (5–10% de fallos, confianzas ruidosas). Con eso se prueba **todo el resto del sistema** sin esperar al modelo.
2. **Carteles con fotos reales** (**prioridad alta**, no opcional): en la punta de cada tallo se pone un plano con la textura de una rosa real. Ya hay recortes de la finca en `app-tablet/assets/rosas/` (1_inmaduro, 2_optimo, 3_pasado). Así **RosaNet de verdad** corre sobre las fotos de la simulación, con la máscara roja encontrando las candidatas.
   - Ojo: muchos de esos recortes los usó RosaNet para entrenar. Para medir de verdad hay que usar los del **test** del equipo (`data/finca_stages/test`) o fotos nuevas.

Se cambia en config: `percepcion.candidatas: auto | oraculo | color | detector_equipo` y `percepcion.clasificador: auto | oraculo | rosanet | detector_equipo`.

### 7.6 Cuando el equipo termine el detector (git pull)

Todo lo que toca `ml/` está en **un solo archivo**: `percepcion/modelo_equipo.py`. Con `auto` (lo que viene por defecto):

| Situación | Candidatas | Clasificador |
|-----------|-----------|--------------|
| Sim con rosas como figuras | oráculo | oráculo (el modelo no reconoce figuras) |
| Sim con carteles o robot real, sin detector (o sin `ultralytics`) | máscara roja | RosaNet |
| Sim con carteles o robot real, con detector (**lo de hoy**) | **detector del equipo** | RosaNet |
| Faltan los pesos de RosaNet | sim: oráculo | sim: oráculo (con aviso) · real: **error**, no adivina |

- `py main.py` imprime qué está listo, qué no y por qué, y qué va a usar la ronda.

### 7.7 Integrado con el modelo del equipo (pull del 2026-10-23)

El equipo subió a `main` el modelo completo (contrato en `robot/CLAUDE.md`). Se integró en la rama `A` **sin cambiar nada de lo que tocaron** (`ml/`, `modelos/`, `robot/CLAUDE.md`, el pitch). Del lado del robot se adaptó:

- **Config:** pesos en `modelos/rosanet.pt` y `modelos/detector_rosas.pt` (ya están en git, no hay que copiarlos) y `margen_recorte: 0.15`, el margen con el que se calibró RosaNet.
- **Candidatas (`percepcion/candidatas.py`):** `CandidatasDetector` llama a `RoseDetector.detect(foto)`. Las fotos del robot ya son RGB (MuJoCo y el driver de la cámara); si alguna vez se leen con OpenCV, hay que pasarlas a RGB antes. `CandidatasColor` (máscara roja) queda de respaldo.
- **Clasificador (`percepcion/clasificador.py`):** `ClasificadorRosaNet` recorta con `pad_box` del equipo (`ml/prepare_data.py`) y 15 % de margen, llama a `RosePredictor.predict` y pasa las etapas al formato del robot: `"2_optimo"` → `"optimo"` (`etapa.split("_", 1)[1]`), también en las probabilidades.
- **Dependencias:** `ultralytics` (lo usa el detector) se agregó a `requirements.txt`.
- **Carteles en la simulación (`sim/rosas.py`):** cada rosa es un plano con una foto real de la finca de su categoría (`app-tablet/assets/rosas/`). Antes de cada foto el plano gira para mirar a la cámara, porque una rosa real es 3D y se ve bien desde cualquier lado, y una foto plana vista de lado se deforma. "Lista mañana" no existe con carteles (una foto no lo muestra).

**Resultado: ronda por los 3 caminos con `python main.py --rosas cartel`** (detector + RosaNet de verdad, 108 fotos, ~1 min):

| Medida | Valor |
|---|---|
| Rosas encontradas por el detector (cobertura) | **85 %** |
| Duplicados / falsas | 0 % / 0 |
| Error de ubicación | 0,2 cm (altura y metro) |
| Óptimas reales que marcó como óptimas | 33 de 39 (85–87 %) |
| De las que marcó como óptimas, cuántas lo eran | **35 %** |
| Inmaduras que marcó como óptimas | 27 de 107 (25 %) |
| Pasadas que marcó como óptimas | 16 de 23 (el equipo ya avisó que `3_pasado` no funciona) |

**Por qué RosaNet marca de más "óptimo" en la simulación.** Se probó con las fotos originales de la finca, fuera de la simulación:

| Cambio a la foto | Inmaduras que salen como óptimas |
|---|---|
| Ninguno (foto original) | 2 de 47 |
| Más o menos brillo, más o menos saturación | 1–3 de 47 (no influye) |
| Reducida a 70 px / 50 px de ancho | 6 / 10 de 47 |
| **Margen de la foto pintado de negro**, misma escala de la rosa (como el fondo de noche) | **14 a 33 de 47** (margen del 8 % / 12 %) |
| Margen de la foto pintado de gris claro, misma escala | 3 de 47 (y 18–19 de 20 óptimas, casi como el original) |

(Una primera prueba que **agregaba** un borde alrededor de la foto daba 30 de 47 con negro, pero también cambiaba el tamaño de la rosa dentro del recorte, y eso solo ya altera a la red: con cualquier borde agregado, incluso claro o espejado, perdía óptimas. La prueba que vale es la de la tabla, que deja la rosa del mismo tamaño.)

El recorte con 15 % de margen toma también lo que hay alrededor de la rosa. De noche ese alrededor es oscuro, y RosaNet, entrenada con fotos de día con fondo claro (plástico del invernadero), se confunde. **Esto también va a pasar en el robot real de noche.** El equipo del modelo no tiene fotos de noche para reentrenar.

### 7.8 Fondo claro: arreglo del lado del robot (`percepcion.fondo_claro`)

Antes de pasar el recorte a RosaNet, el robot usa la profundidad para pintar de gris claro los píxeles del **fondo**: los que no tienen dato o están más de 25 cm detrás de la rosa. La rosa, sus hojas y lo que está delante no se tocan. Sin profundidad (si la unidad no trae RGB-D), el recorte queda igual. Está en `percepcion/clasificador.py` (`aclarar_fondo`) y se apaga con `percepcion.fondo_claro.activo: false`.

**Cambia lo que recibe la red** (no la red): las métricas del equipo del modelo se midieron con recortes sin editar. **Hay que avisarle al equipo del modelo**, para que lo sepan al comparar números y porque si ellos reentrenan con fondos oscuros (aumento de datos, sin fotos nuevas) este arreglo puede sobrar.

**Resultado en la simulación** (carteles + detector + RosaNet, 3 caminos, semillas 7 y 11):

| | Sin fondo claro | Con fondo claro (gris 170) |
|---|---|---|
| Inmaduras marcadas como óptimas (el error más caro) | 27/107 y 24/102 | **8/107 y 16/102** |
| De las que marca como óptimas, cuántas lo eran | 35 % y 41 % | **53 % y 51 %** |
| Óptimas reales que encuentra | 33/39 y 40/42 | 19/39 y 29/42 (**baja**) |
| Inmaduras que marca como dudosas | 33 y 41 | 2 y 3 |
| Pasadas marcadas como óptimas | 16 y 15 | 7 y 11 |

- Baja mucho el error de cortar en punto 2, pero también se pierden óptimas: es un **intercambio**, no un arreglo completo. Se dejó activo porque la finca dice que el error más común es cortar en punto 2.
- El tono del gris casi no cambia el resultado (170, 205 y 235 dan parecido).
- Fuera de la simulación, con las fotos de la finca, el gris claro no hacía perder óptimas. En la simulación sí, probablemente porque los carteles son pequeños (~75 px) y planos. **Hay que validarlo con fotos reales de noche**, aunque sean pocas (rosas compradas, cuarto oscuro y una linterna).
- Otras opciones que siguen abiertas: reentrenar con fondos oscuros (equipo del modelo), prender las luces del invernadero en la ronda (sección 6), usar el tamaño de la cabeza como segunda opinión, y exigir más confianza para "óptimo" de noche.

### 7.9 RosaNet "noche" (pull del 2026-10-24)

El equipo del modelo reentrenó RosaNet con **aumento de fondo oscuro** (`modelos/rosanet.pt`; la anterior quedó en `modelos/rosanet_v1_dia.pt`). Se integró a la rama `A` sin cambiar nada de lo suyo y se midió desde el robot:

**Con las fotos de la finca, margen cambiado y la rosa del mismo tamaño** (inmaduras → óptimo, sobre 47):

| Margen alrededor de la rosa | Red de día | Red noche |
|---|---|---|
| Original | 2 | 2 |
| Negro, 8 % | 14 | **6** |
| Negro, 12 % | 33 | **14** |
| Gris claro, 12 % | 3 | 3 |

**En la simulación** (carteles + detector + RosaNet noche, ronda en serpiente por los 3 caminos, semillas 7 y 11):

| | Sin fondo claro | Con fondo claro |
|---|---|---|
| Inmaduras marcadas como óptimas | **1/113 y 2/104** (con la red de día eran 27 y 24) | 1/113 y 1/104 |
| Óptimas reales marcadas como óptimas | 11/39 y 12/45 | 8/39 y 8/45 |
| Cobertura | 88 % y 82 % | 88 % y 82 % |

- **Decisión: `fondo_claro` APAGADO.** Con la red noche ya no hace falta para las inmaduras y hace perder óptimas, como predijo el equipo del modelo.
- **Problema nuevo: la red noche es muy prudente con las óptimas, sobre todo si la rosa sale pequeña.** Con la regla de "seguro" (confianza ≥ 0,6), en las fotos de la finca:

| Tamaño de la rosa | Red de día: óptimas reconocidas | Red noche: óptimas reconocidas | Red noche: óptimas → dudosa |
|---|---|---|---|
| Foto original | 19/20 | 11/20 | 7 |
| 100 px | 19/20 | 7/20 | 11 |
| 70 px (como en la sim) | 19/20 | 5/20 | 13 |
| 50 px | 18/20 | 1/20 | 16 |

  En la simulación pasa lo mismo: de 39 óptimas, 11 salen óptimas, 12 dudosas (casi todas con "óptimo" como mejor clase, confianza 0,43–0,59) y 16 inmaduras. No marca de más (el error caro), pero se le escapan muchas que había que cortar. **Para el equipo del modelo:** revisar la confianza de "óptimo" en la versión noche y entrenar también con recortes pequeños (70–100 px). **Del lado del robot**, si sigue así: acercar las fotos (rosas más grandes en píxeles) o contar en la prioridad del cuadrante las dudosas cuya mejor clase es "óptimo".

### 7.10 Envío a la app de la tablet (Supabase)

En el mismo pull el equipo de la app agregó `robot/subir_reporte.py`: sube el JSON del reporte a la tabla `reportes` de Supabase, y la app de la tablet lee de ahí el último reporte para el turnero. La app usa **exactamente el formato de nuestro JSON** (sección 10.4; `app-tablet/src/data/reporte.ts`), así que no hubo que cambiar el reporte.

Del lado del robot se agregó `envio.metodo: supabase` (`reporte/envio.py`): usa la función `subir()` de ellos sin modificarla, dentro de la bandeja de salida con sus reintentos. Solo sube el `.json`; el Excel se queda en el robot. Necesita `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` en `robot/.env` (no se sube a git). En la simulación sigue por defecto `carpeta`, porque no hay claves; **no se probó contra el Supabase real.**

### 7.11 Detector ajustado con escenas de la finca (pull del 2026-10-24)

El equipo del modelo subió `modelos/detector_rosas.pt` ajustado con 95 escenas del invernadero (en sus 30
escenas de prueba encuentra el 63 % de las rosas con 5 falsas alarmas; el anterior, el 25 %). También cambió
`ml/detect.py` a 960 px y confianza 0,25. El robot lo usa solo (crea el detector solo con los pesos), sin
cambiar nada de lo suyo. La versión anterior queda como `detector_rosas_v1_publico.pt`.

**Medido en la simulación con carteles (fotos reales de la finca, `--rosas cartel`), misma escena:**

| | Detector anterior | Detector de la finca (960 px) | **Detector de la finca, foto sin achicar (1920 px)** |
|---|---|---|---|
| Cobertura | 29 % | 50 % | **71 %** |
| Clase correcta | 45 % | 61 % | **69 %** |
| Rosas falsas | 0 | 0 | 0 |
| Tiempo de cómputo (CPU, 84 fotos) | 63 s | 61 s | 78 s |

- **Adaptación del lado del robot:** `percepcion.detector_tamano_nativo: true`. El detector mira la foto en su
  tamaño (1920 px en la sim, 1280 en el X2 real) en vez de achicarla a 960: las rosas de la ronda ya son
  pequeñas y al achicar la foto se perdían. No toca `ml/`: cambia el `imgsz` del detector ya creado, y nunca
  por debajo del suyo (la webcam del modo foto sigue igual).
- **Para el equipo del modelo:** ellos midieron 960 px con sus fotos; con las del robot rinde más a tamaño
  completo. Conviene que lo midan también con sus escenas (¿suben las falsas alarmas a 1280–1920 px?).
- **Modo foto:** el detector nuevo ya encuentra solo una rosa de cerca (antes hacía falta el cuadro guía).
- **Lo que cortaría el robot (estado final, 1920 px):** de 12 "cortar hoy", 9 son óptimas, 2 inmaduras y 1
  pasada. Lo que se pierde ahora es de RosaNet (sin cambios en este pull): 12 óptimas salen inmaduras, 8
  dudosas, y las pasadas casi siempre van a "dudosa" (17 de 19). Queda para el paso de las reglas de
  decisión, cuando llegue el RosaNet completo.

### 7.12 Detector "noche" (pull del 2026-10-24, tarde)

El equipo del modelo ajustó el detector con escenas de noche simuladas (`modelos/detector_rosas.pt`; el anterior
quedó como `detector_rosas_dia.pt`). `ml/detect.py` ahora elige el umbral según el archivo de pesos (0,55 para el
de noche, 0,25 para el de día). El robot crea el detector solo con los pesos, así que toma el umbral nuevo sin
cambiar nada.

**Medido con carteles (`--rosas cartel`), misma escena de prueba, 1920 px:**

| | Detector día | **Detector noche (en uso)** |
|---|---|---|
| Cobertura | 72 % | 71 % |
| Clase correcta | 69 % | 67 % |
| Precisión / recall de "óptimo" | 40 % / 39 % | 37 % / 33 % |
| Rosas falsas | 0 | 0 |

- Casi igual (3–4 rosas de diferencia, menos que el ruido de una escena). En la simulación no se ve la mejora que
  midió el equipo (de 22 % a 55 % de noche): los carteles salen bien iluminados por la linterna y la noche de MuJoCo
  no se parece a la que ellos simularon. Se deja el de noche, porque la ronda real es de noche y aquí no pierde nada.
- Esta medición se hizo con la RosaNet anterior. Después llegó **RosaNet + forma** (abajo).

### 7.13 RosaNet + forma (pull del 2026-10-24, tarde)

El equipo sumó un clasificador de forma y color (`ml/shape.py`, `modelos/forma.joblib`). `RosePredictor` lo
carga solo y promedia su opinión con la de RosaNet, sin cambiar el contrato: el robot no cambió nada.

**Medido con carteles (`--rosas cartel`), detector noche, misma escena, semillas 7 y 11:**

| | Solo RosaNet | **RosaNet + forma (en uso)** |
|---|---|---|
| Cobertura | 71 % / 73 % | 71 % / 73 % (no depende del clasificador) |
| Clase correcta | 67 % / 68 % | **74 % / 80 %** |
| Óptimas reales que marca como óptimas (recall) | 33 % / 37 % | **51 % / 59 %** |
| De las que marca como óptimas, cuántas lo eran | 37 % / 46 % | **56 % / 69 %** |
| "Cortar hoy": óptimas / inmaduras / pasadas | 11/0/0 y 13/0/1 | **10/0/7 y 18/0/6** |
| Dudosas | 25 / 24 | 24 / 17 |

- **Ninguna inmadura sale para "cortar hoy"** (el error más caro), y se encuentran casi el doble de óptimas.
- **Problema nuevo: las pasadas salen como óptimas** (6–7 de cada 17–24 rosas para cortar). En la simulación
  todas las pasadas son las **2 únicas fotos** de pasadas de la finca, repetidas en cada cartel, así que el número
  exagera el error; pero indica que la forma ve "copa ancha y roja" y no distingue la copa abierta de más. Cortar
  una pasada es menos grave que cortar una inmadura (ya está perdida), pero llena la lista. **Para el equipo del
  modelo:** revisar la forma con las pasadas, y conseguir más fotos de pasadas.
- **Del lado del robot:** la regla del tamaño de la cabeza (sección 2.6) baja las pasadas en "cortar hoy" de 7 y 6 a
  3 y 0, sin perder óptimas.
- **Fotos de las dudosas para la app (hecho, `reporte/fotos.py`):** un experto revisa las dudosas en la tablet y
  la app muestra la foto si `foto` es una dirección web. Con `envio.metodo: supabase`, antes de subir el reporte
  el robot recorta cada dudosa con su caja de `detecciones.jsonl` (15 % de margen, mínimo 256 px), la sube al
  bucket público `fotos-rosas` de Supabase Storage y pone esa dirección en `foto`. El archivo de `salida/` no
  cambia. Si una foto falla, esa dudosa queda con la ruta local (la app muestra una de muestra) y el reporte se
  sube igual. Para la demo: `python main.py --config config/demo.yaml` (cartel + Supabase + fotos).
  Comprobado con un Storage falso y una ronda real: 25 de 25 dudosas con su recorte. **No se probó contra el
  Supabase real** (falta `SUPABASE_SERVICE_ROLE_KEY` en `robot/.env`). Límite: el modo foto (`--enviar`) no sube
  fotos, porque sus fotos no están en `datos/rondas/`.

### 7.5 Modo foto: para la demo en vivo

En la presentación el jurado **pone a prueba el prototipo con casos evaluados en ese momento** (CONTEXTO.md sección 1, "Funcionamiento y evidencia", 25 pts). Una ronda con oráculo no responde a una rosa que traiga el jurado. Por eso hay un modo aparte:

```powershell
py modo_foto.py foto_del_jurado.jpg      # o --webcam
```

- Pasa la foto por **el mismo pipeline del robot**: candidatas por color → recorte → RosaNet → "lista mañana" (sin historia) → reporte.
- Muestra la foto con las cajas pintadas por estado, la confianza y los **tips** que ya trae RosaNet.
- Genera un mini reporte (Excel + JSON) como si fuera un cuadrante, para que se vea en el dashboard.
- Si hay tiempo, el mismo modo puede poner la foto como cartel en la simulación y hacer que el robot "la encuentre".

**Hecho (`modo_foto.py`, 2026-10-24):**

```bash
python modo_foto.py foto.jpg            # una o varias fotos (acepta comodines)
python modo_foto.py --webcam            # cámara en vivo: ESPACIO analiza, Q sale
python modo_foto.py foto.jpg --reporte  # además un mini reporte (Excel + JSON) como una ronda
python modo_foto.py foto.jpg --enviar   # y lo manda a la app con envio.metodo
```

- Usa las mismas piezas que la ronda real: **detector del equipo + RosaNet** (o la máscara roja si falta el detector) y las reglas de madurez del robot. Nunca usa el oráculo.
- **Una sola rosa de cerca:** el detector del equipo descarta cajas de más del 8 % de la foto (está hecho para escenas del invernadero). Si se le quita ese límite (`max_box_fraction`), marca caras, manos, un termo rojo y hasta el ícono de "cámara tapada": **no sirve para una rosa en la mano** (para el equipo del modelo). Por eso:
  - **Con la cámara:** la vista muestra un **cuadro guía** en el centro ("pon la rosa dentro del cuadro"). Si el detector no encuentra rosas en la escena, se analiza **solo lo que está dentro del cuadro**, nunca la imagen completa con la persona y el salón. Si el cuadro no tiene nada rojizo, dice que no ve una rosa. Límite: un objeto rojo dentro del cuadro se analiza como rosa.
  - **Con una foto que se le pasa a propósito:** si el detector no encuentra rosas, se analiza la foto completa como una rosa (sin filtro de color: los botones inmaduros oscuros casi no tienen píxeles rojizos).
  - **Siempre:** si la imagen está en blanco (cámara tapada o bloqueada), dice que la cámara no muestra imagen.
- **Prueba real con webcam (2026-10-24):** las primeras 8 capturas fueron la pantalla gris de "cámara tapada" de Windows y el robot, sin estas protecciones, decía "inmaduro 78 %". Con el cuadro guía, la rosa mostrada en un celular sale "óptimo" (62–65 %) y la cámara tapada se reconoce. Las fotos de la prueba quedaron en `datos/modo_foto/2026-10-24_022736/`.
- **Salida:** foto anotada (cajas del color de su estado, número, estado y confianza, conteo abajo; las fotos pequeñas se agrandan para que se lean) y en consola, por rosa, el estado, las probabilidades y los consejos de la finca (`tips` de RosaNet). Todo queda en `datos/modo_foto/<hora>/`.
- **Mini reporte:** mismo formato que la ronda (lo lee la app de la tablet), con un solo cuadrante `INV1-DEMO` e `id_ronda` `INV1_DEMO_<fecha_hora>`. Ojo: si se envía, la app lo va a mostrar como el último reporte.
- **Webcam:** OpenCV entrega BGR y se pasa a RGB antes del detector, como pide el equipo del modelo.
- **Límite:** sin profundidad no se sabe el tamaño de la cabeza, así que el modo foto no predice "lista mañana" (en la ronda sí).
- Con el modelo actual ("noche", sin terminar): de las 4 rosas de una escena de prueba con carteles, 3 salen como "dudosa" (óptimo con 51–53 %). Con una rosa de cerca, la reconoce mejor. Cuando el equipo suba el modelo completo a `modelos/`, este modo lo usa solo.

---

## 8. Eficiencia: varias rosas por foto

1. **Varias rosas por foto**: una foto puede dar 0, 1 o 15 rosas. El paso de candidatas (sección 7.2) saca todas las cajas, y RosaNet clasifica cada recorte por separado.
2. **Candidatas baratas**: la máscara de **rojo** (HSV) con la luz del robot es rápida. Si una foto no tiene nada rojo, no se llama al modelo y se ahorra tiempo.
3. **Zoom solo donde hace falta** (sección 3.3): pasada reducida → recortes en alta resolución solo en las zonas con candidatas.
4. **Lotes**: todos los recortes de una parada (las 4 fotos) se pasan juntos al modelo. RosaNet es pequeña (~1,2 M parámetros), así que en la Orin NX esto es rápido.
5. **Ver y caminar a la vez**: mientras el modelo procesa las fotos de la parada k, el robot ya camina a la k+1. Son dos hilos: uno de **captura** y uno de **análisis**, con una cola entre ellos.
6. **Respaldo** (poco probable que haga falta, porque la Orin NX corre RosaNet a bordo): en la ronda solo se toman y guardan fotos con su posición, y el análisis se hace al volver a la base.
7. **Medir tiempos**: cada etapa guarda cuánto tardó (hoja `Ronda`), para ver dónde está el cuello de botella.

**Hecho (punto 5, `ronda.AnalisisEnParalelo`, `percepcion.analisis_en_paralelo: true`):**
- El robot toma cada foto, la guarda y se la pasa a un hilo de análisis (detector + RosaNet + ubicación). No
  espera: sigue con la siguiente postura o camina a la siguiente parada. El hilo analiza en orden y escribe
  `detecciones.jsonl`.
- **Checkpoint seguro:** una parada se marca como hecha recién cuando se analizaron sus 4 fotos. Si se corta
  (batería, ventana cerrada, falla), lo ya fotografiado se termina de analizar antes de guardar; y una parada
  sin analizar se repite al continuar.
- **Con la acción física** (señalar óptimas, sección 1.1) el robot necesita el resultado de esa parada: lo
  espera al terminar las fotos, pero el análisis ya fue corriendo mientras posaba para las otras.
- Si el modelo falla en el hilo, el error llega al robot (no sigue como si nada) y queda en el log.
- **Medido en la simulación con carteles** (detector + RosaNet en CPU): mismas 142 rosas y mismo reporte;
  la ronda pasa de **62 s a 52 s** (−16 %). En el robot real lo que se gana es el tiempo del modelo por parada
  (~0,1–0,5 s por foto en la Orin NX según el equipo del modelo), que ahora se esconde detrás de posar y
  caminar.

---

## 9. Ubicación, altura y no contar dos veces

### 9.1 Dónde está el robot

- **Sim**: MuJoCo da la posición exacta.
- **Real**: la odometría del controlador (cuántos metros ha caminado) más **marcas impresas** (códigos AprilTag/ArUco en una hoja) al inicio de cada cama y cada 5 m. Las marcas corrigen el error acumulado y dicen en qué cama está. Son hojas pegadas en las camas, no hardware del robot.

### 9.2 Dónde está cada rosa (3D)

**Con profundidad:**
1. Se toma el centro de la caja de la rosa (u, v) y la profundidad en ese punto.
2. Se pasa de píxel a 3D con los datos de la cámara.
3. Se pasa de la cámara al mundo con la posición del robot, del cuello y de la cintura.

```
X = (u − cx) · Z / f        Y = (v − cy) · Z / f        Z = profundidad
```

**Sin profundidad (plan B):** se lanza el rayo desde la cámara por ese píxel y se corta con el **plano de la cama** (se conoce dónde está cada cama). Da el metro y la altura con un error razonable.

### 9.3 Qué sale en el reporte

| Campo | Cómo se calcula |
|-------|-----------------|
| cama | por la posición lateral del punto 3D |
| tramo | `metro // 5 + 1` |
| metro_en_cama | coordenada a lo largo de la cama |
| altura_m | coordenada vertical del punto |
| diametro_cm | ancho de la caja × Z / f (sirve para "lista mañana") |

### 9.4 No contar dos veces (deduplicar)

La misma rosa sale en 2 o 3 fotos (traslape entre paradas y entre las fotos media y alta).

- Si dos detecciones quedan a **menos de 8 cm** en 3D, son la **misma rosa**. Ojo: con 8–12 tallos por metro, dos rosas de verdad pueden quedar a menos de 8 cm, y a 2–3 m la profundidad puede errar unos cm. Por eso el radio queda en config (`dedup.radio_m`) y se revisa con la métrica de duplicados de la simulación (sección 16).
- Se queda la de **mejor confianza** y foto más cercana. Las otras se guardan como "vistas extra".
- **ID de rosa** = cuadrante + posición redondeada (`INV1-C07-T3-12.35-1.84`).
- **Noche siguiente**: se busca la rosa de ayer a menos de 8 cm. Así se arma la historia de tamaño para "lista mañana". Las rosas en óptimo se cortan, entonces desaparecen al otro día, y eso es normal.

---

## 10. Reporte Excel y JSON para el dashboard

El reporte lo lee el **dashboard** (CONTEXTO.md sección 2.0), que tiene dos vistas:
- **Coordinadores:** el estado de todo el campo, para organizar al personal.
- **Pantalla a la entrada del campo:** a qué cuadrantes deben ir hoy los operarios.

### 10.1 Archivos por ronda

```
datos/salida/reporte_INV1_2026-10-24.xlsx     ← para personas (y para el dashboard si lo prefiere)
datos/salida/reporte_INV1_2026-10-24.json     ← los mismos datos, para que el dashboard los lea fácil
```

- **Un archivo nuevo por noche.** Así nunca se intenta escribir sobre uno que alguien tenga abierto, que era el error de `Permission denied`.
- Además se guarda un `historial.csv` acumulado que **solo usa el código**.
- Si el archivo de la noche ya existe (o está abierto), se guarda como `reporte_INV1_2026-10-24_v2.xlsx` (y `_v2.json`) y se avisa. **Nunca se sobreescribe ni se cae.**

### 10.2 Hojas

**Hoja 1 – `Resumen_cuadrantes`** (la más importante para el dashboard)

| cuadrante_id | cama | tramo | desde_m | hasta_m | optimo | lista_manana | inmaduro | pasado | dudosa | total | prioridad | orden |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| INV1-C07-T3 | 7 | 3 | 10 | 15 | 4 | 6 | 21 | 1 | 2 | 34 | alta | 3 |

- `inmaduro` cuenta las inmaduras que **no** son "lista mañana" (así las columnas suman el total).
- **`prioridad` y `orden`** son para la **pantalla a la entrada del campo**: "¿a dónde voy hoy?".
  ```
  puntaje_cuadrante = optimo + 0,5 · lista_manana
  ```
  - `alta`: `optimo ≥ 3` (hay que cortar hoy) · `media`: hay alguna `optimo` o `lista_manana` · `baja`: no hay nada para cortar.
  - `orden` = 1 para el cuadrante con más puntaje, 2 para el siguiente, etc.
  - El umbral de 3 rosas queda en config (`reporte.optimo_prioridad_alta`) y hay que acordarlo con la finca.

**Hoja 2 – `Rosas_listas`** (óptimo y lista mañana, con ubicación)

| rosa_id | estado | cuadrante_id | cama | lado | metro_en_cama | altura_m | diametro_cm | confianza | foto | fecha_hora |
|---|---|---|---|---|---|---|---|---|---|---|

**Hoja 3 – `Todas_las_rosas`** (todas, para análisis)

**Hoja 4 – `Dudosas`** (confianza baja, para que una persona revise la foto)

**Hoja 5 – `Ronda`** (datos de la noche)

| campo | valor |
|---|---|
| inicio / fin | 2026-10-24 22:00 / 23:41 |
| caminos recorridos | 21 / 21 |
| fotos tomadas | 1.092 |
| rosas detectadas | 3.410 |
| obstáculos encontrados | 2 (INV1-C04-T2, INV1-C15-T6) |
| factor de color (tarjeta) | 1,04 / 1,00 / 0,93 |
| versión del modelo | (la que dé el equipo) |
| tiempos por etapa | captura X s, modelo Y s, … |

**Hoja 6 – `Diccionario`**: qué significa cada columna y cada estado. Sirve para la persona del dashboard.

### 10.3 Reglas del formato (acordar con el dashboard)

- Nombres de columnas en **minúscula, sin tildes y con guion bajo** (`lista_manana`), para que el dashboard los lea sin problemas.
- Los estados se llaman igual que en RosaNet y en el juego de la tablet (`inmaduro`, `optimo`, `pasado`), más `lista_manana` y `dudosa`.
- Decimales con **punto** dentro del archivo (Excel los muestra según el idioma del computador, pero el dato queda bien).
- Fechas en formato `YYYY-MM-DD HH:MM:SS`.
- Encabezados en negrita, filtros, ancho automático y colores por estado. Es solo visual: el dashboard lee los datos.

### 10.4 JSON para el dashboard

Mismos datos que el Excel, en un formato que una página web lee directo, sin librerías de Excel:

```json
{
  "id_ronda": "INV1_2026-10-24_220000",
  "fecha": "2026-10-24",
  "invernadero": "INV1",
  "inicio": "2026-10-24 22:00:00",
  "fin": "2026-10-24 23:41:00",
  "cuadrantes": [
    {"cuadrante_id": "INV1-C07-T3", "cama": 7, "tramo": 3, "desde_m": 10, "hasta_m": 15,
     "optimo": 4, "lista_manana": 6, "inmaduro": 21, "pasado": 1, "dudosa": 2, "total": 34,
     "prioridad": "alta", "orden": 3}
  ],
  "rosas_listas": [
    {"rosa_id": "INV1-C07-T3-12.35-1.84", "estado": "optimo", "cama": 7, "lado": "izq",
     "metro_en_cama": 12.35, "altura_m": 1.84, "diametro_cm": 5.1, "confianza": 0.87}
  ],
  "obstaculos": ["INV1-C04-T2"]
}
```

- El Excel y el JSON salen de la **misma tabla** en memoria, así que nunca dicen cosas distintas.
- Si la persona del dashboard prefiere solo uno de los dos, se apaga el otro en config (`reporte.formatos: [excel, json]`).
- Ya hecho (paso 4): el JSON trae además `dudosas` y `ronda` (los datos de la hoja `Ronda`). Cada rosa de `rosas_listas` trae `foto` y `fecha_hora`.
- `id_ronda` es el nombre de la carpeta de la ronda (invernadero + fecha + hora), así es único aunque se corra dos veces la misma noche.
- **Pendiente:** `foto` es una ruta dentro de la carpeta de la ronda en el robot. Si el dashboard quiere mostrar las fotos (por ejemplo, de las dudosas), hay que enviarlas también (pregunta 6 al dashboard, sección 19).

---

## 11. Envío al cuartel general sin WiFi constante

### 11.1 Bandeja de salida

```
datos/
├── salida/        ← reportes listos para enviar (.xlsx + .json)
├── enviados/      ← se mueven aquí cuando el dashboard confirma que llegó
└── pendientes.json
```

### 11.2 Lógica

```
cada 60 s:
    ¿hay conexión con el dashboard?  (hace un "ping" a su dirección)
       no → sigue esperando
       sí → por cada archivo en salida/:
               enviarlo
               ¿el dashboard respondió "recibido"?
                   sí → mover a enviados/
                   no → reintentar más tarde (espera 1, 2, 4, 8… min)
```

- Nada se borra hasta que el dashboard confirma.
- Si se envía dos veces el mismo, el dashboard lo reconoce por el nombre y el `id_ronda`, y no lo duplica.

### 11.3 Cómo enviarlo (decidir con el dashboard)

| Opción | Cómo |
|--------|------|
| A. API web del dashboard | `POST` con el JSON (y el Excel adjunto). Lo más limpio |
| B. Carpeta compartida (Drive / OneDrive) | El robot copia los archivos y el dashboard los lee de ahí. Lo más fácil para la demo |
| C. Correo | El robot lo manda como adjunto |

La dirección, usuario y clave van en un archivo **`.env`** que **no** se sube al repo.

En simulación, el WiFi "aparece" cuando el robot vuelve a la base.

### 11.4 Lo que quedó hecho (paso 5, `reporte/envio.py`)

- **Carpeta** (`envio.metodo: carpeta`, el que viene por defecto): copia a la carpeta compartida con nombre temporal y luego renombra, así el dashboard nunca ve un archivo a medias. Llegó = la copia quedó idéntica. Hay conexión = la carpeta existe (está montada o sincronizada). En la simulación la carpeta es `datos/dashboard_simulado/`.
- **API** (`envio.metodo: api`): `POST` del archivo (campo `archivo`, más `nombre`) con `Authorization: Bearer <ENVIO_TOKEN>`. Llegó = responde 200 o 201, o 409 si ya lo tenía. Hay conexión = el dashboard responde en `ENVIO_PING_URL` (o `ENVIO_URL`). **Hay que acordar este contrato con la persona del dashboard.**
- **Correo:** no está hecho.
- Sin conexión, los archivos esperan y **no** cuenta como intento. Si falla un envío con conexión, se reintenta en 1, 2, 4, 8… min, hasta `envio.espera_max_min` (60). El estado queda en `datos/pendientes.json`, así que sobrevive si se apaga el robot.
- Un reporte nuevo nunca usa el nombre de uno que ya está en `enviados/`, para no pisar en el dashboard uno que ya llegó.
- En el robot real se deja corriendo aparte: `python -m reporte.envio` (revisa cada `revisar_cada_s`). Con `--una-vez` hace un solo intento.
- Claves y rutas en `robot/.env` (plantilla: `robot/.env.ejemplo`).

---

## 12. Estructura del repo y cómo armarlo

### 12.1 No se crea un repo nuevo

Todo va dentro de la carpeta **`robot/`** del repo `Reto-Rosas-Hackaton`, que ya existe:
- `X2-Ultra.xml` y `meshes/` **ya están copiados** en `robot/`.
- Los scripts de la prueba anterior **ya están** en `robot/referencias/` (`jardin_10_plantas.py`, `scene_jardin.xml`). Sirven **de base**, pero se reparten en las carpetas nuevas. No se copian tal cual.
- RosaNet **ya está** en `robot/ml/`. **No hace falta submodule**: se importa directo (sección 7).
- Ya hay `requirements.txt`, `pytest.ini` (con `testpaths = tests`) y `tests/test_pipeline.py` (las pruebas del modelo). Se **suman** cosas, no se reemplazan.

### 12.2 Estructura

Lo marcado con `(ya existe)` no se toca, salvo para sumarle líneas.

```
Reto-Rosas-Hackaton/
├── .gitignore                   (ya existe) ← se le suman datos/ y .env
└── robot/
    ├── README.md                (ya existe) ← se le suma una sección "Ronda del robot"
    ├── requirements.txt         (ya existe) ← se le suman las dependencias del robot
    ├── pytest.ini               (ya existe)
    ├── PLAN_robot_rosas_X2.md   (este plan)
    ├── X2-Ultra.xml             (ya existe)
    ├── meshes/                  (ya existe)
    ├── referencias/             (ya existe) ← script de 10 plantas, solo de consulta
    ├── ml/                      (ya existe) ← RosaNet. Lo hace otra persona. NO SE TOCA
    ├── .env.ejemplo             ← plantilla de claves (el .env real no se sube)
    ├── escena_base.xml          ← piso, luces, guía, exclusión cabeza-torso (incluye X2-Ultra.xml)
    ├── config/
    │   └── config.yaml          ← modo sim/real, medidas, umbrales, cámara
    ├── sim/
    │   ├── escena_invernadero.py ← arma camas, rosas, piso difícil
    │   └── rosas.py             ← cómo se dibuja cada estado (figura o cartel)
    ├── cuerpo/                  ← (no se llama robot/ para no confundirse con la carpeta de arriba)
    │   ├── interfaz.py          ← lo que la ronda le pide al cuerpo (Cuerpo) y la foto con su pose (Captura)
    │   ├── posturas.py          ← las 4 posturas de cada parada
    │   ├── sim_backend.py       ← versión MuJoCo
    │   └── real_backend.py      ← versión robot real (para llenar con AimDK_X2)
    ├── navegacion/
    │   ├── plano.py             ← dónde queda cada cama y cada camino (ejes x/y del mundo)
    │   ├── ruta.py              ← paradas de cada camino (y después la serpiente)
    │   └── localizacion.py      ← en qué cama/tramo/metro voy
    ├── configuracion.py         ← lee config.yaml y los cambios de la línea de comandos
    ├── percepcion/
    │   ├── modelo_equipo.py     ← ÚNICO archivo que toca ml/: qué está listo y qué usar (sección 7.6)
    │   ├── candidatas.py        ← oráculo, máscara roja o detector del equipo → cajas
    │   ├── clasificador.py      ← adaptador a RosaNet + oráculo
    │   ├── zoom.py              ← recortes en alta resolución
    │   ├── geometria.py         ← píxel → 3D → cama/metro/altura
    │   ├── analisis.py          ← une candidatas + clasificador + geometría para cada foto
    │   ├── dedup.py             ← juntar la misma rosa
    │   └── madurez.py           ← reglas de "lista mañana"
    ├── reporte/
    │   ├── tabla.py             ← arma la tabla única de la ronda (cuadrantes, prioridad, hojas)
    │   ├── archivos.py          ← .xlsx y .json desde la tabla, nunca sobreescribe (_v2, _v3…)
    │   └── envio.py             ← bandeja de salida + reintentos
    ├── datos/                   ← NO se sube (en .gitignore)
    ├── tests/
    │   ├── test_pipeline.py     (ya existe, del modelo)
    │   ├── test_geometria.py
    │   ├── test_candidatas.py
    │   ├── test_clasificador.py
    │   ├── test_dedup.py
    │   ├── test_madurez.py
    │   ├── test_reporte.py
    │   └── test_envio.py
    ├── ronda.py                 ← recorrido: caminar, posar, fotografiar, analizar y guardar (datos/rondas/<id>/)
    ├── metricas.py              ← lo encontrado contra la verdad de la simulación
    ├── main.py                  ← arranca la ronda
    └── modo_foto.py             ← demo en vivo con una foto o la webcam (sección 7.5)
```

> **¿Por qué `escena_base.xml` va junto a `X2-Ultra.xml` y no en `sim/`?** `X2-Ultra.xml` dice `meshdir="meshes/"`, y MuJoCo busca esa carpeta al lado del archivo principal que se carga. Si el XML base queda en `sim/`, buscaría `sim/meshes/` y no los encontraría. (Igual que hoy hace `scene_jardin.xml` con `<include file="X2-Ultra.xml"/>`.)

### 12.3 Pasos para armarlo (Windows / PowerShell)

Todo se corre **desde la carpeta `robot/`**, como los comandos de `ml/`.

```powershell
# 1. Entrar a la carpeta del robot
cd C:\Users\laura\Downloads\rosas\Reto-Rosas-Hackaton\robot

# 2. Entorno de Python (si no existe ya el de la raíz del repo: ..\.venv)
py -m venv ..\.venv
..\.venv\Scripts\activate
py -m pip install torch torchvision          # o con CUDA, ver README
py -m pip install -r requirements.txt

# 3. Pesos de RosaNet: los entrega la persona del modelo en runs\rosanet\best.pt
#    (runs/ y *.pt no se suben al repo). Sin pesos, se usa el oráculo.

# 4. Probar
py main.py --modo sim --candidatas oraculo --clasificador oraculo
py -m pytest
```

### 12.4 `requirements.txt` (líneas que se suman)

El archivo ya trae `torch`, `torchvision`, `pillow`, `numpy`, `pyyaml`, `pypdf` y `pytest`. Se agregan:

```
mujoco>=3.2
opencv-python
openpyxl
requests
python-dotenv
```

### 12.5 `.gitignore` (líneas que se suman al de la raíz)

El de la raíz ya ignora `.venv/`, `__pycache__/`, `data/`, `descargas/`, `runs/` y `*.pt`. Se agregan:

```
datos/
.env
```

(No se ignora `*.png` en general: taparía imágenes que sí deben subirse, como las de `app-tablet/`. Las fotos de la ronda quedan dentro de `datos/`, que ya se ignora.)

> Los `meshes` pesan ~120 MB en total, y ningún archivo pasa de 100 MB, así que se suben normal. (Hay un archivo suelto de 1 byte, `meshes/meshes`, que sobra y se puede borrar.)

### 12.6 `config/config.yaml` (ejemplo)

```yaml
modo: sim                    # sim | real
percepcion:
  candidatas: auto           # auto | oraculo | color | detector_equipo
  clasificador: auto         # auto | oraculo | rosanet | detector_equipo
  margen_recorte: 0.10       # igual que --pad de ml/prepare_data.py
  tamano_min_px: 32          # igual que --min-size de ml/prepare_data.py
  # la confianza mínima ("seguro") la pone RosaNet (0,6); no se repite aquí
modelo_equipo:               # ver sección 7.6
  clasificador: {modulo: ml.predict, clase: RosePredictor, pesos: runs/rosanet/best.pt}
  detector: {modulo: ml.detect, clase: RoseDetector, pesos: runs/detector/best.pt, clasifica: false}
sim:
  rosas: figura              # figura (para oráculo) | cartel (para RosaNet)
  carteles_dir: ../app-tablet/assets/rosas
invernadero:
  id: INV1
  camas: 20
  largo_cama_m: 30
  ancho_cama_m: 1.0
  ancho_camino_m: 0.8
  tramo_m: 5
rosas:
  altura_min_m: 1.0
  altura_max_m: 2.0
  diametro_punto3_cm: 5.0    # A CALIBRAR
recorrido:
  paso_entre_paradas_m: 1.25 # era 2,5 (sección 16.1)
  velocidad_m_s: 0.3
  velocidad_dificil_m_s: 0.2
  giro_diagonal_rad: 1.13    # ~65° (era 35°, sección 16.1)
  inclinacion_alta_rad: -0.61
camara:
  ancho: 1920                # CONFIRMAR con el X2 real
  alto: 1080
  fov_h_grados: 70           # en MuJoCo se convierte a fovy (vertical)
  distancia_max_m: 3.5
  sim_ancho: 1280            # misma proporción 16:9 que la real, menos píxeles para ir rápido
  sim_alto: 720
madurez:
  p3_min_candidata: 0.30
  tamano_rel_min: 0.85
  puntaje_lista_manana: 0.60
  dias_max_lista_manana: 1.5
dedup:
  radio_m: 0.08
horario:
  inicio: "22:00"
  simular_noche: true
reporte:
  formatos: [excel, json]
  optimo_prioridad_alta: 3   # rosas en óptimo para que un cuadrante sea "alta"
envio:
  metodo: carpeta            # api | carpeta | correo (acordar con el dashboard)
  revisar_cada_s: 60
bateria:
  volver_a_base_pct: 25
```

---

## 13. La simulación paso a paso

### 13.1 Escena del invernadero (`sim/escena_invernadero.py`)

Se arma con `MjSpec` desde Python, como en el script de las 10 plantas: se carga `escena_base.xml` (que incluye `X2-Ultra.xml`, el punto guía, la exclusión cabeza-torso y `offwidth`/`offheight` de 1920 × 1080) y se le agrega todo lo demás:

1. **Piso** con mapa de alturas (desniveles) y mangueras al azar.
2. **Camas**: cajas bajas de 30 × 1 m con tierra.
3. **Rosales**: por cada metro de cama, 8–12 tallos con altura al azar entre 1,0 y 2,0 m. Tallos inclinados un poco y hojas en ramitas.
4. **Estructura**: postes cada 3 m y alambres guía, que también tapan la vista como en las fotos reales.
5. **Techo de plástico**: plano blanco translúcido (de noche casi no se ve).
6. **Luz**: luna muy tenue + linterna del robot (+ luces del invernadero, opcional).
7. **Marcas** AprilTag al inicio de cada cama y cada 5 m (texturas).

> Rendimiento: 20 camas × 30 m × 10 tallos son **6.000 rosas**, y eso es pesado. Para probar se usa `camas: 2` y `largo: 10`. La escena completa se carga **por camino**: solo las 2 camas que está viendo.

### 13.2 Cómo se dibuja cada estado (`sim/rosas.py`)

Hay dos formas de dibujar cada rosa (en config: `sim.rosas: figura | cartel`):

**a) Figura** (para el oráculo):

| Estado (verdad) | Forma | Color (RGB 0–1) | Tamaño cabeza |
|--------|-------|-----------------|---------------|
| inmaduro (punto 2) | elipsoide alargado (bala) + sépalos pegados | 0,40 0,02 0,05 (rojo oscuro) | 3,0–4,0 cm |
| inmaduro, lista_manana | elipsoide un poco más ancho, sépalos medio abiertos | 0,55 0,03 0,06 | 4,0–4,8 cm |
| optimo (punto 3) | copa: cono invertido + disco arriba, sépalos abajo | 0,75 0,04 0,08 (rojo vivo) | 4,8–5,5 cm |
| pasado | disco ancho y plano, pétalos abiertos, bordes oscuros | 0,60 0,05 0,07 + bordes 0,25 0,02 0,03 | 6–8 cm |

**b) Cartel** (para correr RosaNet de verdad, sección 7.4): un plano que siempre mira hacia el camino, del tamaño de la cabeza, con la textura de un recorte real de la categoría que toca (`app-tablet/assets/rosas/<categoria>/`). Para "lista mañana" se usan inmaduras grandes.

- Cada rosa guarda su **verdad** (estado, posición, diámetro) para medir aciertos.
- Las proporciones se sacan al azar con semilla, para repetir la misma escena (`--semilla`).
- **"Crecimiento"** entre noches simuladas: cada rosa avanza de estado según una velocidad al azar. Así se prueba la lógica de "lista mañana" con historia.

### 13.3 Recorrido (`main.py` en modo sim)

```
cargar config
armar escena
para cada camino en ruta_serpiente:
    entrar al camino
    para cada parada:
        caminar hasta la parada (punto guía)
        para cada postura (izq_media, izq_alta, der_media, der_alta):
            mover cintura y cabeza
            foto RGB + profundidad
            mandar a la cola de análisis
        guardar avance (checkpoint)
    salir del camino
volver a la base
armar tabla → Excel + JSON
"aparece WiFi" → enviar al dashboard
```

**Lo que guarda cada ronda** (hecho en el paso 2):

```
datos/rondas/INV1_2026-10-23_212231/
├── fotos/c01_p02_izq_alta.png        ← color
├── fotos/c01_p02_izq_alta_prof.png   ← profundidad en mm (PNG de 16 bits, 0 = sin dato)
├── capturas.jsonl                    ← una línea por foto: posición y ejes de la cámara, focal, robot, ángulos reales
└── verdad.json                       ← solo en sim: cada rosa con estado, posición y diámetro
```

### 13.4 Profundidad en MuJoCo

```python
render.enable_depth_rendering()   # activa profundidad
prof = render.render()            # en metros
render.disable_depth_rendering()  # vuelve a color
```

---

## 14. Modo robot real

Lo que cambia (todo en `robot/real_backend.py`):

| Pieza | Qué hay que hacer |
|-------|-------------------|
| Locomoción | Llamar al controlador oficial de AgiBot: avanzar, parar, girar. **Revisar la documentación oficial del SDK AimDK_X2** (compatible con ROS). |
| Cabeza y cintura | Mandar ángulos por la API oficial, con límites de velocidad. |
| Cámara | Leer RGB + profundidad de la cámara de la cabeza (driver oficial). Si la unidad no trae RGB-D, solo RGB y plan B de la sección 9.2. |
| Centrado y obstáculos | LiDAR 3D (si la unidad lo trae). |
| Pose | Odometría oficial + corrección con AprilTags. |
| Modelo | RosaNet en la **Orin NX** del robot (con CUDA). Copiar `runs/rosanet/best.pt` al robot. |
| Batería | Leer el nivel. Si baja de 25%, volver a la base (o cambiar la batería). |
| Parada de emergencia | Siempre activa. Una persona debe poder detenerlo. |

**Antes de la primera prueba real:**
1. Probar con el robot **colgado** o en un soporte, solo cabeza y cintura.
2. Probar caminando en un pasillo de 80 cm hecho con cajas, **sin rosas**.
3. Probar con fotos de rosas impresas pegadas a 1–2 m de altura.
4. Medir de verdad la cámara (resolución, campo de visión) y el ancho del robot, y actualizar `config.yaml`.
5. Confirmar qué sensores trae la unidad (¿LiDAR? ¿RGB-D?), porque hay una versión del X2 Ultra sin ellos.

### 14.1 Esqueleto hecho (`cuerpo/real_backend.py`)

`CuerpoReal` cumple la misma interfaz que la simulación, así la ronda, la percepción y el reporte no cambian.
Con `modo: real`, `python main.py` muestra la lista de lo que falta probar en el robot.

- **Hecho y probado sin robot:** pasar la nube del LiDAR a "obstáculo alto / bajo" (mismas reglas que los
  rayos de la simulación), la profundidad de milímetros a metros, la cámara de ROS a la convención de la
  percepción (ROS mira hacia +z con y abajo; la percepción hacia −z con y arriba), el campo de visión desde
  `camera_info`, la velocidad para ir a un punto y la lectura de la batería.
- **Falta probar con el robot delante:** cada método dice qué tópico o servicio del SDK usa, con qué mensaje
  y en qué modo, y por ahora levanta `NotImplementedError`.

Lo que dice la documentación oficial (AimDK_X2 1.1.0, https://x2-aimdk.agibot.com/en/latest/), ROS 2 Humble:

| Pieza | Tópico / servicio | Nota |
|-------|-------------------|------|
| Tomar el control | `SetMcInputSource` (fuente `sdk_rosas`, prioridad 40) | el control remoto siempre gana |
| Modo | `SetMcAction`: `STAND_DEFAULT` (de pie y camina), `HEAD_ONLY` (cabeza) | |
| Caminar | `/aima/mc/locomotion/velocity` (`McLocomotionVelocity`, 50 Hz) | lazo abierto; sin comandos 200 ms, frena |
| Cabeza | `/mc/upper_body_command` (`head_pos` = [yaw, pitch]) | solo en modo `HEAD_ONLY` |
| Cintura | `/aima/hal/joint/waist/command` (bajo nivel) | sin protección por tiempo |
| Cámara | `/aima/hal/sensor/rgbd_head_front/rgb_image` y `depth_image` | **1280 × 720**, profundidad en mm |
| LiDAR | `/aima/hal/sensor/lidar_chest_front/lidar_pointcloud` | `PointCloud2`, 10 Hz, en el pecho |
| Batería | `/aima/hal/pmu/state` (`battery_remaining_capacity_percentage`) | 1 Hz |
| Luces | `SetPmuLed` | solo la tira LED del pecho |
| Posición | módulo SLAM / navegación | **opcional**: se pide a soporte de AgiBot |

**Lo que esto cambia en el plan (riesgos):**
1. **La cámara RGB-D de la cabeza es de 1280 × 720.** En la simulación, con esa resolución la cobertura baja
   de **90 % a 68 %** (417 rosas descartadas por medir menos de 32 px). Opciones:
   a) usar la cámara estéreo de la cabeza (2064 × 1552, 10 Hz, sin profundidad) para el color y la RGB-D
   solo para la profundidad (hay que calibrar una contra la otra);
   b) que el equipo del modelo entrene RosaNet también con recortes de 20–32 px;
   c) más fotos por parada, más cerca de la cama (más tiempo por noche).
2. **En el X2 Ultra original la cabeza solo gira (yaw).** La inclinación la hace toda la cintura, y esta llega
   a ±0,31 rad, no a los −0,61 de la postura alta. En el "X2 Ultra (nueva versión)" la cabeza sí inclina.
   Hay que saber cuál tenemos.
3. **Cabeza y caminar van en modos distintos** (`HEAD_ONLY` / `STAND_DEFAULT`): en cada parada hay que
   cambiar de modo y volver. La cintura solo tiene control de bajo nivel: preguntar a AgiBot cómo moverla con
   el robot en equilibrio.
4. **No hay foco en la cabeza.** Para la acción física (sección 1.1) hay que montar uno. Mientras tanto, la tira
   LED del pecho puede parpadear cuando hay una rosa para cortar.
5. **La posición del robot** sale del SLAM opcional o de odometría + marcas AprilTag: hay que pedirlo o armarlo.

---

## 15. Fallas y recuperación

| Falla | Qué hace el sistema |
|-------|---------------------|
| Se cae o se traba | Para, guarda y reporta el último tramo terminado |
| Se va la energía o el programa se cierra | Al arrancar lee `checkpoint.json` y sigue desde el último tramo |
| Batería baja | Vuelve a la base, carga y sigue (ronda en dos partes) |
| No encuentra una marca AprilTag | Sigue por odometría y lo marca "posición aproximada" |
| Obstáculo en el camino | Para, espera 30 s, si sigue ahí salta al siguiente camino y lo reporta |
| El modelo falla en una foto | La guarda en `Dudosas` y sigue |
| Excel abierto / sin permiso | Guarda con otro nombre (`_v2`), nunca se cae |
| Sin WiFi | Guarda en la bandeja de salida y reintenta |
| Foto muy oscura | Reintenta una vez; si sigue oscura la marca en `Dudosas` |

Todo queda en un **log** (`datos/logs/ronda_YYYY-MM-DD.log`).

**Hecho (checkpoint, `ronda.py`):** después de cada parada se guarda `datos/rondas/<id>/checkpoint.json` con las paradas hechas y la escena (semilla, tipo de rosas, caminos).
- `python main.py --parar-despues N` simula batería baja: después de N paradas el robot sigue de frente hasta salir del camino y vuelve a la base.
- `python main.py --continuar` (o `--continuar <id_ronda>`) sigue la última ronda a medias: retoma las detecciones ya hechas, vuelve a planear la serpiente con los caminos que faltan y salta las paradas ya hechas. No repite fotos.
- Si se cierra el programa o la ventana a mitad de ronda, el avance también queda guardado.
- El reporte y el envío se hacen solo cuando la ronda termina.

**Hecho (log y batería, paso 6):**
- **Log:** todo lo que sale en pantalla queda, con la hora, en `datos/logs/ronda_<id_ronda>.log` (`registro.py`).
  Al seguir una ronda con `--continuar` se agrega al mismo archivo. Si el programa se cae, el error completo
  queda en el log (o en `datos/logs/error_<fecha>.log` si todavía no había ronda).
- **Batería:** antes de entrar a cada camino y antes de cada parada el robot lee `nivel_bateria()`. Si está por
  debajo de `recorrido.bateria_min_pct` (25 %), guarda el avance, sale del camino y vuelve a la base. Lo que
  falta se termina con `python main.py --continuar` después de cargar. La hoja Ronda dice con cuánta batería
  llegó a la base.
- **En la simulación** la batería baja con el tiempo del robot: 0,8 % por minuto (X2: ~500 Wh, ~2 h de uso).
  Una ronda completa de prueba gasta ~10 %. `python main.py --bateria 30` lo muestra: vuelve a la base a las
  13 paradas con 25 % y, con `--continuar`, termina el resto (cobertura 92 %).
- **En el robot real** `nivel_bateria()` lee `battery_remaining_capacity_percentage` de `/aima/hal/pmu/state`
  (sección 14.1; falta probarlo en el robot).
- **Pendiente:** que el robot siga solo después de cargar (hoy se relanza con `--continuar`), y calcular la
  reserva según lo lejos que esté de la base en un invernadero grande (hoy es un 25 % fijo).

---

## 16. Pruebas y métricas

### 16.1 Métricas en simulación (hay verdad para comparar)

| Métrica | Fórmula | Meta inicial |
|---------|---------|--------------|
| Cobertura | rosas vistas / rosas que existen | ≥ 95% |
| Precisión óptimo | aciertos óptimo / detectadas óptimo | ≥ 90% (con oráculo); con carteles + RosaNet se reporta lo que salga |
| Recall óptimo | aciertos óptimo / óptimo reales | ≥ 90% (con oráculo) |
| Candidatas por color | rosas encontradas por la máscara roja / rosas que hay en la foto | se mide con carteles |
| Duplicados | rosas contadas 2 veces / total | ≤ 2% |
| Error de altura | promedio de \|altura medida − real\| | ≤ 5 cm |
| Error de metro | promedio de \|metro medido − real\| | ≤ 10 cm |
| Tiempo de ronda | fin − inicio | ≤ 2 h |

**Primeros resultados (paso 3, oráculo, camino 1 de la escena de prueba, semillas 7 y 11):**

| Paradas cada | Mínimo 32 px | Cobertura | Duplicados | Error altura | Error metro | Tiempo sim |
|---|---|---|---|---|---|---|
| 2,5 m (plan) | sí | **47 %** | 0 % | 0,5 cm | 1,4 cm | 10 s |
| 1,25 m | sí | 72–75 % | 0 % | 0,5 cm | 1,3 cm | 16 s |
| 1,0 m | sí | 79 % | 0 % | 0,5 cm | 1,3 cm | 19 s |
| 2,5 m | no | 86–87 % | 0 % | 0,4 cm | 1,6 cm | 10 s |

- La ubicación y la deduplicación funcionan muy bien (con profundidad perfecta de la simulación; la real tendrá más error).
- **La cobertura la limita el tamaño en píxeles:** con paradas cada 2,5 m, más de la mitad de las rosas solo se ven lejos y quedan de menos de 32 px. El ~13 % restante está tapado por tallos y hojas.
- Paradas más seguidas suben la cobertura pero alargan la ronda. **Decisión: paradas cada 1,25 m** (~75 % de cobertura). Son 25 paradas por camino de 30 m en vez de 13, y la ronda pasa de ~95 min a ~2 h 10 min, así que se hace en dos partes con cambio de batería (sección 4.4).
- La última parada de cada camino (al final de la cama) no ve rosas, porque las fotos miran en diagonal hacia adelante. Se puede quitar o cambiar por fotos mirando hacia atrás. (Con el giro de 65° ya ve algunas.)

**Mejora de la cobertura (después del paso 5).** Se midió, rosa por rosa, por qué no se veía. Con un solo camino, el 16 % solo se veía de menos de 32 px (casi todas en la mitad lejana de la cama), el 4 % nunca entraba en una foto y el ~7 % eran fallos a propósito del oráculo. Ninguna quedaba tapada en todas las fotos. Se probaron varias soluciones (oráculo, semillas 7 y 11):

| Solución | Cobertura | Fotos por camino | Tiempo de ronda |
|---|---|---|---|
| Base: giro 35°, un camino (lo que se medía antes) | 73–76 % | 36 | igual |
| A. Medir la ronda por **todos los caminos** (cada cama vista por sus dos lados, como en el invernadero real) | 87–89 % | 36 | igual |
| B. Giro de **55°** en vez de 35°, un camino | 83–90 % | 36 | igual |
| C. 8 fotos por parada (35° + 80°), un camino | 93–94 % | 72 | **el doble** |
| **D. Todos los caminos + giro 65°** | **95–97 %** | 36 | **igual** |
| D con paradas cada 1,67 m | 89–94 % | 28 | ~1 h 50 min: cabe en una batería |
| D con paradas cada 2,0 m | 80–82 % | 24 | ~1 h 35 min |

**Decisión: D** (giro 65°, paradas cada 1,25 m, ronda por todos los caminos). Si la batería no alcanza y no se puede cambiar a mitad de ronda, la opción con paradas cada 1,67 m cabe en una carga perdiendo unos 5 puntos.

**Rosas mal ubicadas.** Con la ronda completa aparecían 5–7 "rosas falsas": una rosa real ubicada hasta 65 cm más cerca porque una hoja o un tallo tapaba más de la mitad del centro de su caja, y la mediana de la profundidad tomaba la hoja. Ahora `profundidad_caja` elige el grupo de profundidades **más lejano** que ocupe al menos el 20 % del centro de la caja. Resultado: 0 falsas, sin perder cobertura. **Hay que validarlo con la cámara RGB-D real**, que tiene más ruido que la simulación.

**Resultado actual (`python main.py`, semillas 7 y 11):** cobertura **94–95 %**, 0 % duplicados, 0 falsas, error de altura 0,5 cm y de metro 0,9 cm, 108 fotos en ~45 s de simulación. El ~5 % que falta son casi todo fallos a propósito del oráculo (sin ellos se podría ver el ~98 %).

Ejemplo de precisión: el robot dice que hay 50 rosas en óptimo y 45 de verdad lo están.

```
precisión = 45 / 50 = 0,90 = 90%
```

**Invernadero completo (paso 9):** 6.031 rosas, cobertura 95 %, 0 duplicados, 0,4 % falsas, error de altura 0,5 cm.
La ronda dura 2 h sin señalar, 4 h 46 min señalando cada óptima y **2 h 18 min señalando solo en los 10 primeros
cuadrantes** (lo que queda en uso, sección 4.5).

> Las métricas con oráculo miden **el robot** (recorrido, ubicación, duplicados, reporte). Las métricas de RosaNet las mide la persona del modelo con `ml/evaluate.py`. Con carteles se mide **todo junto**, que es lo más honesto para el pitch.

### 16.2 Pruebas pequeñas (`tests/`)

Se suman a `tests/test_pipeline.py`, que ya existe y es del modelo (no se toca).

- `test_geometria`: un píxel conocido da el punto 3D esperado.
- `test_candidatas`: una imagen con 3 círculos rojos da 3 cajas; una sin rojo da 0.
- `test_clasificador`: el recorte lleva 10% de margen y la salida de RosaNet (`1_inmaduro`…) se traduce a `inmaduro`… (con un RosaNet de pesos al azar, como hace `test_pipeline.py`).
- `test_dedup`: dos detecciones a 5 cm quedan en una sola rosa.
- `test_madurez`: los dos ejemplos de la sección 2.4 dan "lista mañana".
- `test_reporte`: el Excel tiene las 6 hojas y las columnas acordadas, el JSON tiene los mismos números, nunca sobreescribe y si el archivo está abierto usa `_v2`.
- `test_envio`: sin WiFi no borra nada ni cuenta intentos; con WiFi mueve a `enviados/`; los reintentos esperan 1, 2, 4 min; enviar dos veces no duplica; API con respuesta 500 y luego 201.

```powershell
py -m pytest
```

---

## 17. Cronograma de 10 horas

Prioridad 1: **un camino de punta a punta lo antes posible** (escena fea pero completa → fotos → rosas → Excel/JSON → "envío"). Después, lo que suma puntos en la demo en vivo (RosaNet sobre carteles y modo foto). Lo bonito de la escena va al final.

| Hora | Qué | Listo cuando… |
|------|-----|---------------|
| 0:00–0:30 | Carpetas dentro de `robot/`, `config.yaml`, `escena_base.xml`, líneas nuevas de `requirements.txt` y `.gitignore` | `py main.py` carga el robot |
| 0:30–1:30 | Escena mínima (1 camino, 2 camas de 10 m, rosas como figuras en los 4 estados) + `cuerpo/sim_backend.py` (caminar con el punto guía de `referencias/`) + 4 posturas + fotos RGB + profundidad | Guarda las fotos de un camino |
| 1:30–2:45 | `candidatas.py` y `clasificador.py` en modo oráculo + `geometria.py` + `dedup.py` | Lista de rosas con cama, metro y altura |
| 2:45–3:30 | `madurez.py` + `reporte/tabla.py` + `reporte/archivos.py` | **Primera ronda de punta a punta** con el Excel y el JSON |
| 3:30–4:00 | `reporte/envio.py` (bandeja + reintentos, WiFi simulado) | Se mueve a `enviados/` |
| 4:00–5:30 | Carteles con fotos reales + candidatas por color + adaptador a RosaNet | **RosaNet corre sobre la simulación** |
| 5:30–6:30 | `modo_foto.py` (foto suelta; webcam si alcanza) | Una foto nueva da cajas, estados y tips |
| 6:30–7:45 | Escena completa: varios caminos, ruta en serpiente, postes, mangueras, checkpoint, prioridad por cuadrante | Ronda de varios caminos |
| 7:45–8:45 | Métricas + arreglos | Métricas en consola |
| 8:45–9:30 | README, `cuerpo/real_backend.py` con funciones vacías y comentadas | Se entiende qué falta para el real |
| 9:30–10:00 | Ensayo de la demo (ronda + modo foto + dashboard) | Se puede mostrar |

**Si se acaba el tiempo, se deja para después (en este orden):**
1. Piso con desniveles (dejar solo mangueras).
2. Crecimiento entre noches (dejar "lista mañana" sin historia).
3. Hilos de captura y análisis en paralelo.
4. AprilTags en la simulación.
5. Webcam en el modo foto (dejar solo foto desde archivo).

> Los **carteles** y el **modo foto** ya no están en la lista de cosas que se pueden dejar: sin ellos el prototipo no responde a los casos en vivo del jurado.

**Durante el día, coordinar con:**
- **Persona del modelo** → que entregue `runs/rosanet/best.pt` **antes de la hora 4:00**. Preguntar también si piensa hacer un detector (sección 19). Si los pesos no llegan, se sigue con el oráculo y se avisa.
- **Persona del dashboard** → columnas, JSON o Excel, y cómo recibe los archivos, **antes de la hora 2:45** (sección 19).

---

## 18. Riesgos y decisiones pendientes

| Riesgo | Impacto | Qué hacer |
|--------|---------|-----------|
| De noche no hay luz suficiente sin hardware | **Alto**: el color define punto 2 vs 3 | Decidir: luces del invernadero, luz del X2 o lámpara (sección 6) |
| El modelo no reconoce rosas de la simulación | Alto | Oráculo primero, "carteles" con fotos reales en la hora 4:00 |
| RosaNet solo clasifica, no encuentra las rosas | Alto | Candidatas por máscara roja (sección 7.2). Se pegan o se parten rosas: la profundidad y la dedup lo mitigan. Preguntar si el equipo hará un detector |
| La demo en vivo pide responder a casos nuevos | **Alto**: 25 pts de "Funcionamiento" | Modo foto (sección 7.5) con el mismo pipeline del robot |
| El robot no "actúa" sobre el entorno | **Alto**: 15 pts de "Pertinencia". CONTEXTO decidió que el robot **señala físicamente** cada cuadrante | **Decisión pendiente** (ver abajo) |
| La unidad X2 es la versión sin LiDAR ni RGB-D | Medio | Plan B sin profundidad (9.2) + odometría y marcas para ir centrado |
| Pocas fotos de "pasado" (2) | Medio | Avisar al equipo del modelo; pedir más fotos |
| 8 fotos en dos carpetas a la vez | Medio | Confirmar con el equipo del modelo que etiquetan **por rosa** (cajas), no por foto |
| Fotos del zip de día y a contraluz; el robot opera de noche | Alto | Pedir fotos de noche con luz artificial para entrenar |
| Cámara real con menos resolución de la supuesta | Medio | Bajar `distancia_max_m` y poner paradas más seguidas |
| Cobertura: con paradas cada 2,5 m solo se veía el 47 % (medido en sim, sección 16.1) | Alto → **resuelto en sim** | Paradas cada 1,25 m + giro de 65° + ronda por todos los caminos: ~95 %. Falta medirlo con RosaNet real (carteles) y en el invernadero |
| **RosaNet confunde inmaduras con óptimas cuando el fondo es oscuro** (medido, sección 7.7) | **Alto**: es el error más costoso (cortar en punto 2) y de noche el fondo es oscuro | Hecho del lado del robot: fondo claro con la profundidad (sección 7.8; en sim, de 35–41 % a 51–53 % de aciertos en "óptimo", pero pierde óptimas). Pendiente: reentrenar con fondos oscuros, luces del invernadero, validar con fotos reales de noche y decirlo como límite en el pitch |
| Ronda de ~2 h 10 min con paradas cada 1,25 m | Medio | Ronda en dos partes con cambio de batería y checkpoint (secciones 4.4 y 15) |
| Batería no alcanza para todo el invernadero (~2 h y la ronda dura ~95 min) | Medio | Ronda en dos partes con checkpoint, o cambiar la batería |
| Camino real más difícil que lo simulado | Alto en real | Depende del controlador oficial; probar en pasillo de prueba |
| Robot de 58 cm en camino de 80 cm | Medio | Brazos pegados, caminar centrado, velocidad baja |
| Valores de "lista mañana" sin datos reales | Medio | Calibrar con un experto del cultivo y con la historia de varias noches |
| API del X2 real desconocida | Alto en real | Leer la documentación del SDK AimDK_X2 antes de llenar `real_backend.py` |

### Decisión pendiente: ¿qué acción física hace el robot?

CONTEXTO.md (registro de decisiones) dice que el robot **señala físicamente** el estado de cada cuadrante. Este plan solo detecta y reporta, y de noche no hay operarios que vean una luz. El jurado va a preguntar "¿por qué un robot y no una cámara fija?". Opciones, sin hardware extra:

| Opción | Qué hace | Ventaja | Problema |
|--------|----------|---------|----------|
| A. Apuntar con la cabeza y la linterna | En cada rosa en óptimo, gira la cabeza hacia ella y la ilumina un momento (y se guarda esa foto en el reporte) | Se ve en la demo y en la simulación; usa lo que ya tiene | De noche nadie lo ve; es más una demostración que una ayuda |
| B. Ronda corta de madrugada | Al final de la ronda, se para en la entrada de los cuadrantes de prioridad alta y señala con el brazo o la luz cuando llegan los operarios | Une el robot con la pantalla de la entrada | Más tiempo de batería; los operarios comparten el pasillo |
| C. Solo el dashboard | La "acción" es el reporte y la pantalla de la entrada | Lo más simple | El jurado puede decir que el robot es accesorio |

Recomendación: **A** para la demo (se ve el robot "actuar"), y explicar **B** como el siguiente paso. Hay que decidirlo con el equipo.

---

## 19. Preguntas para el equipo del modelo y para el dashboard

### Para la persona del modelo (RosaNet)

**Respondido en el pull del 2026-10-23 (`robot/CLAUDE.md`):** hay pesos en git (`modelos/rosanet.pt`, `modelos/detector_rosas.pt`), hay detector (YOLO11n, `ml.detect.RoseDetector`), el margen del recorte es 15 %, tarda ~86 ms por foto con GPU y ~540 ms con CPU, se entrenó solo con fotos de día y `seguro` sigue siendo confianza ≥ 0,6.

Lo que falta preguntar o pedir:

1. **Fondo oscuro (hallazgo del robot, sección 7.7):** con el margen del recorte negro, como el de una foto de noche, RosaNet llama "óptimo" a 14–33 de 47 inmaduras (con la foto original, a 2 de 47). No hay fotos de noche, pero ¿se puede reentrenar oscureciendo el fondo de las fotos de día a propósito (aumento de datos)? **Avisar** además que el robot ya aclara el fondo con la profundidad antes de pasarle el recorte (sección 7.8): la red recibe recortes editados.
2. ¿Puede agregar una función para clasificar **varios recortes de una vez** (lote)? Si no, el robot llama uno por uno.
3. ¿Qué recortes quedaron fuera del entrenamiento? Los carteles de la simulación usan los de `app-tablet/assets/rosas/`, que la red ya vio: las métricas con carteles son optimistas.
4. **Rosas pequeñas:** en los recortes de 50 px de ancho, 10 de 47 inmaduras salen como óptimas (en la foto original, 2). ¿Se puede entrenar también con recortes pequeños?
5. `3_pasado` no funciona (solo 2 fotos). ¿Hay planes para más ejemplos?

### Para la persona del dashboard

1. ¿Prefiere leer **JSON**, Excel o los dos? (El robot puede dar los dos con los mismos datos.)
2. ¿Cómo quiere recibir los archivos? (API, carpeta compartida, correo)
3. ¿Le sirven el nombre `reporte_INV1_YYYY-MM-DD` y las 6 hojas / los campos del JSON?
4. ¿Qué columnas necesita sí o sí para la **vista de coordinadores** y para la **pantalla de la entrada**? ¿Le sirven `prioridad` y `orden`?
5. ¿El dashboard responde "recibido" para saber que llegó?
6. ¿Necesita las fotos también (por ejemplo, de las dudosas), o solo los datos?
7. ¿Cómo identifica los invernaderos y las camas? (Que coincida con `INV1-C07-T3`.)

---

*Fin del plan.*
