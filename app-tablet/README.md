# App tablet — juego para mecanizar el proceso

App tipo juego en tablet que ayuda a los operarios a interiorizar el proceso estándar de la finca
hasta hacerlo de forma mecánica. Hecha con **Expo (SDK 58) + Expo Router + TypeScript**.

## Qué hay (base)

| Pantalla | Archivo | Estado |
|---|---|---|
| Inicio: nombre del operario (sin login) y menú | `src/app/index.tsx` | Listo |
| Aprender las 3 categorías: fotos reales de la finca + qué mirar | `src/app/aprender.tsx` | Listo |
| Juego: clasifica el botón (muy pronto / punto óptimo / muy tarde) con explicación inmediata | `src/app/clasificar.tsx` | Listo (básico) |
| Mi progreso: aciertos por categoría y con qué la confunde | `src/app/progreso.tsx` | Listo (básico, solo en la tablet) |
| Sanación después del corte | `src/app/sanacion.tsx` | **Pendiente: falta el proceso de la finca** |

- Las categorías y los tips (`src/data/categorias.ts`) usan las mismas claves que RosaNet
  (`robot/ml/stages.py`). Si cambian allá, cambiarlas aquí.
- Las rondas reparten las fotos por categoría (hay 47 inmaduras, 20 óptimas y solo 2 pasadas), así
  que las de "muy tarde" se repiten.
- El progreso se guarda en la tablet con AsyncStorage.

## Correr en desarrollo

Requiere **Node 22.13 o superior** (Expo SDK 58 avisa que Node 20 ya no está soportado).

```bash
npm install
npm start          # escanear el QR con Expo Go en la tablet
npm run web        # o verla en el navegador
```

Todas las librerías actuales vienen incluidas en **Expo Go**, así que no hace falta compilar para
desarrollar. Solo hará falta un build propio (development build) si se agrega una librería nativa
que Expo Go no trae, por ejemplo correr RosaNet en la tablet (TFLite/ONNX) o el modo kiosco.

## Fotos de las rosas

Las fotos son los recortes de la finca que genera `robot/ml/prepare_data`. Para actualizarlas:

```bash
npm run fotos      # copia ../robot/data/finca_stages a assets/rosas y regenera src/data/rosas.ts
```

## Generar el APK (EAS)

```bash
npx eas-cli@latest login
npx eas-cli@latest init        # solo la primera vez: crea el proyecto en la cuenta de Expo
npm run build:apk              # perfil "preview" de eas.json → APK para instalar en la tablet
```

EAS no sube lo que esté en `.gitignore`, así que `assets/rosas` no debe ignorarse o las fotos no
entran en el APK.

## Pendiente
- Recibir de la finca el proceso de sanación (pasos, errores típicos, fotos o video).
- Definir cuándo y dónde se usa la tablet (los celulares no están permitidos en el cultivo).
- Más fotos de "pasado / sobreabierto".
