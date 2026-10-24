import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator, Animated, Pressable, StyleSheet, Text, View } from 'react-native';

import { colores, espacio, fuente } from '@/tema';

const TECLAS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'volver', '0', 'borrar'];

type Props = {
  longitud: number;
  valor: string;
  onCambio: (valor: string) => void;
  onVolver: () => void;
  error?: string;
  ocupado?: boolean;
  /** translateX para sacudir los puntos cuando hay error (de useSacudir). */
  sacudida?: Animated.Value;
};

// Puntos + teclado grande para PIN (4) y código de activación (6). Sin teclado del sistema: se usa
// con guantes o manos mojadas y no tapa nada.
export function TecladoNumerico({ longitud, valor, onCambio, onVolver, error, ocupado, sacudida }: Props) {
  function pulsar(t: string) {
    if (ocupado) return;
    if (t === 'volver') onVolver();
    else if (t === 'borrar') onCambio(valor.slice(0, -1));
    else if (valor.length < longitud) onCambio(valor + t);
  }

  return (
    <View style={styles.contenedor}>
      <Animated.View style={[styles.puntos, sacudida && { transform: [{ translateX: sacudida }] }]}>
        {Array.from({ length: longitud }, (_, i) => (
          <View key={i} style={[styles.punto, i < valor.length && styles.puntoLleno, !!error && styles.puntoError]} />
        ))}
      </Animated.View>
      <View style={styles.aviso}>
        {ocupado ? <ActivityIndicator color={colores.primario} /> : !!error && <Text style={styles.error}>{error}</Text>}
      </View>
      <View style={styles.teclado}>
        {TECLAS.map((t) => (
          <Pressable
            key={t}
            accessibilityRole="button"
            accessibilityLabel={t === 'borrar' ? 'Borrar' : t === 'volver' ? 'Volver' : t}
            style={({ pressed }) => [styles.tecla, t.length > 1 && styles.teclaSuave, pressed && styles.teclaPulsada]}
            onPress={() => pulsar(t)}
          >
            {t === 'borrar' ? (
              <Ionicons name="backspace-outline" size={28} color={colores.textoSuave} />
            ) : t === 'volver' ? (
              <Ionicons name="arrow-back" size={28} color={colores.textoSuave} />
            ) : (
              <Text style={styles.teclaTexto}>{t}</Text>
            )}
          </Pressable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  contenedor: { alignItems: 'center', gap: espacio.s },
  puntos: { flexDirection: 'row', gap: espacio.m, marginTop: espacio.s },
  punto: { width: 20, height: 20, borderRadius: 10, borderWidth: 3, borderColor: colores.rosa },
  puntoLleno: { backgroundColor: colores.primario, borderColor: colores.primario },
  puntoError: { borderColor: colores.error },
  aviso: { minHeight: 28, justifyContent: 'center', paddingHorizontal: espacio.m },
  error: { fontSize: 16, fontFamily: fuente.negrita, color: colores.error, textAlign: 'center' },
  teclado: { flexDirection: 'row', flexWrap: 'wrap', width: 3 * 92 + 2 * espacio.m, gap: espacio.m },
  tecla: {
    width: 92,
    height: 72,
    borderRadius: 22,
    backgroundColor: colores.tarjeta,
    borderWidth: 2,
    borderBottomWidth: 5,
    borderColor: colores.borde,
    justifyContent: 'center',
    alignItems: 'center',
  },
  teclaSuave: { backgroundColor: 'transparent', borderColor: 'transparent' },
  teclaPulsada: { transform: [{ translateY: 3 }], borderBottomWidth: 2 },
  teclaTexto: { fontSize: 30, fontFamily: fuente.titulo, color: colores.texto },
});
