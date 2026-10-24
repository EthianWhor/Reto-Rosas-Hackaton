# Inversión y retorno — borrador v2

> **v2 (2026-10-24):** la simulación midió la velocidad del robot (~0,09 m/s, 2 h por invernadero de 0,11 ha).
> Con eso el robot no se paga solo en una finca de 20 ha, y el negocio se presenta en **dos paquetes**
> (sección 6): formación en toda la finca y robot piloto.

> **Todas las cifras son supuestos explícitos para discutir.** Las marcadas con 📌 vienen de una fuente
> (ver [investigacion.md](investigacion.md)). Las marcadas con 🏠 las dio la finca. Las marcadas con ❓
> son supuestos nuestros que hay que validar con la finca (la lista de preguntas está en
> [README.md](README.md)). **Todavía no tenemos medidas del campo.** La regla del pitch: **mostrar los supuestos, no esconderlos.** Un jurado de
> empresa confía más en un número conservador explicado que en uno grande sin respaldo.
>
> **Cambios frente a la v0:** se plantea **un solo robot** para empezar y **un robot por campo** después;
> el robot recorre **línea por línea** y gira en las cabeceras; el campo tiene **iluminación LED blanca**;
> se asume que la energía no es un límite (cambio de batería o base de carga); las pantallas son
> **tablets comunes tipo turnero**, y el desarrollo del software deja de ser un costo de la finca y pasa a
> ser nuestro (se recupera con la suscripción).

## 1. Finca de referencia

| Variable | Valor | Origen |
|---|---|---|
| Área en rosa | 20 ha | ❓ tamaño de una finca mediana de la Sabana; pedir el dato real |
| Ingreso por hectárea | ~USD 214.000 / año | 📌 exportaciones 2025 (USD 2.397 M) ÷ 11.200 ha cultivadas (promedio de todas las flores) |
| Ingreso de la finca | ~USD 4,28 M / año | cálculo |
| Personas | ~270 (≈13,4 por ha) | 📌 150.000 empleos directos ÷ 11.200 ha |
| Operarios de cultivo | ~110 | ❓ ~40 % del personal |
| Costo mensual por operario | ~COP 2,8 M ≈ USD 700 | 📌 salario mínimo 2026 (COP 1.750.905) + auxilio de transporte (COP 249.095) + ~47 % de prestaciones y seguridad social ❓; TRM supuesta de COP 4.000 ❓ |
| Personas nuevas por año | ~70 | ❓ 30 % de rotación en cultivo (33) + temporales de San Valentín y Día de la Madre (~40) |

## 2. Capacidad de un robot

**Cómo recorre:** avanza por una línea de punta a punta sin girar dentro de ella, da la vuelta en la
cabecera (donde hay más espacio) y entra a la siguiente. Desde cada pasillo ve **las dos camas** que
tiene a los lados, así que basta con recorrer **un pasillo sí y otro no**.

| Variable | Valor | Origen |
|---|---|---|
| Cama + pasillo | 1,3 m | ❓ medir en el campo |
| Metros de pasillo por hectárea | ~7.700 m → **~3.900 m** recorriendo uno sí y otro no | cálculo |
| Velocidad promedio con fotos | 0,6 m/s (uso diario hasta 0,8 m/s) | 📌 velocidad; ❓ promedio con paradas |
| Ronda nocturna | 10 h | ❓ |
| Energía | No es un límite (batería intercambiable o base de carga) | supuesto del equipo |
| **Recorrido por noche** | **~21,6 km ≈ 5,5 ha** | cálculo |

- **Lo que importa es el área, no el largo de las líneas:** líneas más cortas significan más vueltas
  en las cabeceras, pero los metros totales por hectárea son los mismos. Fórmula para cuando tengamos
  el dato real: *metros por ronda ≈ área del campo ÷ (2 × ancho de cama + pasillo)*.
- **Fase 1, un robot para toda la finca (20 ha):** cada línea se revisa **cada ~4 noches**. Con la
  etapa de cada botón, RosaNet proyecta cuándo llega al punto 3, así que el reporte diario se arma con
  lo visto y lo pronosticado.
- **Fase 2, un robot por campo:** si cada campo mide hasta ~5 ha, se revisa **completo cada noche**.

### ⚠️ La velocidad efectiva decide el negocio, y ya está medida

**Medido en la simulación (2026-10-24, `robot/PLAN_robot_rosas_X2.md` 4.5):** el invernadero completo
(20 camas de 1 m × 30 m, 21 caminos de 0,8 m: ~36,8 m × 30 m ≈ **0,11 ha**, 6.031 rosas) toma **2 h**,
con una vuelta a la base por batería. Son 630 m de caminos en 120 min: **~0,09 m/s**. El robot se detiene
cada 1,25 m y toma 4 fotos; de los ~14 s de cada parada, caminar es solo ~4 s. **La mejora está en las fotos,
no en caminar:** fotografiar en movimiento (la cámara da 40 cuadros por segundo) o con menos posturas.

| Velocidad efectiva | Área por noche (10 h) | 20 ha con un robot | Payback del robot solo* | Payback de todo el sistema* |
|---|---|---|---|---|
| **~0,09 m/s (medido)** | **~0,55 ha** (≈5 invernaderos como el simulado) | cada ~36 noches | **no se paga: es un piloto** | formación sí (~3 meses); robot no |
| 0,3 m/s (paradas cada ~5 m) | ~2,7 ha | cada ~7 noches | ~6 años | ~2,4 años |
| 0,6 m/s (fotos en movimiento) | ~5,5 ha | cada ~4 noches | ~23 meses | **~14 meses** |

\* Las filas de 0,3 y 0,6 m/s son metas que hay que medir: suponen recorrer un pasillo sí y otro no
(cama + pasillo de 1,3 m ❓). Las palancas A (la parte del robot) y C solo aplican al área que el robot revisa con
frecuencia útil. Estimación gruesa para ordenar la conversación, no un cálculo fino.

**Qué decimos en el pitch:** "Medimos que hoy el robot va a 0,09 m/s porque se detiene a tomar fotos. Por eso
no prometemos que el robot se pague solo: entra como **piloto en un bloque** (~0,5 ha revisadas cada noche,
rosa por rosa) y escala cuando capture en movimiento. Lo que sí se paga desde ya es la formación."

## 3. Inversión inicial de la finca (CAPEX), fase 1: un robot

| Concepto | USD | Origen |
|---|---|---|
| AgiBot X2 Ultra | 43.000 | 📌 distribuidor (GlobalDroneHQ, oct. 2026); en Europa ~€50.000. Se cotiza por pedido |
| Paquete de navegación autónoma + base de carga automática + batería extra | 10.000 | ❓ AgiBot no publica precios; la navegación se compra aparte |
| Importación, envío, aranceles y seguro | 7.000 | ❓ ~15 % del robot |
| Sensores ambientales en el robot (temperatura, humedad, luz) | 500 | ❓ el X2 no los trae; se conectan a sus puertos USB y de 12 V |
| Iluminación LED blanca del campo piloto | 3.000 | ❓ depende del campo; puede que la finca ya tenga parte |
| 3 Meta Quest 3 + accesorios | 2.000 | 📌 USD 600 c/u (512 GB) |
| 4 tablets comunes con soporte de pared (turnero y sala de formación) | 1.600 | ❓ |
| Pantalla grande en la entrada + wifi en el invernadero | 3.000 | ❓ |
| **Total** | **≈70.000** | |

## 4. Costo anual de operación (OPEX)

| Concepto | USD / año |
|---|---|
| Mantenimiento y repuestos del robot (~10 %) | 4.300 |
| Técnico del robot (½ tiempo) | 7.800 |
| Suscripción Punto 3 (software, nube y actualizaciones del modelo) | 6.000 |
| Tiempo del experto para etiquetar y actualizar el contenido (~4 h/semana) | 2.000 |
| **Total** | **≈20.100** |

## 5. De dónde sale el retorno (3 palancas)

### A. Calidad del corte (la más grande)
Menos rosas cortadas en punto 2 (la falla más común según la finca) y menos rosas que se pasan en la
cama. Cada punto porcentual de ingreso que se recupera vale **~USD 43.000 al año** en esta finca.
- **Dato de la finca 🏠:** hoy aciertan el punto de corte en **~88 % de las flores**; **~12 % se cortan fuera de punto**. Es la línea base que queremos bajar.
- No todo error es una flor perdida: una rosa en punto 2 puede bajar de grado o irse a nacional. Supuesto ❓: cada error pierde ~1/3 del valor del tallo.
- Cuenta: *puntos de error que se bajan × 1/3 = % de ingreso recuperado.*
  - Conservador: 12 % → 10,5 % de error = **0,5 %** del ingreso.
  - Base: 12 % → 9 % = **1 %**.
  - Optimista: 12 % → 6 % = **2 %**.
- Referencia: GHT reporta que con herramientas de datos el descarte bajó del **8 % al 1 %** 📌 (caso promocional de Microsoft, no independiente).
- La finca hoy **no mide el campo con datos**: sus drones solo se usan para pruebas y no guardan nada. Se parte de cero.

### B. Inducción más corta y curva de aprendizaje
- **Dato de la finca 🏠:** la inducción dura **15 a 18 días**. La teoría ocupa **2 o 3 días**; el resto es práctica en el cultivo, que es donde está el tiempo y donde Punto 3 actúa (VR para practicar sin dañar rosas, juego para repetir hasta mecanizar).
- Costo de un día de inducción ≈ USD 20 ❓: el operario nuevo produce ~50 % (USD 13,5) y un experto lo acompaña ~25 % de su tiempo (USD 6,7), con USD 700/mes y 26 días hábiles.
- Además, después de la inducción el operario sigue por debajo de su meta de tallos por hora; la productividad crece con la experiencia 📌 (estudio en Falcon Farms y GR Chía).
  - Conservador: 3 días menos de inducción = **USD 60** por persona.
  - Base: 5 días menos (de ~16 a ~11) + 1 semana menos de curva al 50 % = **USD 180**.
  - Optimista: 8 días menos + 2 semanas menos de curva = **USD 320**.
- Con ~70 personas nuevas al año ❓.

### C. Orientación y asignación del personal
El conteo y la proyección de botones que hoy se hacen caminando y a ojo pasan al robot, y con la
pantalla turnero los cortadores llegan directo a los cuadrantes y las líneas con rosas listas.
- ~1 persona liberada del conteo (USD 8.400) + 3 % de eficiencia en las horas de corte (~60 cortadores → USD 15.100).
- No se cuenta (es potencial adicional): detección temprana de plagas y enfermedades, mejor pronóstico para ventas y logística, y datos para negociar con clientes.

## 6. Resultado en dos paquetes (propuesta v2, con la velocidad medida)

**Supuesto de reparto ❓:** la mitad de la palanca A (calidad del corte) viene de formar mejor a las personas
(app + VR, en toda la finca) y la otra mitad de orientarlas con el robot (solo donde el robot revisa).

### Paquete 1 · Formación en toda la finca (app RoseApp + VR)
| | Conservador | **Base** | Optimista |
|---|---|---|---|
| CAPEX: 3 Meta Quest + 4 tablets + pantalla y wifi | 6.600 | **6.600** | 6.600 |
| OPEX: suscripción + tiempo del experto | 8.000 | **8.000** | 8.000 |
| A (mitad de formación) | 10.700 | **21.400** | 42.800 |
| B. Inducción y curva | 4.200 | **12.600** | 22.400 |
| **Beneficio neto / año** | 6.900 | **26.000** | 57.200 |
| **Payback** | ~11 meses | **~3 meses** | ~1,5 meses |

### Paquete 2 · Robot piloto
- CAPEX ≈ **USD 63.400** (robot, navegación, importación, sensores y luz LED del bloque); OPEX ≈ **USD 12.100**
  (mantenimiento y técnico).
- **Con la velocidad medida** revisa ~0,55 ha cada noche, rosa por rosa: en 20 ha eso es ~3 % de la finca, así que
  **no se paga por sí solo**. Su valor en el piloto es otro: datos del campo que hoy no existen, miles de fotos
  para que RosaNet supere el 88 % del operario, y validar el robot real.
- **Si captura en movimiento a 0,6 m/s**, su parte (mitad de A + C ≈ USD 44.900 al año en el caso base) da un payback
  de ~23 meses, y el sistema completo (los dos paquetes, USD 70.000) se paga en **~14 meses**, como en la v1.

**Mensaje para la diapositiva:** *La formación se paga en ~3 meses en toda la finca. El robot entra como piloto
y el sistema completo se paga en ~14 meses cuando el robot fotografíe en movimiento (medido hoy: 0,09 m/s).*

## 6b. Resultado anterior (v1: todo junto, suponiendo 0,6 m/s)

| | Conservador | **Base** | Optimista |
|---|---|---|---|
| A. Calidad del corte | 21.400 | **42.800** | 85.600 |
| B. Inducción y curva de aprendizaje | 4.200 | **12.600** | 22.400 |
| C. Orientación y asignación | 10.000 | **23.500** | 40.000 |
| **Beneficio bruto / año** | 35.600 | **78.900** | 148.000 |
| − OPEX | 20.100 | **20.100** | 20.100 |
| **Beneficio neto / año** | 15.500 | **58.800** | 127.900 |
| **Payback de USD 70.000** | ~4,5 años | **~14 meses** | ~7 meses |

Esta tabla supone que el robot va a 0,6 m/s. **La simulación midió 0,09 m/s**, así que ya no se presenta así:
se reemplaza por la sección 6. Se deja para comparar.

## 7. Fase 2: un robot por campo

- Cada robot adicional cuesta **~USD 60.500** (robot, navegación, importación y sensores) y suma **~USD 5.000 al año** de mantenimiento.
- Las pantallas, las gafas, el software y el técnico ya están: no se pagan dos veces.
- Pasar de revisar cada línea cada ~4 noches a **cada noche** mejora sobre todo las palancas A y C. El número exacto sale del piloto: **la fase 2 solo se justifica cuando el piloto lo demuestre.**

## 8. Modelo de negocio (opciones)

1. **Venta + suscripción:** la finca compra el hardware (sección 3) y paga la suscripción anual de software y actualizaciones del modelo.
2. **Robot como servicio (RaaS):** cuota mensual por finca que incluye el robot, el mantenimiento, el software y las actualizaciones. Ejemplo ❓: USD 4.500/mes (USD 54.000/año) frente a USD 78.900 de beneficio base → la finca gana desde el primer mes y no invierte capital.
3. **Nuestro costo de desarrollo** (~USD 40.000 ❓ una sola vez, seis meses de trabajo) se recupera con las suscripciones de varias fincas, no con la primera.
4. **Canal GHT:** GHT presta servicios a más de 40 empresas del sector y centraliza datos con su suite Web Flowers y su BI "Verdad Única" 📌. Punto 3 puede entrar como **un módulo que alimenta ese BI**.
5. **Escalabilidad:** cada finca nueva solo cuesta el hardware y la adaptación por variedad (reetiquetar fotos de esa variedad). La app y la VR se reutilizan sin cambios.
