import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { Aparecer } from '@/componentes/animaciones';
import { BotonGrande } from '@/componentes/BotonGrande';
import { CATEGORIAS } from '@/data/categorias';
import { ROSAS } from '@/data/rosas';
import { colores, espacio, fuente, sombra, texto } from '@/tema';

// Ficha de estudio: una tarjeta por categoría con fotos reales de la finca y qué mirar.
export default function Aprender() {
  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Aparecer>
        <Text style={styles.titulo}>Las 3 categorías</Text>
        <Text style={styles.subtitulo}>Se corta en el punto 3: termina de abrir camino al cliente.</Text>
      </Aparecer>

      {CATEGORIAS.map((cat, i) => (
        <Aparecer key={cat.id} retraso={100 + i * 100} estilo={styles.tarjeta}>
          <View style={[styles.cabeza, { backgroundColor: cat.color }]}>
            <Ionicons name={cat.icono} size={28} color="#fff" />
            <View>
              <Text style={styles.nombre}>{cat.boton}</Text>
              <Text style={styles.finca}>{cat.nombreFinca}</Text>
            </View>
          </View>

          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.fotos}>
            {ROSAS.filter((r) => r.categoria === cat.id)
              .slice(0, 6)
              .map((r) => (
                <Image key={r.id} source={r.imagen} style={styles.foto} contentFit="cover" />
              ))}
          </ScrollView>

          <View style={styles.cuerpo}>
            {cat.mirar.map((m) => (
              <View key={m} style={styles.rasgo}>
                <Ionicons name="checkmark-circle" size={22} color={cat.color} />
                <Text style={styles.rasgoTexto}>{m}</Text>
              </View>
            ))}
            <Text style={styles.pista}>{cat.pista}</Text>
          </View>
        </Aparecer>
      ))}

      <BotonGrande titulo="Practicar ahora" icono="flash" color={colores.rosa} onPress={() => router.replace('/clasificar')} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.l, maxWidth: 820, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontFamily: fuente.titulo, color: colores.texto },
  subtitulo: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, marginTop: 4 },
  tarjeta: { backgroundColor: colores.tarjeta, borderRadius: 24, overflow: 'hidden', ...sombra },
  cabeza: { flexDirection: 'row', alignItems: 'center', gap: espacio.m, padding: espacio.m, paddingHorizontal: espacio.l },
  nombre: { fontSize: 24, fontFamily: fuente.titulo, color: '#fff' },
  finca: { fontSize: texto.pequeno, fontFamily: fuente.normal, color: 'rgba(255,255,255,0.9)' },
  fotos: { gap: espacio.s, padding: espacio.m },
  foto: { width: 130, height: 130, borderRadius: 16, backgroundColor: colores.borde },
  cuerpo: { paddingHorizontal: espacio.l, paddingBottom: espacio.l, gap: espacio.s },
  rasgo: { flexDirection: 'row', alignItems: 'center', gap: espacio.s },
  rasgoTexto: { fontSize: texto.cuerpo + 1, fontFamily: fuente.negrita, color: colores.texto },
  pista: { fontSize: texto.cuerpo, fontFamily: fuente.normal, color: colores.textoSuave, marginTop: espacio.xs },
});
