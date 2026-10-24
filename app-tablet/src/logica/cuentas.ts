import { normalizar, type Rol, type Usuario, type UsuarioAdmin } from '@/data/usuarios';
import { revisar, supabase } from '@/logica/supabase';

// Alta y activación de usuarios (supabase/migraciones/003). La coordinación nunca conoce el PIN de
// nadie: registra a la persona y le entrega un código de 6 dígitos; la persona activa su usuario con
// ese código y crea su propio PIN.

/** Lista completa para la coordinación, con contacto y estado de activación. */
export async function listarUsuarios(token: string): Promise<UsuarioAdmin[]> {
  const filas = revisar(await supabase.rpc('listar_usuarios', { p_token: token })) as UsuarioAdmin[];
  return (filas ?? []).map((f) => ({ ...f, ...normalizar(f) }));
}

/** Registra a una persona y devuelve su código de activación (se muestra una sola vez). */
export async function crearUsuario(token: string, datos: { nombre: string; correo: string; telefono: string; rol: Rol }) {
  const filas = revisar(
    await supabase.rpc('crear_persona', {
      p_token: token,
      p_nombre: datos.nombre.trim(),
      p_correo: datos.correo.trim(),
      p_telefono: datos.telefono.trim(),
      p_rol: datos.rol,
    }),
  ) as { id: string; codigo: string }[];
  return filas[0];
}

/** Borra el PIN de alguien y devuelve un código nuevo (olvidó el PIN o se bloqueó). */
export async function reiniciarAcceso(token: string, persona: string): Promise<string> {
  return revisar(await supabase.rpc('reiniciar_acceso', { p_token: token, p_persona: persona })) as string;
}

/** Personas registradas que todavía no han activado su usuario (solo id y nombre). */
export async function listarPendientes(): Promise<Pick<Usuario, 'id' | 'nombre'>[]> {
  return (revisar(await supabase.rpc('listar_pendientes')) as Pick<Usuario, 'id' | 'nombre'>[]) ?? [];
}

type Respuesta = { ok?: boolean; token?: string; error?: string; pin?: boolean };

/** Paso 1: revisa el código. Devuelve '' si está bien o el mensaje de error. */
export async function verificarCodigo(persona: string, codigo: string): Promise<string> {
  const r = revisar(await supabase.rpc('verificar_codigo', { p_persona: persona, p_codigo: codigo })) as Respuesta;
  return r.error ?? '';
}

/** Paso 2: crea el PIN y devuelve el token de sesión, o el error. */
export async function activarUsuario(persona: string, codigo: string, pin: string) {
  return revisar(await supabase.rpc('activar_usuario', { p_persona: persona, p_codigo: codigo, p_pin: pin })) as Respuesta;
}
