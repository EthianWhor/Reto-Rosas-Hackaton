import type { CategoriaId } from '@/data/tipos';
import { revisar, supabase } from '@/logica/supabase';

// Rosas en las que el robot dudó (confianza baja) y que un experto revisa. Las respuestas quedan en
// la tabla etiquetas_expertos de Supabase, para reentrenar a RosaNet (supabase/migraciones/002).

/** Ids de las dudosas de una ronda que ya revisó algún experto. */
export async function leerRevisadas(idRonda: string): Promise<Set<string>> {
  const ids = revisar(await supabase.rpc('dudosas_revisadas', { p_id_ronda: idRonda })) as string[];
  return new Set(ids ?? []);
}

export async function etiquetarDudosa(
  token: string,
  idRonda: string,
  rosaId: string,
  cuadranteId: string | undefined,
  categoria: CategoriaId,
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
