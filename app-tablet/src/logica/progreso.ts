import AsyncStorage from '@react-native-async-storage/async-storage';

import type { CategoriaId } from '@/data/tipos';

// Por ahora el progreso se guarda solo en la tablet. Más adelante puede enviarse al
// dashboard de coordinadores (ver robot/README.md).
const CLAVE = 'progreso:v1';

export type Respuesta = { rosaId: string; correcta: CategoriaId; elegida: CategoriaId; ms: number };

export type Ronda = {
  fecha: string;
  operario: string;
  respuestas: Respuesta[];
};

export async function leerRondas(): Promise<Ronda[]> {
  const crudo = await AsyncStorage.getItem(CLAVE);
  return crudo ? (JSON.parse(crudo) as Ronda[]) : [];
}

export async function guardarRonda(ronda: Ronda): Promise<void> {
  const rondas = await leerRondas();
  await AsyncStorage.setItem(CLAVE, JSON.stringify([...rondas, ronda]));
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
