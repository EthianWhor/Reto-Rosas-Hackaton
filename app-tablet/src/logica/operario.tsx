import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { AppState, View } from 'react-native';

import type { Rol, Usuario } from '@/data/usuarios';
import { revisar, supabase } from '@/logica/supabase';

// Sesión de la tablet. La tablet es compartida (va a la entrada del invernadero): cada persona
// entra con su nombre y su PIN, y al terminar sale para que entre la siguiente.
// Por seguridad la sesión NO se guarda en la tablet: al abrir la app siempre se pide el PIN, y se
// cierra sola si nadie toca la pantalla un rato o si la app pasa a segundo plano.
// La lista de personas sí se guarda, para mostrarla aunque se caiga la conexión.
const CLAVE_USUARIOS = 'usuarios:v2';
/** Versiones anteriores guardaban la sesión aquí; al abrir se cierra y se borra. */
const CLAVE_SESION_VIEJA = 'sesion:v2';
const INACTIVIDAD_MS = 3 * 60 * 1000;

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
  /** true si la última sesión se cerró sola por inactividad (para avisarlo en el ingreso). */
  cerradaPorInactividad: boolean;
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
  cerradaPorInactividad: false,
  recargarUsuarios: async () => {},
  crearPersona: async () => {},
  quitarPersona: async () => {},
});

export function OperarioProvider({ children }: { children: ReactNode }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [sesion, setSesion] = useState<Sesion | null>(null);
  const [cerradaPorInactividad, setCerradaPorInactividad] = useState(false);
  const sesionActual = useRef<Sesion | null>(null);
  const ultimoToque = useRef(Date.now());
  sesionActual.current = sesion;

  const recargarUsuarios = useCallback(async () => {
    const lista = revisar(await supabase.rpc('listar_personas')) as Usuario[];
    setUsuarios(lista);
    await AsyncStorage.setItem(CLAVE_USUARIOS, JSON.stringify(lista));
  }, []);

  const salir = useCallback((porInactividad = false) => {
    const actual = sesionActual.current;
    if (!actual) return;
    supabase.rpc('salir', { p_token: actual.token }).then(() => {});
    setSesion(null);
    setCerradaPorInactividad(porInactividad);
  }, []);

  useEffect(() => {
    AsyncStorage.multiGet([CLAVE_USUARIOS, CLAVE_SESION_VIEJA]).then(([[, u], [, vieja]]) => {
      if (u) setUsuarios(JSON.parse(u) as Usuario[]);
      if (vieja) {
        const { token } = JSON.parse(vieja) as Sesion;
        supabase.rpc('salir', { p_token: token }).then(() => {});
        AsyncStorage.removeItem(CLAVE_SESION_VIEJA);
      }
    });
    recargarUsuarios().catch(() => {});

    // Si alguien agrega o quita personas en otra tablet (o en Supabase), la lista se actualiza sola.
    const canal = supabase
      .channel('personas')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'version_personas' }, () => {
        recargarUsuarios().catch(() => {});
      })
      .subscribe();
    return () => {
      supabase.removeChannel(canal);
    };
  }, [recargarUsuarios]);

  // Si quitaron a la persona que tiene la sesión abierta, se cierra su sesión.
  useEffect(() => {
    if (sesion && usuarios.length > 0 && !usuarios.some((u) => u.id === sesion.usuario.id)) salir();
  }, [usuarios, sesion, salir]);

  // Se cierra sola tras INACTIVIDAD_MS sin tocar la pantalla, o si la app pasa a segundo plano.
  useEffect(() => {
    const reloj = setInterval(() => {
      if (sesionActual.current && Date.now() - ultimoToque.current > INACTIVIDAD_MS) salir(true);
    }, 10_000);
    const estado = AppState.addEventListener('change', (s) => {
      if (s === 'background') salir();
    });
    return () => {
      clearInterval(reloj);
      estado.remove();
    };
  }, [salir]);

  async function entrar(usuario: Usuario, pin: string) {
    const token = revisar(await supabase.rpc('entrar', { p_persona: usuario.id, p_pin: pin })) as string | null;
    if (!token) return false;
    ultimoToque.current = Date.now();
    setCerradaPorInactividad(false);
    setSesion({ token, usuario });
    return true;
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
        salir: () => salir(),
        cerradaPorInactividad,
        recargarUsuarios,
        crearPersona,
        quitarPersona,
      }}
    >
      {/* Cualquier toque en la pantalla cuenta como actividad. */}
      <View
        style={{ flex: 1 }}
        onStartShouldSetResponderCapture={() => {
          ultimoToque.current = Date.now();
          return false;
        }}
      >
        {children}
      </View>
    </OperarioContext.Provider>
  );
}

export function useOperario() {
  return useContext(OperarioContext);
}
