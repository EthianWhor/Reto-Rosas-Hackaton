import { Ionicons } from '@expo/vector-icons';
import { useRef, type ComponentProps } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';

import { colores, espacio, fuente, oscurecer, texto } from '@/tema';

type Props = {
  titulo: string;
  detalle?: string;
  icono: ComponentProps<typeof Ionicons>['name'];
  color: string;
  /** Tarjeta grande, de color y a lo ancho, para la acción principal. */
  destacado?: boolean;
  etiqueta?: string;
  onPress: () => void;
};

// Tarjeta del menú de inicio. Las destacadas van a lo ancho con el texto al lado del ícono; las
// demás son cuadradas, todas del mismo alto, con el ícono arriba y el texto abajo.
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
    >
      <Animated.View
        style={[
          styles.tarjeta,
          destacado ? styles.ancha : styles.cuadrada,
          destacado
            ? { backgroundColor: color, borderColor: color, borderBottomColor: oscurecer(color) }
            : { backgroundColor: colores.tarjeta, borderColor: colores.borde },
          { transform: [{ scale: escala }] },
        ]}
      >
        <View style={[styles.icono, { backgroundColor: destacado ? 'rgba(255,255,255,0.22)' : color }]}>
          <Ionicons name={icono} size={destacado ? 34 : 30} color="#fff" />
        </View>

        {destacado ? (
          <>
            <View style={styles.textos}>
              <Text style={styles.tituloGrande} numberOfLines={1}>
                {titulo}
              </Text>
              {detalle ? (
                <Text style={styles.detalleClaro} numberOfLines={1}>
                  {detalle}
                </Text>
              ) : null}
            </View>
            <Ionicons name="chevron-forward" size={28} color="#fff" />
          </>
        ) : (
          <Text style={styles.titulo} numberOfLines={2} adjustsFontSizeToFit minimumFontScale={0.8}>
            {titulo}
          </Text>
        )}

        {etiqueta ? (
          <View style={styles.etiqueta}>
            <Text style={styles.etiquetaTexto}>{etiqueta}</Text>
          </View>
        ) : null}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tarjeta: { borderRadius: 22, borderWidth: 2, borderBottomWidth: 5 },
  ancha: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, padding: espacio.m, paddingVertical: espacio.l },
  cuadrada: { height: 132, alignItems: 'center', justifyContent: 'center', gap: espacio.s, padding: espacio.m },
  icono: { width: 56, height: 56, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  textos: { flex: 1 },
  titulo: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto, textAlign: 'center' },
  tituloGrande: { fontSize: 24, fontFamily: fuente.titulo, color: '#fff' },
  detalleClaro: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: 'rgba(255,255,255,0.9)', marginTop: 2 },
  etiqueta: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: colores.rosaSuave,
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  etiquetaTexto: { fontSize: 12, fontFamily: fuente.negrita, color: colores.rosaOscuro },
});
