# Reto-Rosas-Hackaton

Sistema para apoyar el aprendizaje y la decisión del punto de corte de rosas de exportación
(reto "Corte de rosas", Sabana Hack). El contexto del reto, las decisiones y el análisis
están en [CONTEXTO.md](CONTEXTO.md).

Los operarios **no pueden usar celulares** en el cultivo, así que la solución se divide en tres áreas:

| Carpeta | Qué es | Para quién |
|---|---|---|
| [`metaquest/`](metaquest/) | Entrenamiento en realidad virtual para Meta Quest (WebXR, también se juega en el computador): reconocer el punto de corte, cortar, sellar y clasificar | Operarios nuevos |
| [`app-tablet/`](app-tablet/) | RoseApp: tablet a la entrada del invernadero con el informe del robot, el reparto del turno y un juego para mecanizar el proceso estándar (muy pronto / punto óptimo / muy tarde) y la sanación de la planta | Operarios y coordinación |
| [`robot/`](robot/) | AgiBot X2 Ultra (en simulación) que recorre el invernadero de noche por cuadrantes, detecta con la red neuronal (RosaNet) los botones listos y sube el reporte a la app | Coordinadores y operarios |

Cada carpeta tiene su propio README con el detalle. La base de datos que comparten la app y el robot
está en [`supabase/`](supabase/), la investigación del corte y la sanación en [`contenido/`](contenido/),
y el pitch, la inversión y la investigación del sector en [`pitch/`](pitch/).
