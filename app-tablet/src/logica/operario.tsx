import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

// Sin login: el operario escribe su nombre una vez y queda guardado en la tablet.
const CLAVE = 'operario:v1';

type Contexto = { nombre: string; cambiarNombre: (nombre: string) => void };

const OperarioContext = createContext<Contexto>({ nombre: '', cambiarNombre: () => {} });

export function OperarioProvider({ children }: { children: ReactNode }) {
  const [nombre, setNombre] = useState('');

  useEffect(() => {
    AsyncStorage.getItem(CLAVE).then((guardado) => guardado && setNombre(guardado));
  }, []);

  function cambiarNombre(nuevo: string) {
    setNombre(nuevo);
    AsyncStorage.setItem(CLAVE, nuevo);
  }

  return <OperarioContext.Provider value={{ nombre, cambiarNombre }}>{children}</OperarioContext.Provider>;
}

export function useOperario() {
  return useContext(OperarioContext);
}
