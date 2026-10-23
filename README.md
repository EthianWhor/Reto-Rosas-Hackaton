# Reto-Rosas-Hackaton

Sistema para apoyar el aprendizaje y la decisión del punto de corte de rosas de exportación
(reto "Corte de rosas", Sabana Hack). El contexto del reto, las decisiones y el análisis
están en [CONTEXTO.md](CONTEXTO.md).

Los operarios **no pueden usar celulares** en el cultivo, así que la solución se divide en tres áreas:

| Carpeta | Qué es | Para quién |
|---|---|---|
| [`metaquest/`](metaquest/) | App de entrenamiento con realidad aumentada en Meta Quest (modelos 2D): cómo reconocer el punto de corte y cómo cortar | Operarios nuevos |
| [`app-tablet/`](app-tablet/) | App tipo juego en tablet para mecanizar el proceso estándar (muy pronto / punto óptimo / muy tarde) y la sanación de la planta después del corte | Operarios |
| [`robot/`](robot/) | Robot que recorre el campo por sectores, detecta con la red neuronal (RosaNet) los botones listos y reporta a un dashboard (coordinadores y pantalla a la entrada del campo) | Coordinadores y operarios |

Cada carpeta tiene su propio README con el detalle.
