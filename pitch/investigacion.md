# Investigación — robot, sector y proceso (2026-10-23)

## 1. AgiBot X2 Ultra: lo que dicen sus documentos

Fuentes: manual AimDK_X2 (`X2AIMDK_X2.docx`), "X2 Datasheet", "LINGXI X2 Exhibition Hall Guide …
Boundary Specifications", fichas técnicas en español e inglés y los ejemplos de código en C++ y Python
(todos entregados por el equipo).

### Lo que juega a favor
| | |
|---|---|
| Tamaño | 1,31 m × 46 cm × 21 cm; ~39 kg. La cámara queda **por debajo de las rosas y mira hacia arriba**, igual que en las fotos de la finca |
| Visión | RGB-D Orbbec Gemini335 (1920×1080 color + profundidad), estéreo frontal 2064×1552 a 40 fps, cámara de interacción 2608×1960, cámara trasera, LiDAR RoboSense E1R (120° × 90°, ~30 m) |
| Cómputo | **Jetson Orin NX 16 GB, 157 TOPS**, 512 GB, en una unidad de desarrollo aparte (PC2). RosaNet corre a bordo |
| Software | AimDK_X2 sobre **ROS 2 Humble**, C++ y Python, desarrollo en contenedor Docker. Hay ejemplos para: leer cámaras y LiDAR, caminar por velocidad, **navegación a un punto del mapa con evasión de obstáculos** (SLAM, opcional), voz, **pantalla**, **tira LED**, gestos preprogramados y agentes de voz en la nube (LinkSoul, con soporte MCP) |
| Interacción | Micrófonos, parlantes, pantalla, luces, sensor táctil en la cabeza. Puede **hablar con los operarios y responder preguntas** |
| Brazos | 7 grados de libertad por brazo: puede **señalar** una rosa o un cuadrante (acción física para el reto) |
| Energía | ~421 Wh (500 Wh en algunas fichas), ~2 h caminando a 0,5 m/s, carga en 1,5 h, batería intercambiable y base de carga automática opcional |
| Simulación | MuJoCo con el control de movimiento oficial: se puede probar la lógica sin el robot físico |
| Garantía | 1,5 años (Ultra) |

### Lo que juega en contra y cómo lo resolvemos
| Límite | Dato | Qué proponemos |
|---|---|---|
| **Pasillos** | Ancho mínimo para girar: **0,9 m**. Navegación autónoma: corredor mínimo de **1,5 m** | **Decisión del equipo:** el robot no gira dentro de la línea. La recorre de punta a punta y da la vuelta en la cabecera, donde hay más espacio. Medir el ancho real de pasillos y cabeceras |
| **Piso** | Rampas de más de 3° no soportadas para navegar (10° para caminar), escalón máximo de 5 cm, pisos con cambios bruscos de color se confunden con desniveles | Mapear el campo piloto; evitar zonas con mangueras o canales |
| **Luz y ambiente** | La navegación es inestable con contraluz, poca luz, polvo, humo o **vapor de agua**; los espacios semiexteriores son inestables | **Decisión del equipo:** el campo tendrá **iluminación LED blanca** para la ronda nocturna. Falta validar con la humedad alta del invernadero |
| Energía | ~2 h por batería a 0,5 m/s | **Supuesto del equipo:** no es un límite (cambio de batería o base de carga) |
| Temperatura | −10 °C a 40 °C | La Sabana está dentro del rango; ojo con el calor del mediodía bajo plástico (por eso de noche) |
| Navegación | La navegación autónoma es **beta** y requiere comprar un paquete aparte | Incluido en el CAPEX; para el demo, control remoto o recorrido guiado |
| Sensores ambientales | No trae sensor de humedad ni de temperatura ambiente | Módulo externo por USB / 12 V |
| GNSS | No sirve bajo plástico | Ubicación por mapa SLAM + marcadores QR/ArUco por cuadrante |
| Carga útil | ≤1 kg con el brazo en cualquier posición | Solo lleva la lámpara y los sensores, no flores |
| Desarrollo | Prohibido programar en la unidad de control de movimiento; no lanzar muchos nodos ROS seguidos (riesgo de caída) | Todo en el contenedor del Orin NX |

### Teleoperación con VR (dato interesante)
AgiBot tiene un kit de teleoperación de cuerpo completo con gafas PICO 4 Ultra y rastreadores. **No
es Meta Quest** y se compra aparte, pero abre una idea para el futuro: que el instructor vea por los
ojos del robot o lo guíe en VR.

## 2. El sector en cifras

| Dato | Valor | Fuente |
|---|---|---|
| Exportaciones de flores 2025 | USD 2.397 M (+2,1 %); ~USD 2.376 M y >338.000 t según otro reporte | Portafolio, Agronegocios |
| Hectáreas | ~11.200 ha; Cundinamarca 70 %, Antioquia 28 % | Contexto Ganadero |
| Empleo | ~240.000 formales, 150.000 directos, ~60 % mujeres; +20.000 temporales en San Valentín | Asocolflores vía Portafolio |
| Mercado | EE. UU. recibe ~80 % | Portafolio |
| Rosas | Colombia es el 2.º exportador de rosas del mundo; ~700 millones de rosas para San Valentín | Gestión, EFE |
| Presiones | Alza del salario mínimo (+23 % en 2026), peso revaluado y aranceles | Portafolio |
| Productividad | Más baja que Chile, México y la OCDE; se atribuye a baja innovación y gestión de calidad | Uniagraria |
| Personas | Alta rotación usada como estrategia de contratación; difícil conseguir personal en temporada alta; relevo generacional | Uniminuto, U. Santo Tomás |

**Argumento para el pitch:** el costo laboral subió 23 % en un año y la finca necesita más rosas
buenas por persona. Formar más rápido y cortar mejor es la forma de crecer sin reemplazar personas.

## 3. GHT

- Empresa colombiana **nativa digital** que presta servicios a **más de 40 empresas** del sector,
  con fincas en Colombia y Ecuador y capacidad de exportar hasta mil millones de flores al año.
- Suite propia **Web Flowers** y un BI llamado **"Verdad Única"** que centraliza los datos de todas las fincas (Microsoft Power BI, Power Apps, RPA).
- Ya usa **machine learning sobre imágenes de dron para predecir la cosecha de rosa (85 % de exactitud)** y RFID en estibas para trazabilidad.
- Reporta que el **descarte de flor bajó del 8 % al 1 %**.
- Fuente: caso de cliente de Microsoft (promocional, no independiente).

### Lo que nos dijo la finca (2026-10-23)
- La finca **sí tiene drones**, pero **no los usa para muestreo ni para revisar el cultivo**: solo hace pruebas (no se especificó cuáles).
- Los drones **no tienen base de datos ni guardan ningún dato**, así que hoy no le sirven para decidir.
- No vamos a integrar drones en el hackatón (no hay tiempo en las ~10 horas que quedan). Queda como idea a futuro: sumarlos a la misma base de datos.

**Qué significa para nosotros:** el caso de GHT muestra que los datos y la IA funcionan en el sector,
pero **la finca del reto hoy no tiene datos del campo**. Punto 3 llena ese vacío:
1. **Datos desde el primer día:** cada ronda queda guardada, con fotos como evidencia.
2. **La vista desde abajo y de lado** (sépalos, copa, caracol), que un dron no ve desde arriba.
3. **Las personas:** no solo se predice, también se orienta y se forma al operario. Punto 3 cierra el ciclo dato → formación.
4. **Integración:** si la finca trabaja con GHT, el reporte puede alimentar a "Verdad Única" en lugar de competir con él.

> Ojo: en CONTEXTO.md el video de capacitación aparece como material de "CHT". Confirmar si es GHT.

## 4. Proceso completo de la rosa (para la VR, la tablet y la base de conocimiento)

1. **Cultivo:** invernadero de plástico, camas en suelo o hidroponía. Desde el pinche (poda que inicia el tallo) hasta la cosecha.
2. **Lectura del punto de corte (variedad Freedom):** punto 3 = caracol definido mostrando el centro, rojo vivo e intenso, patrón de copa. Falla común: punto 2 (cabeza más pequeña, rojo más oscuro, sépalos pegados).
3. **Corte:** a mano con tijera o cuchillo afilado. La flor **nunca se pone en el suelo**.
4. **Sanación de la planta después del corte:** ❓ la finca no envió material. Hay una versión de trabajo sacada de manuales (sellar el corte, quitar residuos y tallos débiles, desinfectar la tijera) en [`contenido/corte-y-sanacion.md`](../contenido/corte-y-sanacion.md), ya en la app y en la VR. Es justo donde más se equivocan los operarios: hay que confirmarla con la finca.
5. **Transporte a poscosecha:** con carro o caja de corte por los pasillos.
6. **Hidratación:** baldes limpios con agua y biocida; si el agua es dura, ácido cítrico para bajar el pH por debajo de 5.
7. **Recepción en cuarto frío** (~3 °C), en agua.
8. **Clasificación, despetale, desespine y deshoje, y boncheo** (armado de ramos; ~300 tallos por hora por persona en una finca de la Sabana).
9. **Tratamiento químico** (~2 h) en otro cuarto frío.
10. **Empaque** a 2–4 °C, en cajas según el pedido del cliente, y despacho (a Miami en avión).

La flor tarda unos días entre el corte y el cliente. Por eso se corta antes de abrir del todo.

## 5. Referentes de robots de monitoreo
- **Plantalyzer** (Wageningen University & Research, Países Bajos): robot autónomo que **cuenta y clasifica la madurez del tomate en la planta** y alimenta un software de pronóstico. Es el referente más parecido a nuestro robot y demuestra que el modelo "robot que cuenta y pronostica" ya existe en horticultura de invernadero.
- Conteo de flores con IA en frutales: ~90 % de precisión; el error de pronóstico baja a ~5 % cerca de la cosecha si se calibra con conteos de campo.

## Fuentes
- Portafolio: [Floricultura pide oxígeno al Gobierno](https://www.portafolio.co/economia/agro/floricultura-pide-oxigeno-al-gobierno-ante-alza-de-costos-peso-fuerte-y-presion-sobre-sus-exportaciones-502808), [San Valentín y presiones](https://www.portafolio.co/negocios/empresas/san-valentin-entre-el-auge-exportador-y-las-presiones-que-golpean-a-la-floricultura-colombiana-488219)
- [Forbes Colombia: exportaciones 2025](https://forbes.co/economia-y-finanzas/colombia-exporto-mas-de-300-000-toneladas-en-2025)
- [Contexto Ganadero: 61 mil toneladas](https://www.contextoganadero.com/agricultura/flores-colombianas-se-imponen-en-el-mundo-61-mil-toneladas-de-tallos-saldran-en-el-mes-de-las-madres)
- [Agronegocios: proceso en finca de la Sabana](https://www.agronegocios.co/agricultura/en-san-valentin-la-mitad-de-las-flores-que-llegan-a-ee-uu-son-colombianas-2620258)
- [Microsoft: caso GHT](https://news.microsoft.com/es-xl/features/eficiencia-transparencia-e-incremento-en-las-ventas-como-una-empresa-nativa-digital-impulsa-la-floricultura-basada-en-datos-en-colombia/)
- [GlobalDroneHQ: precio X2 Ultra](https://globaldronehq.com/blogs/guides/agibot-x2-vs-x2-ultra), [OpenELAB (EUR)](https://openelab.io/it/collections/agibot-x2-humanoids)
- [Consultorsalud: salario mínimo 2026](https://consultorsalud.com/aumento-del-salario-minimo-en-colombia-2026/)
- [Notebookcheck: precios Meta Quest](https://www.notebookcheck.org/Los-precios-de-Meta-Quest-3-y-Meta-Quest-3s-aumentaran-en-los-proximos-dias.1276180.0.html)
- [Uniagraria: productividad floricultura](https://uniagraria.edu.co/wp-content/uploads/2024/12/ElDesafioDeLaProductividadEnLaFloriculturaColombiana.pdf), [Uniminuto: rotación](https://repository.uniminuto.edu/handle/10656/17520), [U. EAN: experiencia y productividad](https://repository.universidadean.edu.co/bitstreams/23c6443f-297d-4ee5-a84f-f47827bfce79/download)
- [U. Católica de Oriente: cosecha y poscosecha](https://repositorio.uco.edu.co:443/bitstream/20.500.13064/1446/5/Trabajo%20de%20grado.pdf), [U. Nacional: pérdidas poscosecha en rosa](https://revistas.unal.edu.co/index.php/agrocol/article/view/21718)
- [WUR: Plantalyzer](https://wur.nl/en/project/Plantalyzer-tomato-monitoring-robot-for-harvesting-forecast.htm), [Portal Frutícola: IA y pronóstico](https://www.portalfruticola.com/?p=623292)
