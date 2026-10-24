import AsyncStorage from '@react-native-async-storage/async-storage';

import type { CategoriaId, Rosa } from '@/data/tipos';
import { revisar, supabase } from '@/logica/supabase';

// Fotos reales del robot con la categoría confirmada (por un experto en "Rosas dudosas", o por el
// robot cuando estuvo muy seguro). Se suman a las fotos de la finca en el juego y en "Aprender", para
// que el material no se repita (supabase/migraciones/004). Sin conexión se usan las últimas descargadas.
const CLAVE = 'fotos-confirmadas:v1';

type Fila = { id: string; categoria: CategoriaId; foto: string; fuente: 'experto' | 'robot' };

const aRosa = (f: Fila): Rosa => ({ id: `robot:${f.id}`, categoria: f.categoria, imagen: { uri: f.foto }, fuente: f.fuente });

export async function cargarConfirmadas(): Promise<Rosa[]> {
  try {
    const filas = revisar(await supabase.rpc('fotos_confirmadas')) as Fila[];
    await AsyncStorage.setItem(CLAVE, JSON.stringify(filas));
    return filas.map(aRosa);
  } catch {
    const guardadas = await AsyncStorage.getItem(CLAVE);
    return guardadas ? (JSON.parse(guardadas) as Fila[]).map(aRosa) : [];
  }
}
