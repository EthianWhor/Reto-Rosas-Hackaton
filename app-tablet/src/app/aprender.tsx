import { Image } from 'expo-image';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { CATEGORIAS } from '@/data/categorias';
import { ROSAS } from '@/data/rosas';
import { colores, espacio, texto } from '@/tema';

// Ficha de estudio: una tarjeta por categoría con ejemplos reales de la finca y qué mirar.
export default function Aprender() {
  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.intro}>
        El punto de corte de la finca es el <Text style={styles.negrita}>punto 3</Text>. La rosa se corta antes de abrir
        del todo porque termina de abrir en el camino al cliente.
      </Text>

      {CATEGORIAS.map((cat) => {
        const ejemplos = ROSAS.filter((r) => r.categoria === cat.id).slice(0, 4);
        return (
          <View key={cat.id} style={[styles.tarjeta, { borderLeftColor: cat.color }]}>
            <Text style={[styles.nombre, { color: cat.color }]}>{cat.boton}</Text>
            <Text style={styles.finca}>{cat.nombreFinca}</Text>

            <View style={styles.fotos}>
              {ejemplos.map((r) => (
                <Image key={r.id} source={r.imagen} style={styles.foto} contentFit="cover" />
              ))}
            </View>

            <Text style={styles.seccion}>Qué mirar</Text>
            {cat.mirar.map((m) => (
              <Text key={m} style={styles.punto}>
                • {m}
              </Text>
            ))}
            <Text style={styles.seccion}>Cómo no confundirla</Text>
            <Text style={styles.punto}>{cat.diferencia}</Text>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.l, maxWidth: 900, width: '100%', alignSelf: 'center' },
  intro: { fontSize: texto.cuerpo, color: colores.texto, lineHeight: 26 },
  negrita: { fontWeight: '800' },
  tarjeta: {
    backgroundColor: colores.tarjeta,
    borderRadius: 16,
    padding: espacio.l,
    borderLeftWidth: 8,
    gap: espacio.s,
  },
  nombre: { fontSize: texto.titulo, fontWeight: '800' },
  finca: { fontSize: 16, color: colores.textoSuave },
  fotos: { flexDirection: 'row', flexWrap: 'wrap', gap: espacio.s, marginVertical: espacio.s },
  foto: { width: 140, height: 140, borderRadius: 12, backgroundColor: colores.borde },
  seccion: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto, marginTop: espacio.s },
  punto: { fontSize: texto.cuerpo, color: colores.texto, lineHeight: 26 },
});
