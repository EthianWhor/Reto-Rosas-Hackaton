import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { colores, espacio, texto } from '@/tema';

// PENDIENTE: la finca todavía no ha enviado el proceso de sanación (ver CONTEXTO.md, sección 4).
// No inventar pasos: cuando llegue el material, cargarlo en src/data/sanacion.ts y armar aquí
// un juego de "ordena los pasos" + "¿qué está mal en esta foto?".
export default function Sanacion() {
  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <View style={styles.aviso}>
        <Text style={styles.titulo}>En construcción</Text>
        <Text style={styles.cuerpo}>
          Aquí vas a practicar el tratamiento que se le hace a la planta después del corte para que vuelva a crecer y
          siga produciendo.
        </Text>
        <Text style={styles.cuerpo}>Estamos esperando que la finca nos comparta los pasos del proceso.</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, maxWidth: 720, width: '100%', alignSelf: 'center' },
  aviso: { backgroundColor: colores.tarjeta, borderRadius: 16, padding: espacio.l, gap: espacio.m },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.texto, lineHeight: 26 },
});
