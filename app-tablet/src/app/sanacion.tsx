import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, View } from 'react-native';

import { Aparecer } from '@/componentes/animaciones';
import { colores, espacio, fuente, texto } from '@/tema';

// PENDIENTE: la finca todavía no ha enviado el proceso de sanación (ver CONTEXTO.md, sección 4).
// No inventar pasos: cuando llegue el material, cargarlo en src/data/sanacion.ts y armar aquí
// un juego de "ordena los pasos" + "¿qué está mal en esta foto?".
export default function Sanacion() {
  return (
    <View style={styles.centro}>
      <Aparecer estilo={styles.centrado}>
        <View style={styles.icono}>
          <Ionicons name="medkit" size={56} color="#fff" />
        </View>
        <Text style={styles.titulo}>Muy pronto</Text>
        <Text style={styles.cuerpo}>Aquí vas a practicar cómo sanar la planta después del corte.</Text>
      </Aparecer>
    </View>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  centrado: { alignItems: 'center', gap: espacio.m, maxWidth: 420 },
  icono: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#26A69A',
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 6,
    borderBottomColor: '#1B7C73',
  },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, textAlign: 'center' },
});
