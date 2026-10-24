# Meta Quest — entrenamiento en realidad virtual

Escuela de corte para operarios nuevos (rosa Freedom). El operario recorre en VR los senderos de 80 cm
entre camas de rosas con su carrito y, por cada rosa:

1. **Elige y corta:** solo la rosa en punto 3, sobre la 2.ª o 3.ª hoja de cinco foliolos, hacia el lado
   contrario al corte anterior y dentro del rango de tallo de la empresa (50 a 100 cm).
2. **Sella** el corte con sellante azul.
3. **Clasifica** en el carrito: cosecha (en punto y bien cortada) o desecho.

Cada acierto suma puntos y cada error resta, con un consejo del proceso correcto. Hay tutorial en VR y
en pantalla. Las categorías son las mismas de la app y de RosaNet: muy pronto (cerrada), punto óptimo
(punto 3) y muy tarde (muy abierta).

## Cómo abrirla

Es una sola página web, [`index.html`](index.html), hecha con **A-Frame 1.7 (WebXR)**: las rosas y las
camas se dibujan en 3D con código, sin modelos externos.

- **Meta Quest 3:** abrir la página en el navegador del visor (tiene que estar publicada con `https`, por
  ejemplo en GitHub Pages; por eso está `.nojekyll`) y tocar "Entrar en VR".
- **Computador:** abrir `index.html` en el navegador y jugar en pantalla (WASD o flechas para caminar,
  clic para cortar y sellar, B / Y para clasificar).

## Pendiente
- Confirmar con la finca el sellante, la hoja de corte y la regla de alternar el lado
  (preguntas en [`contenido/corte-y-sanacion.md`](../contenido/corte-y-sanacion.md)).
- Desinfección de la tijera, tocón e hidratación a tiempo (están en la app, todavía no en la VR).
