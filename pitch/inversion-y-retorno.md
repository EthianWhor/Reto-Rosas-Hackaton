# Inversión y retorno — borrador v1

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

### ⚠️ La velocidad efectiva es la variable que decide el negocio

La simulación del equipo (rama `A`, `robot/PLAN_robot_rosas_X2.md`) recorre un invernadero de
20 camas de 30 m (caminos de 0,8 m) **parando cada 1,25 m** para girar la cabeza y fotografiar:
tarda ~95–130 min en ~630 m de caminos, es decir **~0,1 m/s en promedio**. Las cuentas de arriba
suponen **0,6 m/s**, fotografiando sin parar (la cámara estéreo da 40 cuadros por segundo con 156° de
campo de visión).

| Velocidad efectiva | Recorrido por noche (10 h) | Área por noche | 20 ha con un robot | Payback base* |
|---|---|---|---|---|
| ~0,1 m/s (simulación actual, con paradas) | ~3,6 km | ~0,7 ha (todos los caminos, cama + camino de 1,8 m) | cada línea cada ~30 noches | **no se paga en un plazo razonable** |
| 0,3 m/s (paradas cada ~5 m) | ~10,8 km | ~2,7 ha | cada ~7 noches | ~2,4 años |
| **0,6 m/s (fotos en movimiento)** | **~21,6 km** | **~5,5 ha** | **cada ~4 noches** | **~14 meses** |

\* Las palancas A y C solo aplican al área que el robot alcanza a revisar con frecuencia útil
(cada ≤ 4 noches); la B (formación) no depende del robot. Estimación gruesa para ordenar la
conversación, no un cálculo fino.

**Qué hacer:** (1) probar en la simulación la captura en movimiento, sin paradas, y medir cuántas
rosas se pierden; (2) mientras tanto, en el pitch presentar la fase 1 como **un robot en un campo
piloto**, que sí se recorre completo cada noche, y el número de la finca completa como meta
condicionada a esa prueba.

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

## 6. Resultado (fase 1: un robot)

| | Conservador | **Base** | Optimista |
|---|---|---|---|
| A. Calidad del corte | 21.400 | **42.800** | 85.600 |
| B. Inducción y curva de aprendizaje | 4.200 | **12.600** | 22.400 |
| C. Orientación y asignación | 10.000 | **23.500** | 40.000 |
| **Beneficio bruto / año** | 35.600 | **78.900** | 148.000 |
| − OPEX | 20.100 | **20.100** | 20.100 |
| **Beneficio neto / año** | 15.500 | **58.800** | 127.900 |
| **Payback de USD 70.000** | ~4,5 años | **~14 meses** | ~7 meses |

**Mensaje para la diapositiva (3 números):** *Un robot · Inversión ≈ USD 70 mil · Se paga en ~14 meses*,
y se dice en voz alta: **"hoy 12 de cada 100 rosas se cortan fuera de punto; si bajamos a 9, el robot
se paga en poco más de un año"**.

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
