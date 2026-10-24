import * as Haptics from 'expo-haptics';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';

import { BotonGrande } from '@/componentes/BotonGrande';
import { categoria, CATEGORIAS } from '@/data/categorias';
import type { CategoriaId } from '@/data/tipos';
import { useOperario } from '@/logica/operario';
import { guardarRonda, type Respuesta } from '@/logica/progreso';
import { armarRonda } from '@/logica/ronda';
import { colores, espacio, texto } from '@/tema';

// Juego principal: se muestra una rosa real de la finca, el operario elige la categoría y
// recibe de inmediato el porqué. Al final de la ronda se guarda el resultado.
export default function Clasificar() {
  const { nombre, token } = useOperario();
  const { width, height } = useWindowDimensions();
  const horizontal = width > height;

  const [ronda, setRonda] = useState(() => armarRonda());
  const [indice, setIndice] = useState(0);
  const [respuestas, setRespuestas] = useState<Respuesta[]>([]);
  const [elegida, setElegida] = useState<CategoriaId | null>(null);
  const inicioPregunta = useRef(Date.now());

  if (ronda.length === 0) {
    return (
      <View style={styles.centro}>
        <Text style={styles.titulo}>No hay fotos cargadas</Text>
        <Text style={styles.cuerpo}>Corran `npm run fotos` en app-tablet/ para copiar las rosas de la finca.</Text>
      </View>
    );
  }

  const terminada = indice >= ronda.length;
  if (terminada) {
    const aciertos = respuestas.filter((r) => r.correcta === r.elegida).length;
    return (
      <View style={styles.centro}>
        <Text style={styles.titulo}>
          {aciertos} de {ronda.length} correctas
        </Text>
        <Text style={styles.cuerpo}>{mensajeFinal(aciertos / ronda.length)}</Text>
        <View style={styles.acciones}>
          <BotonGrande titulo="Jugar otra ronda" onPress={reiniciar} />
          <BotonGrande titulo="Ver mi progreso" color="#455A64" onPress={() => router.replace('/progreso')} />
        </View>
      </View>
    );
  }

  const rosa = ronda[indice];
  const correcta = categoria(rosa.categoria);
  const acerto = elegida === rosa.categoria;

  function responder(id: CategoriaId) {
    if (elegida) return;
    setElegida(id);
    setRespuestas((prev) => [
      ...prev,
      { rosaId: rosa.id, correcta: rosa.categoria, elegida: id, ms: Date.now() - inicioPregunta.current },
    ]);
    Haptics.notificationAsync(
      id === rosa.categoria ? Haptics.NotificationFeedbackType.Success : Haptics.NotificationFeedbackType.Error,
    ).catch(() => {});
  }

  function siguiente() {
    const nuevoIndice = indice + 1;
    if (nuevoIndice >= ronda.length) {
      guardarRonda(token, { fecha: new Date().toISOString(), operario: nombre, respuestas }).catch(() => {});
    }
    setElegida(null);
    setIndice(nuevoIndice);
    inicioPregunta.current = Date.now();
  }

  function reiniciar() {
    setRonda(armarRonda());
    setIndice(0);
    setRespuestas([]);
    setElegida(null);
    inicioPregunta.current = Date.now();
  }

  return (
    <ScrollView contentContainerStyle={[styles.contenido, horizontal && styles.fila]}>
      <View style={horizontal ? styles.mitad : undefined}>
        <Text style={styles.contador}>
          Rosa {indice + 1} de {ronda.length}
        </Text>
        <Image
          source={rosa.imagen}
          style={[styles.foto, { height: horizontal ? height * 0.7 : width * 0.9 }]}
          contentFit="contain"
        />
      </View>

      <View style={[styles.panel, horizontal && styles.mitad]}>
        {!elegida ? (
          <>
            <Text style={styles.pregunta}>¿En qué punto está esta rosa?</Text>
            {CATEGORIAS.map((c) => (
              <BotonGrande key={c.id} titulo={c.boton} subtitulo={c.nombreFinca} color={c.color} onPress={() => responder(c.id)} />
            ))}
          </>
        ) : (
          <View style={styles.feedback}>
            <Text style={[styles.veredicto, { color: acerto ? colores.acierto : colores.error }]}>
              {acerto ? '¡Correcto!' : `No. Era: ${correcta.boton}`}
            </Text>
            {!acerto ? (
              <Text style={styles.cuerpo}>Elegiste «{categoria(elegida).boton}».</Text>
            ) : null}
            <Text style={styles.seccion}>Fíjate en</Text>
            {correcta.mirar.map((m) => (
              <Text key={m} style={styles.cuerpo}>
                • {m}
              </Text>
            ))}
            <Text style={styles.cuerpo}>{correcta.diferencia}</Text>
            <BotonGrande titulo="Siguiente" onPress={siguiente} estilo={{ marginTop: espacio.m }} />
          </View>
        )}
      </View>
    </ScrollView>
  );
}

function mensajeFinal(proporcion: number) {
  if (proporcion >= 0.9) return '¡Excelente ojo! Ya reconoces el punto de corte.';
  if (proporcion >= 0.6) return 'Vas bien. Repasa las rosas en las que fallaste.';
  return 'Sigue practicando. Revisa “Aprender las 3 categorías” antes de la próxima ronda.';
}

const styles = StyleSheet.create({
  contenido: { padding: espacio.l, gap: espacio.l },
  fila: { flexDirection: 'row', alignItems: 'flex-start' },
  mitad: { flex: 1 },
  centro: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: espacio.xl, gap: espacio.m },
  acciones: { gap: espacio.m, width: '100%', maxWidth: 480 },
  titulo: { fontSize: texto.titulo, fontWeight: '800', color: colores.texto, textAlign: 'center' },
  contador: { fontSize: 16, color: colores.textoSuave, marginBottom: espacio.s },
  foto: { width: '100%', borderRadius: 16, backgroundColor: '#000' },
  panel: { gap: espacio.m },
  pregunta: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto },
  feedback: { backgroundColor: colores.tarjeta, borderRadius: 16, padding: espacio.l, gap: espacio.s },
  veredicto: { fontSize: texto.titulo, fontWeight: '800' },
  seccion: { fontSize: texto.subtitulo, fontWeight: '700', color: colores.texto, marginTop: espacio.s },
  cuerpo: { fontSize: texto.cuerpo, color: colores.texto, lineHeight: 26 },
});
