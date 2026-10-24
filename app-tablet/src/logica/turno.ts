import type { Cuadrante, Reporte } from '@/data/reporte';
import type { Usuario } from '@/data/usuarios';
import { revisar, supabase } from '@/logica/supabase';

// Reparto del turno: con el reporte del robot, quién vino hoy y cuánto dura el turno, a cada
// trabajador le tocan cuadrantes distintos. Es determinístico: con los mismos datos todos ven el
// mismo reparto en la tablet.

export type ConfigTurno = {
  /** Horas del turno dedicadas a cortar. */
  horasCorte: number;
  /** Segundos que toma cortar una rosa (mirar, cortar, sanar la planta, dejarla en el carro). */
  segundosPorRosa: number;
  /** Minutos para llegar a un cuadrante y acomodarse. */
  minutosPorCuadrante: number;
};

// Supuestos para la demo; los ajusta la coordinadora en la pantalla del turno.
export const CONFIG_INICIAL: ConfigTurno = { horasCorte: 6, segundosPorRosa: 30, minutosPorCuadrante: 2 };

export type Tarea = { cuadrante: Cuadrante; minutos: number };

export type Reparto = {
  porTrabajador: Record<string, { tareas: Tarea[]; minutos: number }>;
  /** Cuadrantes con rosas para hoy que no caben en el turno de nadie. */
  sinAsignar: Tarea[];
};

export function minutosDe(c: Cuadrante, config: ConfigTurno): number {
  return config.minutosPorCuadrante + (c.optimo * config.segundosPorRosa) / 60;
}

/**
 * 1. Si no alcanza el tiempo de todos, se quedan los cuadrantes de mayor prioridad del robot y el
 *    resto queda sin asignar.
 * 2. Los elegidos se ordenan por cama y tramo (el recorrido por el invernadero) y se parten en
 *    zonas seguidas con más o menos el mismo tiempo: cada persona trabaja en camas vecinas y no
 *    camina de un extremo al otro.
 */
export function repartir(reporte: Reporte, trabajadores: Usuario[], config: ConfigTurno): Reparto {
  const capacidad = config.horasCorte * 60;
  const ids = [...trabajadores].sort((a, b) => a.id.localeCompare(b.id)).map((t) => t.id);
  const porTrabajador: Reparto['porTrabajador'] = Object.fromEntries(ids.map((id) => [id, { tareas: [], minutos: 0 }]));
  const sinAsignar: Tarea[] = [];

  const pendientes = reporte.cuadrantes
    .filter((c) => c.optimo > 0)
    .sort((a, b) => a.orden - b.orden)
    .map((cuadrante) => ({ cuadrante, minutos: minutosDe(cuadrante, config) }));
  if (ids.length === 0) return { porTrabajador, sinAsignar: pendientes };

  const elegidas: Tarea[] = [];
  let total = 0;
  for (const tarea of pendientes) {
    if (total + tarea.minutos <= capacidad * ids.length) {
      elegidas.push(tarea);
      total += tarea.minutos;
    } else sinAsignar.push(tarea);
  }

  elegidas.sort((a, b) => a.cuadrante.cama - b.cuadrante.cama || a.cuadrante.tramo - b.cuadrante.tramo);
  const objetivo = total / ids.length;
  let k = 0;
  for (const tarea of elegidas) {
    while (k < ids.length - 1 && porTrabajador[ids[k]].minutos + tarea.minutos > capacidad) k++;
    const actual = porTrabajador[ids[k]];
    if (actual.minutos + tarea.minutos > capacidad) {
      sinAsignar.push(tarea);
      continue;
    }
    actual.tareas.push(tarea);
    actual.minutos += tarea.minutos;
    if (actual.minutos >= objetivo && k < ids.length - 1) k++;
  }
  return { porTrabajador, sinAsignar };
}

// --- Lo que se guarda en Supabase (supabase/schema.sql). Leer es público; escribir pide el token
// de la sesión, y la base revisa que sea de un admin cuando hace falta. ---

export async function leerConfig(): Promise<ConfigTurno> {
  const fila = revisar(
    await supabase.from('config_turno').select('horas_corte, segundos_por_rosa, minutos_por_cuadrante').maybeSingle(),
  );
  if (!fila) return CONFIG_INICIAL;
  return {
    horasCorte: Number(fila.horas_corte),
    segundosPorRosa: fila.segundos_por_rosa,
    minutosPorCuadrante: fila.minutos_por_cuadrante,
  };
}

export async function guardarConfig(token: string, config: ConfigTurno): Promise<void> {
  revisar(
    await supabase.rpc('guardar_config', {
      p_token: token,
      p_horas: config.horasCorte,
      p_segundos: config.segundosPorRosa,
      p_minutos: config.minutosPorCuadrante,
    }),
  );
}

/** Ids de los trabajadores que vinieron. Si la coordinadora no ha marcado a nadie, son todos. */
export async function leerPresentes(fecha: string, trabajadores: Usuario[]): Promise<string[]> {
  const fila = revisar(await supabase.from('asistencia').select('presentes').eq('fecha', fecha).maybeSingle());
  return fila ? (fila.presentes as string[]) : trabajadores.map((t) => t.id);
}

export async function guardarPresentes(token: string, fecha: string, ids: string[]): Promise<void> {
  revisar(await supabase.rpc('guardar_asistencia', { p_token: token, p_fecha: fecha, p_presentes: ids }));
}

/** Cuadrantes marcados como hechos en esta ronda: cuadrante_id → id de quien lo marcó. */
export async function leerHechos(idRonda: string): Promise<Record<string, string>> {
  const filas = revisar(
    await supabase.from('cuadrantes_hechos').select('cuadrante_id, persona_id').eq('id_ronda', idRonda),
  );
  return Object.fromEntries((filas ?? []).map((f) => [f.cuadrante_id as string, f.persona_id as string]));
}

export async function marcarHecho(token: string, idRonda: string, cuadranteId: string, hecho: boolean) {
  revisar(
    await supabase.rpc('marcar_hecho', { p_token: token, p_id_ronda: idRonda, p_cuadrante: cuadranteId, p_hecho: hecho }),
  );
}

/** '1 h 25 min' */
export function duracion(minutos: number): string {
  const m = Math.round(minutos);
  const h = Math.floor(m / 60);
  if (h === 0) return `${m} min`;
  return m % 60 === 0 ? `${h} h` : `${h} h ${m % 60} min`;
}
