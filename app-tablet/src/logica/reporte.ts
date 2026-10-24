import AsyncStorage from '@react-native-async-storage/async-storage';

import { REPORTE_EJEMPLO, type Reporte } from '@/data/reporte';
import { supabase } from '@/logica/supabase';

// El reporte de la última ronda del robot sale de Supabase (tabla reportes; el robot lo sube con
// robot/subir_reporte.py). Sin conexión se usa el último que descargó la tablet y, si nunca
// descargó uno, el de ejemplo.
const CLAVE = 'reporte:ultimo:v1';

export type Origen = 'robot' | 'guardado' | 'ejemplo';

export async function cargarReporte(): Promise<{ reporte: Reporte; origen: Origen }> {
  const { data, error } = await supabase
    .from('reportes')
    .select('datos')
    .order('fecha', { ascending: false })
    .order('recibido', { ascending: false })
    .limit(1)
    .maybeSingle();
  if (!error && data) {
    const reporte = data.datos as Reporte;
    await AsyncStorage.setItem(CLAVE, JSON.stringify(reporte));
    return { reporte, origen: 'robot' };
  }
  const guardado = await AsyncStorage.getItem(CLAVE);
  if (guardado) return { reporte: JSON.parse(guardado) as Reporte, origen: 'guardado' };
  return { reporte: REPORTE_EJEMPLO, origen: 'ejemplo' };
}

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

/** '2026-10-24' → '24 de octubre' */
export function fechaLarga(fecha: string): string {
  const [, mes, dia] = fecha.split('-').map(Number);
  return `${dia} de ${MESES[mes - 1]}`;
}

/** '2026-10-24 23:41:00' → '23:41' */
export function hora(fechaHora: string): string {
  return fechaHora.slice(11, 16);
}
