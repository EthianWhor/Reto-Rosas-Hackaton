import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

import type { Rol, Usuario } from '@/data/usuarios';
import { revisar, supabase } from '@/logica/supabase';

// Sesión de la tablet. La tablet es compartida (va a la entrada del invernadero): cada persona
// entra con su nombre y su PIN, y al terminar sale para que entre la siguiente.
// La lista de personas se guarda también en la tablet, para mostrarla aunque se caiga la conexión.
const CLAVE_USUARIOS = 'usuarios:v2';
const CLAVE_SESION = 'sesion:v2';

type Sesion = { token: string; usuario: Usuario };

type Contexto = {
  /** Usuario con la sesión abierta, o null. */
  usuario: Usuario | null;
  /** Nombre del usuario con la sesión abierta ('' si no hay). Lo usan el juego y el progreso. */
  nombre: string;
  /** Token de la sesión, para las funciones de Supabase que escriben. */
  token: string | null;
  usuarios: Usuario[];
  /** Devuelve false si el PIN no coincide; lanza un error si no hay conexión. */
  entrar: (usuario: Usuario, pin: string) => Promise<boolean>;
  salir: () => void;
  recargarUsuarios: () => Promise<void>;
  crearPersona: (nombre: string, rol: Rol, pin: string) => Promise<void>;
  quitarPersona: (id: string) => Promise<void>;
};

const OperarioContext = createContext<Contexto>({
  usuario: null,
  nombre: '',
  token: null,
  usuarios: [],
  entrar: async () => false,
  salir: () => {},
  recargarUsuarios: async () => {},
  crearPersona: async () => {},
  quitarPersona: async () => {},
});

export function OperarioProvider({ children }: { children: ReactNode }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [sesion, setSesion] = useState<Sesion | null>(null);

  const recargarUsuarios = useCallback(async () => {
    const lista = revisar(await supabase.rpc('listar_personas')) as Usuario[];
    setUsuarios(lista);
    await AsyncStorage.setItem(CLAVE_USUARIOS, JSON.stringify(lista));
  }, []);

  useEffect(() => {
    AsyncStorage.multiGet([CLAVE_USUARIOS, CLAVE_SESION]).then(([[, u], [, s]]) => {
      if (u) setUsuarios(JSON.parse(u) as Usuario[]);
      if (s) setSesion(JSON.parse(s) as Sesion);
    });
    recargarUsuarios().catch(() => {});
  }, [recargarUsuarios]);

  async function entrar(usuario: Usuario, pin: string) {
    const token = revisar(await supabase.rpc('entrar', { p_persona: usuario.id, p_pin: pin })) as string | null;
    if (!token) return false;
    const nueva = { token, usuario };
    setSesion(nueva);
    await AsyncStorage.setItem(CLAVE_SESION, JSON.stringify(nueva));
    return true;
  }

  function salir() {
    if (sesion) supabase.rpc('salir', { p_token: sesion.token }).then(() => {});
    setSesion(null);
    AsyncStorage.removeItem(CLAVE_SESION);
  }

  async function crearPersona(nombre: string, rol: Rol, pin: string) {
    revisar(await supabase.rpc('crear_persona', { p_token: sesion?.token, p_nombre: nombre, p_rol: rol, p_pin: pin }));
    await recargarUsuarios();
  }

  async function quitarPersona(id: string) {
    revisar(await supabase.rpc('quitar_persona', { p_token: sesion?.token, p_persona: id }));
    await recargarUsuarios();
  }

  const usuario = sesion?.usuario ?? null;
  return (
    <OperarioContext.Provider
      value={{
        usuario,
        nombre: usuario?.nombre ?? '',
        token: sesion?.token ?? null,
        usuarios,
        entrar,
        salir,
        recargarUsuarios,
        crearPersona,
        quitarPersona,
      }}
    >
      {children}
    </OperarioContext.Provider>
  );
}

export function useOperario() {
  return useContext(OperarioContext);
}
