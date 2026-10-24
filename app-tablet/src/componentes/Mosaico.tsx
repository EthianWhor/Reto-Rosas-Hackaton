import { Ionicons } from '@expo/vector-icons';
import { useRef, type ComponentProps } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';

import { colores, espacio, fuente, oscurecer, texto } from '@/tema';

type Props = {
  titulo: string;
  detalle?: string;
  icono: ComponentProps<typeof Ionicons>['name'];
  color: string;
  /** Tarjeta grande y de color, para la acción principal. */
  destacado?: boolean;
  etiqueta?: string;
  onPress: () => void;
};

// Tarjeta del menú de inicio. Se hunde un poco al tocarla.
export function Mosaico({ titulo, detalle, icono, color, destacado, etiqueta, onPress }: Props) {
  const escala = useRef(new Animated.Value(1)).current;
  const animar = (a: number) => Animated.spring(escala, { toValue: a, friction: 5, tension: 300, useNativeDriver: true }).start();

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={titulo}
      onPress={onPress}
      onPressIn={() => animar(0.96)}
      onPressOut={() => animar(1)}
      style={styles.anchoCompleto}
    >
      <Animated.View
        style={[
          styles.tarjeta,
          destacado
            ? { backgroundColor: color, borderColor: color, borderBottomColor: oscurecer(color) }
            : { backgroundColor: colores.tarjeta, borderColor: colores.borde, borderBottomColor: colores.borde },
          destacado && styles.destacado,
          { transform: [{ scale: escala }] },
        ]}
      >
        <View style={[styles.icono, { backgroundColor: destacado ? 'rgba(255,255,255,0.22)' : color }]}>
          <Ionicons name={icono} size={destacado ? 34 : 28} color="#fff" />
        </View>
        <View style={styles.textos}>
          <Text style={[styles.titulo, { color: destacado ? '#fff' : colores.texto }, destacado && styles.tituloGrande]}>
            {titulo}
          </Text>
          {detalle ? (
            <Text style={[styles.detalle, { color: destacado ? 'rgba(255,255,255,0.9)' : colores.textoSuave }]}>{detalle}</Text>
          ) : null}
        </View>
        {etiqueta ? (
          <View style={styles.etiqueta}>
            <Text style={styles.etiquetaTexto}>{etiqueta}</Text>
          </View>
        ) : destacado ? (
          <Ionicons name="chevron-forward" size={28} color="#fff" />
        ) : null}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  anchoCompleto: { width: '100%' },
  tarjeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: espacio.m,
    padding: espacio.m,
    borderRadius: 22,
    borderWidth: 2,
    borderBottomWidth: 5,
    minHeight: 84,
  },
  destacado: { paddingVertical: espacio.l, minHeight: 104 },
  icono: { width: 54, height: 54, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  textos: { flex: 1 },
  titulo: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita },
  tituloGrande: { fontSize: 24, fontFamily: fuente.titulo },
  detalle: { fontSize: texto.pequeno, fontFamily: fuente.normal, marginTop: 2 },
  etiqueta: { backgroundColor: colores.rosaSuave, borderRadius: 10, paddingHorizontal: 8, paddingVertical: 3 },
  etiquetaTexto: { fontSize: 12, fontFamily: fuente.negrita, color: colores.rosaOscuro },
});
