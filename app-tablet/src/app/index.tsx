import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import { useOperario } from '@/logica/operario';
import { colores, espacio, texto } from '@/tema';

export default function Inicio() {
  const { nombre, cambiarNombre } = useOperario();
  const [borrador, setBorrador] = useState('');

  if (!nombre) {
    return (
      <View style={styles.centro}>
        <Text style={styles.titulo}>¡Bienvenido!</Text>
        <Text style={styles.cuerpo}>Escribe tu nombre para guardar tu progreso.</Text>
        <TextInput
          value={borrador}
          onChangeText={setBorrador}
          placeholder="Tu nombre"
          style={styles.input}
          autoCapitalize="words"
          returnKeyType="done"
          onSubmitEditing={() => borrador.trim() && cambiarNombre(borrador.trim())}
        />
        <BotonGrande
          titulo="Empezar"
          deshabilitado={!borrador.trim()}
          onPress={() => cambiarNombre(borrador.trim())}
          estilo={styles.ancho}
        />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>Hola, {nombre}</Text>
      <Text style={styles.cuerpo}>¿Qué quieres practicar hoy?</Text>

      <View style={styles.menu}>
        <BotonGrande
          titulo="Aprender las 3 categorías"
          subtitulo="Muy pronto · Punto óptimo · Muy tarde"
          color="#6D4C41"
          onPress={() => router.push('/aprender')}
        />
        <BotonGrande
          titulo="Juego: clasifica el botón"
          subtitulo="Mira la rosa y decide"
          onPress={() => router.push('/clasificar')}
        />
        <BotonGrande
          titulo="Sanación después del corte"
          subtitulo="En construcción"
          color="#33691E"
          onPress={() => router.push('/sanacion')}
        />
        <BotonGrande titulo="Mi progreso" color="#455A64" onPress={() => router.push('/progreso')} />
      </View>

      <Text style={styles.cambiar} onPress={() => cambiarNombre('')}>
        No soy {nombre} · cambiar operario
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl, gap: espacio.m },
  contenido: { padding: espacio.xl, gap: espacio.m, maxWidth: 720, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto },
  cuerpo: { fontSize: texto.cuerpo, color: colores.textoSuave },
  menu: { gap: espacio.m, marginTop: espacio.m },
  input: {
    width: '100%',
    maxWidth: 480,
    fontSize: texto.subtitulo,
    backgroundColor: colores.tarjeta,
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 12,
    padding: espacio.m,
  },
  ancho: { width: '100%', maxWidth: 480 },
  cambiar: { marginTop: espacio.l, color: colores.textoSuave, textDecorationLine: 'underline', textAlign: 'center' },
});
