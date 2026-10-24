import type { Reporte } from '@/data/reporte';
import type { CategoriaId } from '@/data/tipos';
import { revisar, supabase } from '@/logica/supabase';

// Rosas en las que el robot dudó (confianza baja) y que un experto revisa. Las respuestas quedan en
// la tabla etiquetas_expertos de Supabase, para reentrenar a RosaNet (supabase/migraciones/002).

export type Dudosa = NonNullable<Reporte['dudosas']>[number] & {
  id_ronda: string;
  /** Viene del modo foto del robot (demo en vivo), no de una ronda por el invernadero. */
  enVivo: boolean;
};

/** Cuántos reportes recientes se miran: las rondas nocturnas y las fotos del modo en vivo. */
const REPORTES_RECIENTES = 30;

export const esEnVivo = (idRonda: string) => idRonda.includes('_DEMO_');

/** Ids de las dudosas de una ronda que ya revisó algún experto. */
export async function leerRevisadas(idRonda: string): Promise<Set<string>> {
  const ids = revisar(await supabase.rpc('dudosas_revisadas', { p_id_ronda: idRonda })) as string[];
  return new Set(ids ?? []);
}

/**
 * Dudosas sin revisar de los reportes recientes, de la más nueva a la más vieja. Junta todas las
 * rondas (también las del modo foto), porque cada foto en vivo del robot llega como un reporte aparte.
 */
export async function cargarDudosas(): Promise<{ pendientes: Dudosa[]; total: number }> {
  const filas = revisar(
    await supabase.from('reportes').select('id_ronda, datos').order('recibido', { ascending: false }).limit(REPORTES_RECIENTES),
  ) as { id_ronda: string; datos: Reporte }[];

  const conDudosas = filas.filter((f) => (f.datos.dudosas?.length ?? 0) > 0);
  const revisadas = await Promise.all(conDudosas.map((f) => leerRevisadas(f.id_ronda)));

  const pendientes: Dudosa[] = [];
  let total = 0;
  conDudosas.forEach((f, i) => {
    for (const d of f.datos.dudosas!) {
      total++;
      if (!revisadas[i].has(d.rosa_id)) pendientes.push({ ...d, id_ronda: f.id_ronda, enVivo: esEnVivo(f.id_ronda) });
    }
  });
  return { pendientes, total };
}

export async function etiquetarDudosa(
  token: string,
  idRonda: string,
  rosaId: string,
  cuadranteId: string | undefined,
  /** 'no_rosa' si la foto no es una rosa (hoja, mano, poste…): ejemplo negativo para el modelo. */
  categoria: CategoriaId | 'no_rosa',
): Promise<void> {
  revisar(
    await supabase.rpc('etiquetar_dudosa', {
      p_token: token,
      p_id_ronda: idRonda,
      p_rosa_id: rosaId,
      p_cuadrante: cuadranteId ?? null,
      p_categoria: categoria,
    }),
  );
}
