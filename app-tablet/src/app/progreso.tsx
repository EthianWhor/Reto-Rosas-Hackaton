import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { CATEGORIAS } from '@/data/categorias';
import { useOperario } from '@/logica/operario';
import { leerRondas, matrizDeConfusion, type Ronda } from '@/logica/progreso';
import { colores, espacio, texto } from '@/tema';

export default function Progreso() {
  const { nombre } = useOperario();
  const [rondas, setRondas] = useState<Ronda[]>([]);

  useFocusEffect(
    useCallback(() => {
      leerRondas().then((todas) => setRondas(todas.filter((r) => r.operario === nombre)));
    }, [nombre]),
  );

  if (rondas.length === 0) {
    return (
      <View style={styles.centro}>
        <Text style={styles.cuerpo}>Todavía no has jugado ninguna ronda.</Text>
      </View>
    );
  }

  const matriz = matrizDeConfusion(rondas);

  return (
    <ScrollView contentContainerStyle={styles.contenido}>
      <Text style={styles.titulo}>Rondas de {nombre}</Text>
      {rondas
        .slice(-5)
        .reverse()
        .map((r) => {
          const aciertos = r.respuestas.filter((x) => x.correcta === x.elegida).length;
          return (
            <Text key={r.fecha} style={styles.cuerpo}>
              {new Date(r.fecha).toLocaleString()} — {aciertos}/{r.respuestas.length}
            </Text>
          );
        })}

      <Text style={styles.titulo}>Aciertos por categoría</Text>
      {CATEGORIAS.map((c) => {
        const fila = matriz[c.id];
        const total = Object.values(fila).reduce((a, b) => a + b, 0);
        const confusiones = CATEGORIAS.filter((o) => o.id !== c.id && fila[o.id] > 0);
        return (
          <View key={c.id} style={[styles.tarjeta, { borderLeftColor: c.color }]}>
            <Text style={[styles.nombre, { color: c.color }]}>
              {c.boton}: {total ? Math.round((fila[c.id] / total) * 100) : 0}% ({fila[c.id]}/{total})
            </Text>
            {confusiones.map((o) => (
              <Text key={o.id} style={styles.cuerpo}>
                La confundiste {fila[o.id]} {fila[o.id] === 1 ? 'vez' : 'veces'} con «{o.boton}».
              </Text>
            ))}
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl },
  contenido: { padding: espacio.l, gap: espacio.m, maxWidth: 720, width: '100%', alignSelf: 'center' },
  titulo: { fontSize: texto.subtitulo, fontWeight: '800', color: colores.texto, marginTop: espacio.m },
  tarjeta: { backgroundColor: colores.tarjeta, borderRadius: 12, padding: espacio.m, borderLeftWidth: 6, gap: 4 },
  nombre: { fontSize: texto.cuerpo, fontWeight: '700' },
  cuerpo: { fontSize: texto.cuerpo, color: colores.texto },
});
