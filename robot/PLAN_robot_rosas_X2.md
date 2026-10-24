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
| izq_media | +35° | 0° | 0,9–1,6 m |
| izq_alta | +35° | −35° (arriba) | 1,4–2,2 m |
| der_media | −35° | 0° | 0,9–1,6 m |
| der_alta | −35° | −35° (arriba) | 1,4–2,2 m |

> **Comprobado en la simulación:** "mirar hacia arriba" es un ángulo **negativo**, en la cabeza y en la cintura. El giro lo hace la cintura y la inclinación primero la cabeza (hasta −0,40) y el resto la cintura (`cuerpo/posturas.py`). Con −0,61 pedidos, la cámara queda mirando **~38° hacia arriba** y **35° hacia el lado**: la cintura cede un poco por el peso del torso. No importa, porque cada foto guarda la pose **real** de la cámara. La inclinación de cintura se hace **solo con el robot quieto**, por equilibrio.
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
| Sim con carteles o robot real, **hoy** (solo RosaNet) | máscara roja | RosaNet |
| Después del pull, con el detector y sus pesos | **detector del equipo** | RosaNet, o el detector si `clasifica: true` |
| Faltan los pesos de RosaNet | — | sim: oráculo (con aviso) · real: **error**, no adivina |

- El robot reconoce el detector cuando existen el módulo y los pesos que dice `modelo_equipo.detector` en el config (hoy `ml.detect`, `RoseDetector`, `runs/detector/best.pt`: **nombres supuestos**, confirmar con el equipo). Si el equipo usa otros nombres, **solo se cambia el config**.
- Los pesos (`*.pt`) no se suben a git: después del pull hay que **copiarlos** a la ruta del config (en el PC y en el robot).
- Lo único que puede tocar código es el **formato de salida** del detector: se traduce en una sola función del adaptador (`percepcion/clasificador.py`) al contrato de 7.3.
- `py main.py` imprime qué está listo, qué no y por qué, y qué va a usar la ronda.

### 7.5 Modo foto: para la demo en vivo

En la presentación el jurado **pone a prueba el prototipo con casos evaluados en ese momento** (CONTEXTO.md sección 1, "Funcionamiento y evidencia", 25 pts). Una ronda con oráculo no responde a una rosa que traiga el jurado. Por eso hay un modo aparte:

```powershell
py modo_foto.py foto_del_jurado.jpg      # o --webcam
```

- Pasa la foto por **el mismo pipeline del robot**: candidatas por color → recorte → RosaNet → "lista mañana" (sin historia) → reporte.
- Muestra la foto con las cajas pintadas por estado, la confianza y los **tips** que ya trae RosaNet.
- Genera un mini reporte (Excel + JSON) como si fuera un cuadrante, para que se vea en el dashboard.
- Si hay tiempo, el mismo modo puede poner la foto como cartel en la simulación y hacer que el robot "la encuentre".

---

## 8. Eficiencia: varias rosas por foto

1. **Varias rosas por foto**: una foto puede dar 0, 1 o 15 rosas. El paso de candidatas (sección 7.2) saca todas las cajas, y RosaNet clasifica cada recorte por separado.
2. **Candidatas baratas**: la máscara de **rojo** (HSV) con la luz del robot es rápida. Si una foto no tiene nada rojo, no se llama al modelo y se ahorra tiempo.
3. **Zoom solo donde hace falta** (sección 3.3): pasada reducida → recortes en alta resolución solo en las zonas con candidatas.
4. **Lotes**: todos los recortes de una parada (las 4 fotos) se pasan juntos al modelo. RosaNet es pequeña (~1,2 M parámetros), así que en la Orin NX esto es rápido.
5. **Ver y caminar a la vez**: mientras el modelo procesa las fotos de la parada k, el robot ya camina a la k+1. Son dos hilos: uno de **captura** y uno de **análisis**, con una cola entre ellos.
6. **Respaldo** (poco probable que haga falta, porque la Orin NX corre RosaNet a bordo): en la ronda solo se toman y guardan fotos con su posición, y el análisis se hace al volver a la base.
7. **Medir tiempos**: cada etapa guarda cuánto tardó (hoja `Ronda`), para ver dónde está el cuello de botella.

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
  giro_diagonal_rad: 0.61    # ~35°
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
- La última parada de cada camino (al final de la cama) no ve rosas, porque las fotos miran en diagonal hacia adelante. Se puede quitar o cambiar por fotos mirando hacia atrás.

Ejemplo de precisión: el robot dice que hay 50 rosas en óptimo y 45 de verdad lo están.

```
precisión = 45 / 50 = 0,90 = 90%
```

> Las métricas con oráculo miden **el robot** (recorrido, ubicación, duplicados, reporte). Las métricas de RosaNet las mide la persona del modelo con `ml/evaluate.py`. Con carteles se mide **todo junto**, que es lo más honesto para el pitch.

### 16.2 Pruebas pequeñas (`tests/`)

Se suman a `tests/test_pipeline.py`, que ya existe y es del modelo (no se toca).

- `test_geometria`: un píxel conocido da el punto 3D esperado.
- `test_candidatas`: una imagen con 3 círculos rojos da 3 cajas; una sin rojo da 0.
- `test_clasificador`: el recorte lleva 10% de margen y la salida de RosaNet (`1_inmaduro`…) se traduce a `inmaduro`… (con un RosaNet de pesos al azar, como hace `test_pipeline.py`).
- `test_dedup`: dos detecciones a 5 cm quedan en una sola rosa.
- `test_madurez`: los dos ejemplos de la sección 2.4 dan "lista mañana".
- `test_reporte`: el Excel tiene las 6 hojas y las columnas acordadas, el JSON tiene los mismos números, nunca sobreescribe y si el archivo está abierto usa `_v2`.
- `test_envio`: sin WiFi no borra nada; con WiFi mueve a `enviados/`.

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
| Cobertura: con paradas cada 2,5 m solo se veía el 47 % (medido en sim, sección 16.1) | Alto → **decidido** | Paradas cada 1,25 m (~75 %). Falta confirmar con el equipo del modelo si RosaNet lee bien rosas de menos de 32 px, que subiría la cobertura sin alargar la ronda |
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

Lo que ya se sabe leyendo `robot/ml/`, y no hace falta preguntar: es una CNN propia que **clasifica un recorte** (no detecta), devuelve las 3 clases `1_inmaduro`, `2_optimo` y `3_pasado`, entrega **todas las probabilidades**, usa entrada de 224 × 224, recortes con 10% de margen y mínimo 32 px, y `seguro` con confianza ≥ 0,6. Se carga con `RosePredictor(ckpt)`.

1. ¿Cuándo hay unos pesos `best.pt` que se puedan usar? (Hacen falta antes de la hora 4:00 del cronograma.)
2. ¿Piensa hacer un **detector** (por ejemplo, YOLO) que encuentre las rosas en la foto? Si no, el robot usa la máscara roja.
3. ¿Puede agregar una función para clasificar **varios recortes de una vez** (lote)? Si no, el robot llama uno por uno.
4. ¿Qué recortes quedaron en **test** (que el modelo nunca vio)? Esos son los que se usan para los carteles de la simulación cuando se mide.
5. ¿Cuánto tarda por recorte y en qué computador?
6. ¿Lo entrenaron solo con fotos de día? ¿Se pueden agregar fotos **de noche con luz artificial**?
7. ¿El umbral de 0,6 para `seguro` va a cambiar? El robot lo lee del modelo.

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
