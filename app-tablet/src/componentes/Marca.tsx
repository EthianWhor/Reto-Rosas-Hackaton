import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';

import { colores, fuente } from '@/tema';

/** Logo de RoseApp: una rosa dentro de un círculo y el nombre. */
export function Marca({ tamano = 28 }: { tamano?: number }) {
  return (
    <View style={styles.fila}>
      <View style={[styles.circulo, { width: tamano * 1.6, height: tamano * 1.6, borderRadius: tamano }]}>
        <Ionicons name="rose" size={tamano} color="#fff" />
      </View>
      <Text style={[styles.nombre, { fontSize: tamano }]}>
        Rose<Text style={{ color: colores.primario }}>App</Text>
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  fila: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  circulo: { backgroundColor: colores.primario, justifyContent: 'center', alignItems: 'center' },
  nombre: { fontFamily: fuente.titulo, color: colores.texto },
});
