import type { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';

// Personas que usan la tablet. Hay tres roles:
// - admin: coordinación del turno (asistencia, reparto, usuarios y promociones).
// - experto: corta y revisa las rosas en las que el robot tuvo dudas. No ve los juegos.
// - aprendiz: en capacitación; corta, aprende y practica con el juego.
//
// Viven en Supabase (tabla personas, supabase/schema.sql). El PIN nunca llega a la app: se valida
// en la base y la app solo recibe un token de sesión.

export type Rol = 'admin' | 'experto' | 'aprendiz';

export type Usuario = {
  id: string;
  nombre: string;
  rol: Rol;
};

export const ROLES: Record<Rol, { nombre: string; color: string; fondo: string; icono: ComponentProps<typeof Ionicons>['name'] }> = {
  admin: { nombre: 'Coordinación', color: '#455A64', fondo: '#ECEFF1', icono: 'shield-checkmark' },
  experto: { nombre: 'Experto', color: '#B7791F', fondo: '#FDF3E1', icono: 'star' },
  aprendiz: { nombre: 'Aprendiz', color: '#2E9E5B', fondo: '#E3F5EA', icono: 'leaf' },
};

/** Lo que ve la coordinación en "Usuarios" (incluye a quien no ha activado su usuario). */
export type UsuarioAdmin = Usuario & {
  correo: string | null;
  telefono: string | null;
  /** Todavía no creó su PIN. */
  pendiente: boolean;
  /** Se equivocó 5 veces con el código: hay que darle uno nuevo. */
  bloqueado: boolean;
};

// Validaciones (las mismas que hace la base en supabase/migraciones/003).
export const validar = {
  nombre: (v: string) =>
    /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'. -]{1,59}$/.test(v.trim()) ? '' : 'Solo letras y espacios (mínimo 2).',
  correo: (v: string) => (!v.trim() || /^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(v.trim()) ? '' : 'Correo no válido.'),
  telefono: (v: string) => (!v.trim() || /^\d{7,15}$/.test(v.replace(/[\s+()-]/g, '')) ? '' : 'Entre 7 y 15 números.'),
  pin: (v: string) =>
    !/^\d{4}$/.test(v)
      ? 'El PIN tiene 4 números.'
      : /^(\d)\1{3}$/.test(v) || '0123456789 9876543210'.includes(v)
        ? 'Elige un PIN menos obvio (sin repetir ni seguir números).'
        : '',
};

/** Corrige roles viejos o desconocidos (por ejemplo, "trabajador" antes de la migración 002). */
export function normalizar(u: { id: string; nombre: string; rol: string }): Usuario {
  return { ...u, rol: u.rol in ROLES ? (u.rol as Rol) : 'aprendiz' };
}

/** Quienes cortan en el turno (todos menos coordinación). */
export const cortaEnTurno = (u: Usuario) => u.rol !== 'admin';
