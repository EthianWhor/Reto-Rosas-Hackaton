import { ROSAS } from '@/data/rosas';
import type { CategoriaId, Rosa } from '@/data/tipos';

export const PREGUNTAS_POR_RONDA = 10;

function barajar<T>(lista: T[]): T[] {
  const copia = [...lista];
  for (let i = copia.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copia[i], copia[j]] = [copia[j], copia[i]];
  }
  return copia;
}

/**
 * Arma una ronda de fotos. Las clases están muy desbalanceadas (47 inmaduras, 20 óptimas,
 * 2 pasadas), así que se reparte por categoría para que el operario no aprenda que
 * "casi siempre es muy pronto". Las categorías con pocas fotos pueden repetirse.
 */
export function armarRonda(cantidad = PREGUNTAS_POR_RONDA): Rosa[] {
  const porCategoria = new Map<CategoriaId, Rosa[]>();
  for (const rosa of ROSAS) {
    porCategoria.set(rosa.categoria, [...(porCategoria.get(rosa.categoria) ?? []), rosa]);
  }
  const grupos = [...porCategoria.values()].map(barajar);
  if (grupos.length === 0) return [];

  const ronda: Rosa[] = [];
  for (let i = 0; ronda.length < cantidad; i++) {
    const grupo = grupos[i % grupos.length];
    ronda.push(grupo[Math.floor(i / grupos.length) % grupo.length]);
  }
  return barajar(ronda);
}
