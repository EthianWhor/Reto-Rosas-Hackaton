import { useEffect, useState } from 'react';
import { Keyboard } from 'react-native';

/**
 * Alto del teclado en pantalla (0 si está cerrado). Sirve para dejar ese espacio libre al final de
 * un formulario y que el botón de enviar no quede tapado. En Expo Go no está disponible
 * react-native-keyboard-controller, y KeyboardAvoidingView no siempre alcanza en Android con la
 * pantalla de borde a borde.
 */
export function useAlturaTeclado() {
  const [altura, setAltura] = useState(0);
  useEffect(() => {
    const abre = Keyboard.addListener('keyboardDidShow', (e) => setAltura(e.endCoordinates.height));
    const cierra = Keyboard.addListener('keyboardDidHide', () => setAltura(0));
    return () => {
      abre.remove();
      cierra.remove();
    };
  }, []);
  return altura;
}
