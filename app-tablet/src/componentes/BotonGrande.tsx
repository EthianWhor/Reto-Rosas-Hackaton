import { Pressable, StyleSheet, Text, type ViewStyle } from 'react-native';

import { colores, espacio, texto } from '@/tema';

type Props = {
  titulo: string;
  subtitulo?: string;
  color?: string;
  onPress: () => void;
  deshabilitado?: boolean;
  estilo?: ViewStyle;
};

export function BotonGrande({ titulo, subtitulo, color = colores.primario, onPress, deshabilitado, estilo }: Props) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={deshabilitado}
      style={({ pressed }) => [
        styles.boton,
        { backgroundColor: color, opacity: deshabilitado ? 0.4 : pressed ? 0.8 : 1 },
        estilo,
      ]}
    >
      <Text style={styles.titulo}>{titulo}</Text>
      {subtitulo ? <Text style={styles.subtitulo}>{subtitulo}</Text> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  boton: {
    minHeight: 72,
    borderRadius: 16,
    paddingVertical: espacio.m,
    paddingHorizontal: espacio.l,
    justifyContent: 'center',
    alignItems: 'center',
  },
  titulo: { color: '#fff', fontSize: texto.boton, fontWeight: '700', textAlign: 'center' },
  subtitulo: { color: '#fff', fontSize: 15, marginTop: 4, opacity: 0.9, textAlign: 'center' },
});
