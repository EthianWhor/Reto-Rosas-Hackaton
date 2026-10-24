import AsyncStorage from '@react-native-async-storage/async-storage';

import type { CategoriaId } from '@/data/tipos';

import { revisar, supabase } from '@/logica/supabase';

// El progreso se guarda en Supabase (tabla rondas_juego) y también en la tablet, para no perder
// una ronda si se cae la conexión.
const CLAVE = 'progreso:v1';

export type Respuesta = { rosaId: string; correcta: CategoriaId; elegida: CategoriaId; ms: number };

export type Ronda = {
  fecha: string;
  operario: string;
  respuestas: Respuesta[];
};

async function leerLocales(): Promise<Ronda[]> {
  const crudo = await AsyncStorage.getItem(CLAVE);
  return crudo ? (JSON.parse(crudo) as Ronda[]) : [];
}

/** Rondas de la persona con la sesión abierta: de Supabase o, sin conexión, las de la tablet. */
export async function leerRondas(token: string | null, operario: string): Promise<Ronda[]> {
  if (token) {
    try {
      const filas = revisar(await supabase.rpc('mis_rondas_juego', { p_token: token })) as {
        fecha: string;
        respuestas: Respuesta[];
      }[];
      return filas.map((f) => ({ fecha: f.fecha, operario, respuestas: f.respuestas }));
    } catch {
      // sin conexión: se usan las guardadas en la tablet
    }
  }
  return (await leerLocales()).filter((r) => r.operario === operario);
}

export async function guardarRonda(token: string | null, ronda: Ronda): Promise<void> {
  const rondas = await leerLocales();
  await AsyncStorage.setItem(CLAVE, JSON.stringify([...rondas, ronda]));
  if (token) await supabase.rpc('guardar_ronda_juego', { p_token: token, p_respuestas: ronda.respuestas });
}

export async function borrarProgreso(): Promise<void> {
  await AsyncStorage.removeItem(CLAVE);
}

/** Cuenta cuántas veces se respondió `elegida` cuando la correcta era `correcta`. */
export function matrizDeConfusion(rondas: Ronda[]): Record<CategoriaId, Record<CategoriaId, number>> {
  const ids: CategoriaId[] = ['1_inmaduro', '2_optimo', '3_pasado'];
  const matriz = Object.fromEntries(ids.map((c) => [c, Object.fromEntries(ids.map((e) => [e, 0]))])) as Record<
    CategoriaId,
    Record<CategoriaId, number>
  >;
  for (const r of rondas.flatMap((x) => x.respuestas)) matriz[r.correcta][r.elegida]++;
  return matriz;
}
