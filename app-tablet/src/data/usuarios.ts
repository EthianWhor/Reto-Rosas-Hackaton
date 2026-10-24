// Personas que usan la tablet. Hay dos roles:
// - admin: coordina el turno (quién vino, cuánto dura el turno) y ve el avance de todos.
// - trabajador: ve los cuadrantes que le tocan, los marca como hechos y practica.
//
// Viven en Supabase (tabla personas, supabase/schema.sql). El PIN nunca llega a la app: se valida
// en la base y la app solo recibe un token de sesión.

export type Rol = 'admin' | 'trabajador';

export type Usuario = {
  id: string;
  nombre: string;
  rol: Rol;
};
