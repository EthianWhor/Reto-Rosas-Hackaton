// Copia los recortes de rosas de la finca (generados por robot/ml/prepare_data) a
// assets/rosas/<categoria>/ y regenera src/data/rosas.ts con un require() por foto.
//
// Uso (desde app-tablet/):  npm run fotos
// Origen por defecto: ../robot/data/finca_stages  (subcarpetas train/val/test/<categoria>)
// Otro origen:            npm run fotos -- <carpeta>

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const origen = path.resolve(raiz, process.argv[2] ?? '../robot/data/finca_stages');
const destino = path.join(raiz, 'assets', 'rosas');
const salidaTs = path.join(raiz, 'src', 'data', 'rosas.ts');

// Mismos nombres que robot/ml/stages.py y src/data/categorias.ts.
const CATEGORIAS = ['1_inmaduro', '2_optimo', '3_pasado'];
const EXTENSIONES = new Set(['.jpg', '.jpeg', '.png']);

if (!fs.existsSync(origen)) {
  console.error(`No existe la carpeta de origen: ${origen}`);
  console.error('Primero corran en robot/: python -m ml.prepare_data --yolo data/finca_yolo --out data/finca_stages');
  process.exit(1);
}

// Busca <origen>/<split>/<categoria>/* y también <origen>/<categoria>/*.
function carpetasDe(categoria) {
  const carpetas = [];
  const directa = path.join(origen, categoria);
  if (fs.existsSync(directa)) carpetas.push(directa);
  for (const split of fs.readdirSync(origen, { withFileTypes: true })) {
    const dir = path.join(origen, split.name, categoria);
    if (split.isDirectory() && fs.existsSync(dir)) carpetas.push(dir);
  }
  return carpetas;
}

fs.rmSync(destino, { recursive: true, force: true });
const rosas = [];
for (const categoria of CATEGORIAS) {
  fs.mkdirSync(path.join(destino, categoria), { recursive: true });
  for (const dir of carpetasDe(categoria)) {
    for (const archivo of fs.readdirSync(dir).sort()) {
      if (!EXTENSIONES.has(path.extname(archivo).toLowerCase())) continue;
      fs.copyFileSync(path.join(dir, archivo), path.join(destino, categoria, archivo));
      rosas.push({ id: `${categoria}/${archivo}`, categoria, archivo });
    }
  }
}

const lineas = rosas.map(
  (r) => `  { id: '${r.id}', categoria: '${r.categoria}', imagen: require('../../assets/rosas/${r.categoria}/${r.archivo}') },`,
);
fs.writeFileSync(
  salidaTs,
  `// ARCHIVO GENERADO por scripts/importar-fotos.mjs. No editar a mano: correr \`npm run fotos\`.
import type { Rosa } from './tipos';

export const ROSAS: Rosa[] = [
${lineas.join('\n')}
];
`,
);

const conteo = CATEGORIAS.map((c) => `${c}: ${rosas.filter((r) => r.categoria === c).length}`).join(', ');
console.log(`Copiadas ${rosas.length} fotos a assets/rosas (${conteo}).`);
