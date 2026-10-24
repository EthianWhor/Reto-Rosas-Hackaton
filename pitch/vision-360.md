# Visión 360 — borrador v0

## 1. Las personas primero

| Persona | Hoy | Con Punto 3 |
|---|---|---|
| **Operario nuevo** ("Marta, 3 semanas") | Aprende al lado de alguien, con miedo de equivocarse y sin saber si va bien | Practica en VR sin dañar rosas, juega en la tablet, ve su avance y sabe en qué se confunde |
| **Cortador experto** ("Don Luis, 15 años") | Enseña lo mismo una y otra vez y pierde productividad | Su criterio queda en el sistema (él etiqueta los casos difíciles). Enseña lo que solo él sabe enseñar. Se reconoce como **maestro** |
| **Instructor** | Evalúa a ojo, sin registro | Evalúa en VR con escenarios repetibles y ve el progreso de cada persona |
| **Coordinador de cultivo** | Decide a dónde mandar gente según recorridos y experiencia | Ve en la mañana el mapa de cuadrantes con rosas listas y el pronóstico; la pantalla turnero de la entrada orienta a cada trabajador |
| **Gerencia** | Se entera de la calidad del corte cuando llega el reclamo | Tiene indicadores diarios y datos para vender y planear |

**Principios:**
- **No reemplaza:** el robot no corta rosas. Quita la adivinanza y acelera el aprendizaje.
- **Retroalimentación, no vigilancia:** los datos de cada persona son para que mejore, no para sancionarla. Se dice en el pitch y se diseña así (el operario ve su progreso; los reportes a la gerencia son por equipo o por cuadrante).
- **Diseño para todos:** ~60 % de las personas del sector son mujeres y muchas son cabeza de hogar; hay diferentes niveles de lectura. Por eso: botones grandes, fotos, voz, cero texto largo y sin login complicado.
- **Sin celulares en el cultivo:** la app vive en pantallas comunes tipo turnero (a la entrada del invernadero y en la sala de formación). Nadie tiene que usar su teléfono personal para trabajar.
- **Orgullo y carrera:** el operario que domina el punto 3 puede subir de nivel (insignias en la tablet, certificación interna) y llegar a ser instructor.

## 2. Ética y datos

- Las fotos son de rosas, no de personas. Si una cámara capta a alguien, se descarta o se difumina.
- Los datos de desempeño se tratan según la Ley 1581 de 2012 (habeas data): autorización, finalidad clara y acceso del trabajador a sus propios datos.
- El modelo dice **"no estoy seguro"** cuando su confianza es baja, en lugar de inventar una respuesta.
- La decisión final la toma la persona. El sistema recomienda y explica.
- Seguridad física: el robot trabaja **de noche, cuando no hay operarios**; si detecta a alguien, se detiene (evasión de obstáculos dinámicos del SDK).

## 3. Mantenimiento y operación

| Qué | Cada cuánto | Quién |
|---|---|---|
| Carga o cambio de batería | Cada ronda (~2 h) | Automático con base de carga o vigilante nocturno |
| Limpieza de lentes y LiDAR (polvo, humedad) | Diario | Técnico del robot |
| Revisión de articulaciones, pies y carcasa | Mensual | Técnico + soporte del distribuidor |
| Actualizaciones del sistema (OTA) | Según AgiBot | Técnico |
| Reentrenamiento de RosaNet con fotos nuevas | Mensual o por temporada | Equipo de datos + experto que valida etiquetas |
| Actualización del contenido de la tablet y la VR | Por temporada o variedad nueva | Instructor |
| Desinfección de las gafas VR | Cada uso | Instructor |

- **Riesgos:** humedad y vapor del invernadero, caídas del robot por el terreno, dependencia de un solo proveedor (AgiBot) y repuestos importados.
- **Mitigación:** piloto en un bloque, garantía de 1,5 años, contrato de soporte local y la posibilidad de cambiar el robot por otra plataforma, porque el software (RosaNet, tablet, VR y dashboard) es independiente del hardware.

## 4. Escalabilidad

1. **Piloto (8 semanas):** 1 campo con iluminación LED, 1 robot, 1 variedad (Freedom). Medir: exactitud del conteo frente al conteo manual, tiempo de inducción y porcentaje de rosas en punto 2.
2. **Finca completa con un robot:** el robot rota por los campos; cada línea se revisa cada pocas noches y RosaNet proyecta el resto.
3. **Un robot por campo:** cada campo se revisa completo cada noche. Se da este paso solo si el piloto demuestra la mejora.
4. **Más variedades:** reetiquetar fotos por variedad; el criterio por variedad se configura sin rehacer la app.
5. **Red de fincas (canal GHT):** el modelo aprende de todas y el dashboard alimenta su BI.
6. **Más allá de la rosa:** el mismo esquema (aprender, practicar, decidir) sirve para clavel, crisantemo, hortensia u otros cultivos de corte.

## 5. Límites que decimos nosotros antes que el jurado

- Solo hay **2 fotos de "pasado"** y el dataset es de **día**; el robot verá **de noche** con la luz LED blanca del campo. Hay que tomar fotos de prueba con esa luz.
- Una sola variedad (Freedom).
- RosaNet con forma y color acierta el 77 % en rosas de la finca, de día y de noche; marca como óptimas ~7 de 45 inmaduras (la falla más costosa). Por eso existe la categoría "incierta" y la revisión del experto.
- El detector encuentra ~78 % de las rosas del invernadero y tiene falsos positivos (postes, hojas).
- En la simulación, la ronda con paradas cada 1,25 m avanza ~0,1 m/s; hay que llevarla a fotos en movimiento para cubrir la finca (ver inversion-y-retorno.md).
- Asumimos que el robot cabe por las líneas y gira en las cabeceras, y que la energía alcanza para la ronda; falta medirlo en el campo.
- Con un solo robot, cada línea se revisa cada pocas noches, no todas las noches.
- No tenemos el proceso de **sanación**; esa parte del juego está pendiente.
- Las cifras de retorno son supuestos hasta que la finca nos dé sus datos.
- Los drones de la finca quedan fuera del prototipo.
