import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';

// Modo turnero: coordinación deja la tablet de la entrada fija en el tablero del turno, y solo se
// sale con el código que eligió al activarlo. Se guarda en la tablet (sobrevive a cerrar la app),
// pero el código nunca se guarda tal cual: solo una huella con sal.
const CLAVE = 'turnero:v1';
export const LARGO_CODIGO = 6;
const MAX_INTENTOS = 5;
const ESPERA_MS = 60_000;

type Guardado = { sal: string; huella: string; activadoPor: string; desde: string };

// FNV-1a de 32 bits repetido: no es criptografía fuerte, pero evita dejar el código a la vista.
function huella(sal: string, codigo: string) {
  let h = 0x811c9dc5;
  let texto = `${sal}:${codigo}`;
  for (let vuelta = 0; vuelta < 2000; vuelta++) {
    for (let i = 0; i < texto.length; i++) {
      h ^= texto.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    texto = h.toString(16) + sal;
  }
  return h.toString(16).padStart(8, '0');
}

type Contexto = {
  /** true mientras la app espera saber si el modo está activo (para no mostrar el ingreso un instante). */
  cargando: boolean;
  activo: boolean;
  activadoPor: string;
  activar: (codigo: string, activadoPor: string) => Promise<void>;
  /** '' si el código es correcto (y sale del modo); si no, el mensaje de error. */
  salirConCodigo: (codigo: string) => Promise<string>;
  /** Salida de emergencia, cuando una persona de coordinación ya confirmó su PIN. */
  salirSinCodigo: () => Promise<void>;
};

const TurneroContext = createContext<Contexto>({
  cargando: true,
  activo: false,
  activadoPor: '',
  activar: async () => {},
  salirConCodigo: async () => '',
  salirSinCodigo: async () => {},
});

export function TurneroProvider({ children }: { children: ReactNode }) {
  const [guardado, setGuardado] = useState<Guardado | null>(null);
  const [cargando, setCargando] = useState(true);
  const [intentos, setIntentos] = useState(0);
  const [bloqueadoHasta, setBloqueadoHasta] = useState(0);

  useEffect(() => {
    AsyncStorage.getItem(CLAVE)
      .then((v) => v && setGuardado(JSON.parse(v) as Guardado))
      .catch(() => {})
      .finally(() => setCargando(false));
  }, []);

  const activar = useCallback(async (codigo: string, activadoPor: string) => {
    const sal = Math.random().toString(36).slice(2, 10);
    const nuevo = { sal, huella: huella(sal, codigo), activadoPor, desde: new Date().toISOString() };
    await AsyncStorage.setItem(CLAVE, JSON.stringify(nuevo));
    setIntentos(0);
    setGuardado(nuevo);
  }, []);

  const salirSinCodigo = useCallback(async () => {
    await AsyncStorage.removeItem(CLAVE);
    setIntentos(0);
    setBloqueadoHasta(0);
    setGuardado(null);
  }, []);

  const salirConCodigo = useCallback(
    async (codigo: string) => {
      if (!guardado) return '';
      const espera = bloqueadoHasta - Date.now();
      if (espera > 0) return `Demasiados intentos. Espera ${Math.ceil(espera / 1000)} s.`;
      if (huella(guardado.sal, codigo) === guardado.huella) {
        await salirSinCodigo();
        return '';
      }
      const n = intentos + 1;
      if (n >= MAX_INTENTOS) {
        setIntentos(0);
        setBloqueadoHasta(Date.now() + ESPERA_MS);
        return 'Demasiados intentos. Espera 1 minuto.';
      }
      setIntentos(n);
      return `Código incorrecto. Te quedan ${MAX_INTENTOS - n} intentos.`;
    },
    [guardado, intentos, bloqueadoHasta, salirSinCodigo],
  );

  return (
    <TurneroContext.Provider
      value={{ cargando, activo: !!guardado, activadoPor: guardado?.activadoPor ?? '', activar, salirConCodigo, salirSinCodigo }}
    >
      {children}
    </TurneroContext.Provider>
  );
}

export function useTurnero() {
  return useContext(TurneroContext);
}
