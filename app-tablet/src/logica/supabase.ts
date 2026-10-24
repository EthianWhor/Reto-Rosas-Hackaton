import { createClient } from '@supabase/supabase-js';

// Cliente de Supabase (esquema en supabase/schema.sql de la raíz del repo). No se usa Supabase
// Auth: cada persona entra con nombre + PIN y las funciones de la base validan su sesión.
export const supabase = createClient(
  process.env.EXPO_PUBLIC_SUPABASE_URL!,
  process.env.EXPO_PUBLIC_SUPABASE_KEY!,
  { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false } },
);

/** Lanza el error de Supabase con un mensaje para mostrar en pantalla. */
export function revisar<T>({ data, error }: { data: T; error: { message: string } | null }): T {
  if (error) throw new Error(error.message.includes('fetch') ? 'Sin conexión con el servidor.' : error.message);
  return data;
}
