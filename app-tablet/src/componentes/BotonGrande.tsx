import { Ionicons } from '@expo/vector-icons';
import { useRef, type ComponentProps } from 'react';
import { Animated, Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { colores, espacio, fuente, oscurecer, texto } from '@/tema';

type Props = {
  titulo: string;
  subtitulo?: string;
  icono?: ComponentProps<typeof Ionicons>['name'];
  color?: string;
  /** Botón blanco con borde, para acciones secundarias. */
  claro?: boolean;
  onPress: () => void;
  deshabilitado?: boolean;
  estilo?: ViewStyle;
};

// Botón 3D (con borde inferior más oscuro) que se hunde al tocarlo.
export function BotonGrande({ titulo, subtitulo, icono, color = colores.primario, claro, onPress, deshabilitado, estilo }: Props) {
  const hundido = useRef(new Animated.Value(0)).current;
  const fondo = claro ? colores.tarjeta : color;
  const base = claro ? colores.borde : oscurecer(color);
  const letra = claro ? colores.texto : '#fff';

  const animar = (a: number) => Animated.timing(hundido, { toValue: a, duration: 70, useNativeDriver: true }).start();

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={titulo}
      onPress={onPress}
      onPressIn={() => animar(1)}
      onPressOut={() => animar(0)}
      disabled={deshabilitado}
      style={[styles.base, { backgroundColor: base, opacity: deshabilitado ? 0.45 : 1 }, estilo]}
    >
      <Animated.View
        style={[
          styles.cara,
          { backgroundColor: fondo, borderColor: claro ? colores.borde : fondo },
          { transform: [{ translateY: hundido.interpolate({ inputRange: [0, 1], outputRange: [0, 4] }) }] },
        ]}
      >
        {icono && <Ionicons name={icono} size={26} color={claro ? color : '#fff'} />}
        <View style={styles.textos}>
          <Text style={[styles.titulo, { color: letra }]}>{titulo}</Text>
          {subtitulo ? <Text style={[styles.subtitulo, { color: letra }]}>{subtitulo}</Text> : null}
        </View>
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { borderRadius: 18, paddingBottom: 5 },
  cara: {
    minHeight: 64,
    borderRadius: 18,
    borderWidth: 2,
    paddingVertical: espacio.m,
    paddingHorizontal: espacio.l,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: espacio.m,
  },
  textos: { alignItems: 'center', flexShrink: 1 },
  titulo: { fontSize: texto.boton, fontFamily: fuente.negrita, textAlign: 'center' },
  subtitulo: { fontSize: texto.pequeno, fontFamily: fuente.normal, marginTop: 2, opacity: 0.9, textAlign: 'center' },
});
