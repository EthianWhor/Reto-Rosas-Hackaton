# Demo del robot y números para el pitch

Guion para mostrar el robot en la presentación (unos 5–6 minutos) y los números medidos, con sus límites.
**Ojo:** el guion del pitch le da 3,5 minutos a toda la demo, incluidos el juego y la VR. Versión corta:
1 minuto de la parte 1 (o la ronda de respaldo), la parte 2 completa y una sola rosa en la parte 3.
Todo se corre desde `robot/`, con el entorno de la raíz activado: `..\.venv\Scripts\activate`.
El detalle de cada número está en [PLAN_robot_rosas_X2.md](PLAN_robot_rosas_X2.md).

---

## 1. Antes de la presentación (una vez)

1. **Clave de Supabase:** ya viene en `robot/.env` (está en git; el repo es privado). Probar que llega: `python -m reporte.envio --una-vez --config config/demo.yaml`. En la tablet, en "Informe
   del robot", abajo ya no debe decir que es un reporte de ejemplo.
2. **Revisar el modelo y la cámara:** `python main.py --revisar` (sin caminar) y
   `python modo_foto.py ../app-tablet/assets/rosas/2_optimo/finca_yolo_26_1.jpg` (debe salir "Óptimo").
3. **Webcam:** conectada y probada con `python modo_foto.py --webcam` (ESPACIO analiza, Q sale).
4. **Dejar lista una ronda de respaldo** por si algo falla en vivo:
   `python main.py --config config/demo.yaml --camino 1` y guardar la carpeta de `datos/rondas/`.
5. Tener la **tablet** abierta en la app, con un usuario experto (para revisar las dudosas). En la base de
   prueba todos son aprendices: entrar como Coordinadora y, en "Usuarios", tocar "Promover a experto" en
   alguien (por ejemplo, Luis). La Coordinadora también ve las dudosas.

## 2. Guion

### Parte 1: el robot hace la ronda (2 min)

```bash
python main.py --config config/demo.yaml --ventana
```

Qué decir mientras camina:
- "Es un AgiBot X2 Ultra en simulación. Sale de la base de noche y recorre el invernadero camino por camino, en
  serpiente: nunca gira dentro del camino, que mide 80 cm."
- "Cada 1,25 m se detiene y toma 4 fotos: izquierda y derecha, a media altura y hacia arriba. Así ve rosas
  de 1 a 2 m."
- "Las rosas de la simulación son fotos reales de la finca. El detector y RosaNet del equipo deciden de verdad;
  no hay trampa."
- "Cuando encuentra una rosa óptima, apunta la cabeza y la ilumina: esa es la acción física. Lo hace en los
  cuadrantes que se cosechan primero; señalarlas todas no cabría en una noche."
- En el camino 1 hay una caja: "Frena, espera, y cuando la quitan sigue." En el camino 2 hay un balde: "Espera
  30 s, como sigue ahí abandona el camino y lo anota en el reporte."
- Al final: "Volvió a la base, encontró WiFi y subió el reporte a la app."

### Parte 2: el reporte en la tablet (1 min)

- Abrir "Informe del robot": los cuadrantes ordenados por prioridad ("¿a dónde voy hoy?").
- Abrir una rosa dudosa con el usuario experto: se ve **la foto real que tomó el robot**, el experto la clasifica
  y esa etiqueta queda para reentrenar a RosaNet.

### Parte 3: el jurado pone a prueba el robot (2–3 min)

```bash
python modo_foto.py --webcam --auto --enviar --config config/demo.yaml
```

- "Traigan una rosa o una foto." Ponerla dentro del cuadro guía. **Con `--auto` no hay que tocar nada:** cuando
  reconoce la misma rosa dos lecturas seguidas (~2 s), la analiza y la manda sola a la app. No la vuelve a mandar
  hasta que se saque la rosa del cuadro, y una mano que la tape un momento no cuenta. Arriba de la imagen dice qué
  está haciendo ("esperando una rosa", "reconociendo…", "enviada a la app"). ESPACIO sigue funcionando para
  mandarla a mano. Sin `--auto`, solo con ESPACIO.
- Muestra la rosa con su estado y confianza, y en la consola **los consejos de la finca** (qué mirar).
- Si la confianza es baja, dice "dudosa" y no adivina: "Prefiere decir que no sabe a mandar a cortar en punto 2."
- El resultado llega a la tablet como un cuadrante `INV1-DEMO`, con la foto si fue dudosa.

> Ojo: el envío deja ese mini reporte como el último en la app. Al terminar, volver a subir la ronda de la
> parte 1 si se quiere mostrar de nuevo.

### Si algo falla en vivo

- Sin internet: el reporte queda en `datos/salida/` y se sube después con `python -m reporte.envio --una-vez --config config/demo.yaml`.
- Sin webcam: `python modo_foto.py foto.jpg --enviar --config config/demo.yaml` con una foto del celular.
- La ventana de MuJoCo va lenta: correr sin `--ventana` y mostrar las fotos de `datos/rondas/<id>/fotos/`.

## 3. Números para el pitch (simulación, 2026-10-24)

| Qué | Número | De dónde |
|---|---|---|
| Rosas que ve el robot en el invernadero completo (20 camas de 30 m, 6.031 rosas) | **95 %** | plan 4.5 |
| Rosas contadas dos veces | **0 %** | plan 4.5 |
| Error de ubicación (altura / metro en la cama) | **0,5 cm / 0,9 cm** | plan 4.5 |
| Duración de la ronda completa, sin señalar | **2 h** (1 vuelta a la base por batería) | plan 4.5 |
| Duración señalando las óptimas de los 10 primeros cuadrantes (en uso) | **2 h 18 min** (1 vuelta, 211 rosas) | plan 4.5 |
| Duración si señalara todas las óptimas | 4 h 46 min (~5,3 s por rosa, 2 vueltas) | plan 4.5 |
| Con fotos reales y el modelo del equipo: rosas encontradas | **71–73 %** | plan 7.13 |
| Con fotos reales: clase correcta | **74–80 %** | plan 7.13 |
| Inmaduras mandadas a "cortar hoy" (el error más caro) | **0** | plan 7.13 |
| Pasadas mandadas a "cortar hoy" (con el tamaño de la cabeza como segunda opinión) | **0–3** (antes 6–7) | plan 2.6 |
| Óptimas reales que reconoce | **51–59 %** | plan 7.13 |
| Obstáculos: espera, sigue si lo quitan, abandona el camino si no | 30 s de espera | plan 5.2 |
| Analizar mientras camina | ronda 16 % más corta | plan 8 |
| Batería | vuelve a la base al 25 % y sigue donde quedó | plan 15 |

Línea base de la finca: los operarios aciertan ~88 % del punto de corte (CONTEXTO.md 2.0.4). El robot no
reemplaza ese ojo: **cuenta y prioriza el campo** para que los operarios vayan primero a donde hay que cortar.

## 4. Límites (decirlos antes de que pregunten)

- **Todo es simulación.** El robot real no se probó. Del SDK del X2 Ultra salen riesgos concretos (plan 14.1):
  la cámara es de 1280 × 720 (en la simulación la cobertura baja de 90 % a 68 %), en el modelo original la
  cabeza no se inclina, cabeza y caminar van en modos distintos, y no trae foco en la cabeza.
- **La noche es simulada.** No hay fotos reales de noche con la luz del robot; el modelo se midió oscureciendo
  fotos de día.
- **Pasadas:** la finca dio 2 fotos y el modelo a veces las llama óptimas. El robot usa el tamaño de la cabeza
  como segunda opinión (una pasada es más grande) y las manda a revisión: en la simulación bajan de 6–7 a 0–3 por
  ronda. Los umbrales de tamaño se eligieron en la simulación; falta calibrarlos con rosas reales.
- **No señala todas las óptimas:** señalarlas todas no cabe en una noche, así que señala solo en los 10 primeros
  cuadrantes del reporte anterior (los que se cosechan primero). La primera noche, sin reporte, señala en todos.
- **Las rosas de la simulación son las mismas fotos con las que se entrenó el modelo**: los números con carteles
  son optimistas.
- **"Lista mañana"** se estima la primera noche; los umbrales no están calibrados con un experto.

## 5. Preguntas probables del jurado

- **¿Por qué un robot y no una cámara fija?** Las rosas están a 1–2 m en pasillos de 80 cm a lo largo de
  cientos de metros: una cámara fija no ve el campo. El robot recorre todo cada noche, ubica cada rosa (cama,
  metro, altura), la señala, y la finca ve por primera vez el estado de todo el campo por cuadrante.
- **¿Qué pasa si se equivoca?** Si duda, no adivina: la rosa va a "dudosa", un experto la revisa en la tablet
  con la foto, y esa etiqueta sirve para reentrenar el modelo.
- **¿Qué falta para el robot real?** Probar `cuerpo/real_backend.py` con el robot (tópicos del SDK ya
  identificados), medir la cámara, fotos reales de noche y decidir la luz.
